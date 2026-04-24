import json
import logging
import os
import time
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("figma")

BASE_URL = "https://api.figma.com/v1"
MAX_RETRIES = 5
MAX_RETRY_WAIT = 60.0
HTTP_TIMEOUT = 60.0
BATCH_SIZE = 50

logger = logging.getLogger("figma-mcp")


def _setup_logging(work_dir: Path) -> Path:
    log_path = work_dir / "debug.log"
    for h in list(logger.handlers):
        logger.removeHandler(h)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return log_path


def _headers() -> dict:
    return {"X-Figma-Token": os.environ["FIGMA_ACCESS_TOKEN"]}


def _api(method: str, path: str, **kwargs):
    for attempt in range(MAX_RETRIES):
        logger.info(f"{method} {path} attempt={attempt + 1}")
        r = httpx.request(
            method,
            f"{BASE_URL}{path}",
            headers=_headers(),
            timeout=HTTP_TIMEOUT,
            **kwargs,
        )
        if r.status_code == 429 and attempt < MAX_RETRIES - 1:
            retry_after = r.headers.get("Retry-After")
            try:
                raw = float(retry_after) if retry_after else 2 ** attempt
            except ValueError:
                raw = 2 ** attempt
            wait = min(raw, MAX_RETRY_WAIT)
            if raw > MAX_RETRY_WAIT:
                logger.warning(
                    f"429 rate limited, Retry-After={raw}s capado em {wait}s"
                )
            else:
                logger.warning(f"429 rate limited, sleeping {wait}s")
            time.sleep(wait)
            continue
        if r.status_code == 429:
            logger.error(f"429 rate limited após {MAX_RETRIES} tentativas em {path}")
            raise RuntimeError(
                f"Figma rate limit (429) em {path} após {MAX_RETRIES} tentativas. "
                f"Aguarde e re-invoque a fase para retomar de onde parou."
            )
        logger.info(f"  -> status={r.status_code}")
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r


def _rgba_to_hex(c: dict | None) -> str | None:
    if c is None:
        return None
    r = round(c.get("r", 0) * 255)
    g = round(c.get("g", 0) * 255)
    b = round(c.get("b", 0) * 255)
    a = c.get("a", 1.0)
    if abs(a - 1.0) < 0.004:
        return f"#{r:02X}{g:02X}{b:02X}"
    alpha = round(a * 255)
    return f"#{r:02X}{g:02X}{b:02X}{alpha:02X}"


def _to_kebab(name: str) -> str:
    return name.replace(" ", "-").lower()


def _chunk(lst: list, size: int = BATCH_SIZE):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def _walk_frames(node: dict, depth: int, current: int = 0) -> list[str]:
    lines = []
    indent = "  " * current
    node_id = node.get("id", "?")
    name = node.get("name", "?")
    node_type = node.get("type", "?")
    lines.append(f"{indent}[{node_id}] {name} ({node_type})")
    if current < depth:
        for child in node.get("children", []) or []:
            lines.extend(_walk_frames(child, depth, current + 1))
    return lines


def _load_state(work_dir: Path) -> dict:
    state_path = work_dir / "state.json"
    if not state_path.exists():
        raise FileNotFoundError(
            f"state.json não encontrado em {work_dir}. Rode extract_ds_init primeiro."
        )
    return json.loads(state_path.read_text(encoding="utf-8"))


def _save_state(work_dir: Path, state: dict) -> None:
    (work_dir / "state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


@mcp.tool()
def get_file(file_key: str, depth: int = 2) -> str:
    """
    Retorna a estrutura de um arquivo do Figma: páginas e frames até a profundidade especificada.

    Args:
        file_key: Chave do arquivo Figma, extraída da URL (ex: https://www.figma.com/design/<file_key>/...)
        depth: Profundidade da árvore a retornar. 1 = só páginas, 2 = páginas + frames principais, 3+ = mais níveis. Padrão: 2.
    """
    data = _api("GET", f"/files/{file_key}", params={"depth": depth}).json()
    name = data.get("name", "?")
    last_modified = data.get("lastModified", "?")
    version = data.get("version", "?")
    document = data.get("document", {})

    lines = [
        f"Arquivo: {name}",
        f"Última modificação: {last_modified}",
        f"Versão: {version}",
        "",
        "Estrutura:",
    ]
    for page in document.get("children", []) or []:
        lines.extend(_walk_frames(page, depth))
    return "\n".join(lines)


@mcp.tool()
def get_file_nodes(file_key: str, node_ids: str) -> str:
    """
    Retorna os detalhes de nodes específicos de um arquivo Figma (tipo, posição, tamanho, filhos).

    Args:
        file_key: Chave do arquivo Figma
        node_ids: IDs dos nodes separados por vírgula (ex: "1:2,3:4"). Os IDs aparecem na URL do Figma quando um node é selecionado (parâmetro node-id).
    """
    data = _api("GET", f"/files/{file_key}/nodes", params={"ids": node_ids}).json()
    nodes = data.get("nodes", {})
    if not nodes:
        return "Nenhum node encontrado."

    lines = []
    for nid, wrapper in nodes.items():
        if wrapper is None:
            lines.append(f"[{nid}] (não encontrado)")
            continue
        doc = wrapper.get("document", {})
        name = doc.get("name", "?")
        ntype = doc.get("type", "?")
        bbox = doc.get("absoluteBoundingBox") or {}
        size = f"{bbox.get('width', '?')}x{bbox.get('height', '?')} @ ({bbox.get('x', '?')},{bbox.get('y', '?')})" if bbox else "(sem bounding box)"
        children = doc.get("children", []) or []
        lines.append(
            f"[{nid}] {name} ({ntype})\n"
            f"  Tamanho/posição: {size}\n"
            f"  Filhos: {len(children)}"
        )
    return "\n\n".join(lines)


@mcp.tool()
def list_components(file_key: str) -> str:
    """
    Lista os componentes publicados em um arquivo Figma (útil para design systems).

    Args:
        file_key: Chave do arquivo Figma
    """
    data = _api("GET", f"/files/{file_key}/components").json()
    components = data.get("meta", {}).get("components", [])
    if not components:
        return "Nenhum componente encontrado."

    lines = []
    for c in components:
        key = c.get("key", "?")
        name = c.get("name", "?")
        description = c.get("description", "") or "(sem descrição)"
        node_id = c.get("node_id", "?")
        lines.append(f"[{node_id}] {name} (key: {key})\n  {description}")
    return "\n\n".join(lines)


@mcp.tool()
def list_styles(file_key: str) -> str:
    """
    Lista os estilos publicados em um arquivo Figma (cores, tipografia, efeitos, grades).

    Args:
        file_key: Chave do arquivo Figma
    """
    data = _api("GET", f"/files/{file_key}/styles").json()
    styles = data.get("meta", {}).get("styles", [])
    if not styles:
        return "Nenhum estilo encontrado."

    lines = []
    for s in styles:
        key = s.get("key", "?")
        name = s.get("name", "?")
        stype = s.get("style_type", "?")
        description = s.get("description", "") or "(sem descrição)"
        node_id = s.get("node_id", "?")
        lines.append(f"[{node_id}] {name} ({stype}, key: {key})\n  {description}")
    return "\n\n".join(lines)


@mcp.tool()
def export_images(file_key: str, node_ids: str, format: str = "png", scale: float = 1.0) -> str:
    """
    Exporta imagens de nodes específicos de um arquivo Figma. Retorna URLs S3 temporárias
    (válidas por cerca de 30 dias) — faça o download ou copie antes de expirar.

    Args:
        file_key: Chave do arquivo Figma
        node_ids: IDs dos nodes separados por vírgula (ex: "1:2,3:4")
        format: Formato da imagem — png, jpg, svg ou pdf (padrão: png)
        scale: Escala da exportação, entre 0.01 e 4 (padrão: 1.0). Só se aplica a png/jpg.
    """
    params = {"ids": node_ids, "format": format, "scale": scale}
    data = _api("GET", f"/images/{file_key}", params=params).json()
    images = data.get("images", {})
    if not images:
        return "Nenhuma imagem gerada."

    lines = []
    for nid, url in images.items():
        if url is None:
            lines.append(f"{nid} → (falha ao exportar)")
        else:
            lines.append(f"{nid} → {url}")
    err = data.get("err")
    if err:
        lines.append(f"\nAviso da API: {err}")
    return "\n".join(lines)


@mcp.tool()
def get_me() -> str:
    """
    Retorna os dados do usuário autenticado pelo FIGMA_ACCESS_TOKEN (útil para validar o token).
    """
    data = _api("GET", "/me").json()
    return (
        f"ID: {data.get('id', '?')}\n"
        f"Handle: {data.get('handle', '?')}\n"
        f"Email: {data.get('email', '?')}\n"
        f"Avatar: {data.get('img_url', '?')}"
    )


@mcp.tool()
def list_projects(team_id: str = "") -> str:
    """
    Lista os projetos de um time no Figma.

    Args:
        team_id: ID do time no Figma. É o número que aparece na URL do time:
                 https://www.figma.com/files/team/<team_id>/...
                 Se vazio, usa a variável de ambiente FIGMA_TEAM_ID.
    """
    team_id = team_id or os.environ.get("FIGMA_TEAM_ID", "")
    if not team_id:
        return "team_id não informado e FIGMA_TEAM_ID não está configurado no ambiente."
    data = _api("GET", f"/teams/{team_id}/projects").json()
    team_name = data.get("name", "?")
    projects = data.get("projects", [])
    if not projects:
        return f"Time '{team_name}' não possui projetos (ou token sem acesso)."

    lines = [f"Time: {team_name}", ""]
    for p in projects:
        lines.append(f"[{p.get('id', '?')}] {p.get('name', '?')}")
    return "\n".join(lines)


@mcp.tool()
def list_project_files(project_id: str) -> str:
    """
    Lista os arquivos de um projeto no Figma.

    Args:
        project_id: ID do projeto no Figma (obtido via `list_projects`).
    """
    data = _api("GET", f"/projects/{project_id}/files").json()
    project_name = data.get("name", "?")
    files = data.get("files", [])
    if not files:
        return f"Projeto '{project_name}' não possui arquivos."

    lines = [f"Projeto: {project_name}", ""]
    for f in files:
        key = f.get("key", "?")
        name = f.get("name", "?")
        last_modified = f.get("last_modified", "?")
        lines.append(f"[{key}] {name}\n  Última modificação: {last_modified}")
    return "\n\n".join(lines)


@mcp.tool()
def extract_ds_init(file_key: str, work_dir: str) -> str:
    """
    Fase 1/4 da extração do design system. Baixa metadados do arquivo, lista de styles e
    lista de components, e persiste em {work_dir}/state.json.

    Cada fase é curta o suficiente para caber no timeout padrão do Claude Code. Logs detalhados
    ficam em {work_dir}/debug.log. Próxima fase: extract_ds_styles.

    Args:
        file_key: Chave do arquivo Figma (da URL ou via list_project_files).
        work_dir: Diretório onde o estado intermediário e o markdown final serão salvos.
                  Criado se não existir.
    """
    wd = Path(work_dir).expanduser().resolve()
    wd.mkdir(parents=True, exist_ok=True)
    log_path = _setup_logging(wd)
    logger.info(f"=== PHASE INIT START file_key={file_key} ===")

    file_meta = _api("GET", f"/files/{file_key}", params={"depth": 1}).json()
    file_name = file_meta.get("name", "?")
    last_modified = file_meta.get("lastModified", "?")
    pages = [p.get("name", "?") for p in file_meta.get("document", {}).get("children", []) or []]

    styles = _api("GET", f"/files/{file_key}/styles").json().get("meta", {}).get("styles", [])
    components = _api("GET", f"/files/{file_key}/components").json().get("meta", {}).get("components", [])

    state = {
        "file_key": file_key,
        "file_name": file_name,
        "last_modified": last_modified,
        "pages": pages,
        "styles": styles,
        "components": components,
        "phases": {
            "init": "done",
            "styles": "pending",
            "components": "pending",
            "finalize": "pending",
        },
    }
    _save_state(wd, state)

    fill = sum(1 for s in styles if s["style_type"] == "FILL")
    text = sum(1 for s in styles if s["style_type"] == "TEXT")
    effect = sum(1 for s in styles if s["style_type"] == "EFFECT")
    grid = sum(1 for s in styles if s["style_type"] == "GRID")

    logger.info(
        f"=== PHASE INIT DONE styles={len(styles)} "
        f"(FILL={fill} TEXT={text} EFFECT={effect} GRID={grid}) "
        f"components={len(components)} ==="
    )

    return (
        f"Phase INIT concluída.\n"
        f"work_dir: {wd}\n"
        f"log: {log_path}\n"
        f"Arquivo: {file_name} ({file_key})\n"
        f"Styles: {len(styles)} (FILL={fill}, TEXT={text}, EFFECT={effect}, GRID={grid}) | "
        f"Components: {len(components)}\n"
        f"Próxima fase: extract_ds_styles(work_dir='{wd}')"
    )


@mcp.tool()
def extract_ds_styles(work_dir: str) -> str:
    """
    Fase 2/4. Resolve os nodes de cada style (FILL/TEXT/EFFECT/GRID) em lotes e persiste
    incrementalmente em {work_dir}/styles_nodes.json.

    Suporta resume: se a fase foi interrompida, re-invocar continua do último lote salvo.
    Próxima fase: extract_ds_components.

    Args:
        work_dir: Mesmo diretório passado para extract_ds_init.
    """
    wd = Path(work_dir).expanduser().resolve()
    _setup_logging(wd)
    state = _load_state(wd)
    file_key = state["file_key"]
    styles = state["styles"]

    nodes_path = wd / "styles_nodes.json"
    existing: dict = {}
    if nodes_path.exists():
        existing = json.loads(nodes_path.read_text(encoding="utf-8"))

    pending_ids = [s["node_id"] for s in styles if s["node_id"] not in existing]
    logger.info(
        f"=== PHASE STYLES START total={len(styles)} "
        f"resolved={len(existing)} pending={len(pending_ids)} ==="
    )

    batches = list(_chunk(pending_ids))
    for i, batch in enumerate(batches, 1):
        logger.info(f"styles batch {i}/{len(batches)} size={len(batch)}")
        resp = _api(
            "GET",
            f"/files/{file_key}/nodes",
            params={"ids": ",".join(batch), "depth": 1},
        ).json()
        existing.update(resp.get("nodes", {}))
        nodes_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    state["phases"]["styles"] = "done"
    _save_state(wd, state)
    logger.info(f"=== PHASE STYLES DONE resolved={len(existing)} ===")

    return (
        f"Phase STYLES concluída.\n"
        f"Nodes resolvidos: {len(existing)}/{len(styles)}\n"
        f"styles_nodes.json: {nodes_path}\n"
        f"Próxima fase: extract_ds_components(work_dir='{wd}')"
    )


@mcp.tool()
def extract_ds_components(work_dir: str) -> str:
    """
    Fase 3/4. Resolve os nodes de cada componente em lotes e persiste incrementalmente
    em {work_dir}/components_nodes.json.

    Suporta resume. Próxima fase: extract_ds_finalize.

    Args:
        work_dir: Mesmo diretório passado para extract_ds_init.
    """
    wd = Path(work_dir).expanduser().resolve()
    _setup_logging(wd)
    state = _load_state(wd)
    file_key = state["file_key"]
    components = state["components"]

    nodes_path = wd / "components_nodes.json"
    existing: dict = {}
    if nodes_path.exists():
        existing = json.loads(nodes_path.read_text(encoding="utf-8"))

    pending_ids = [c["node_id"] for c in components if c["node_id"] not in existing]
    logger.info(
        f"=== PHASE COMPONENTS START total={len(components)} "
        f"resolved={len(existing)} pending={len(pending_ids)} ==="
    )

    batches = list(_chunk(pending_ids))
    for i, batch in enumerate(batches, 1):
        logger.info(f"components batch {i}/{len(batches)} size={len(batch)}")
        resp = _api(
            "GET",
            f"/files/{file_key}/nodes",
            params={"ids": ",".join(batch), "depth": 2},
        ).json()
        existing.update(resp.get("nodes", {}))
        nodes_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    state["phases"]["components"] = "done"
    _save_state(wd, state)
    logger.info(f"=== PHASE COMPONENTS DONE resolved={len(existing)} ===")

    return (
        f"Phase COMPONENTS concluída.\n"
        f"Nodes resolvidos: {len(existing)}/{len(components)}\n"
        f"components_nodes.json: {nodes_path}\n"
        f"Próxima fase: extract_ds_finalize(work_dir='{wd}')"
    )


@mcp.tool()
def extract_ds_finalize(work_dir: str, output_path: str = "") -> str:
    """
    Fase 4/4. Monta o markdown final do design system a partir do state + styles_nodes +
    components_nodes salvos pelas fases anteriores. Nenhuma chamada à API do Figma.

    Args:
        work_dir: Diretório com state.json, styles_nodes.json e components_nodes.json.
        output_path: Caminho do .md final. Se vazio, usa {work_dir}/design-system.md.
    """
    wd = Path(work_dir).expanduser().resolve()
    _setup_logging(wd)
    state = _load_state(wd)

    style_nodes_path = wd / "styles_nodes.json"
    comp_nodes_path = wd / "components_nodes.json"
    if not style_nodes_path.exists() or not comp_nodes_path.exists():
        return (
            f"Erro: fases styles/components ainda não executadas em {wd}. "
            f"Rode extract_ds_styles e extract_ds_components antes."
        )

    style_nodes = json.loads(style_nodes_path.read_text(encoding="utf-8"))
    comp_nodes = json.loads(comp_nodes_path.read_text(encoding="utf-8"))

    logger.info("=== PHASE FINALIZE START ===")

    file_key = state["file_key"]
    file_name = state["file_name"]
    last_modified = state["last_modified"]
    pages = state["pages"]
    styles = state["styles"]
    components = state["components"]

    fill_styles = [s for s in styles if s["style_type"] == "FILL"]
    text_styles = [s for s in styles if s["style_type"] == "TEXT"]
    effect_styles = [s for s in styles if s["style_type"] == "EFFECT"]
    grid_styles = [s for s in styles if s["style_type"] == "GRID"]

    colors = []
    for s in fill_styles:
        token = _to_kebab(s["name"])
        desc = s.get("description", "") or "—"
        node = style_nodes.get(s["node_id"])
        hex_val = "(erro)"
        if node:
            fills = node.get("document", {}).get("fills", [])
            if fills:
                fill = fills[0]
                ftype = fill.get("type", "")
                if ftype == "SOLID":
                    hex_val = _rgba_to_hex(fill.get("color")) or "—"
                elif ftype.startswith("GRADIENT_"):
                    hex_val = "(gradient)"
                elif ftype == "IMAGE":
                    hex_val = "(image)"
                else:
                    hex_val = f"({ftype.lower()})"
            else:
                hex_val = "(sem fill)"
        colors.append({"token": token, "hex": hex_val, "desc": desc})

    typographies = []
    for s in text_styles:
        token = _to_kebab(s["name"])
        node = style_nodes.get(s["node_id"])
        typo = {"token": token, "font": "—", "size": "—", "weight": "—", "line_height": "—", "letter_spacing": "—"}
        if node:
            st = node.get("document", {}).get("style", {})
            if st:
                typo["font"] = st.get("fontFamily", "—")
                typo["size"] = st.get("fontSize", "—")
                typo["weight"] = st.get("fontWeight", "—")
                lh_unit = st.get("lineHeightUnit", "")
                if lh_unit == "PIXELS":
                    lh = st.get("lineHeightPx")
                    typo["line_height"] = f"{round(lh, 1)}px" if lh is not None else "—"
                elif lh_unit == "PERCENT":
                    lh = st.get("lineHeightPercentFontSize") or st.get("lineHeightPercent")
                    typo["line_height"] = f"{round(lh, 1)}%" if lh is not None else "—"
                elif lh_unit == "AUTO":
                    typo["line_height"] = "auto"
                else:
                    lh = st.get("lineHeightPx")
                    typo["line_height"] = f"{round(lh, 1)}px" if lh is not None else "—"
                typo["letter_spacing"] = st.get("letterSpacing", 0)
        typographies.append(typo)

    effects = []
    type_map = {
        "DROP_SHADOW": "drop-shadow",
        "INNER_SHADOW": "inner-shadow",
        "LAYER_BLUR": "layer-blur",
        "BACKGROUND_BLUR": "background-blur",
    }
    for s in effect_styles:
        token = _to_kebab(s["name"])
        node = style_nodes.get(s["node_id"])
        if not node:
            effects.append({"token": token, "type": "(erro)", "specs": "—"})
            continue
        effs = node.get("document", {}).get("effects", [])
        if not effs:
            effects.append({"token": token, "type": "—", "specs": "—"})
            continue
        for eff in effs:
            etype = eff.get("type", "UNKNOWN")
            parts = []
            if "offset" in eff:
                parts.append(f"x={eff['offset'].get('x', 0)} y={eff['offset'].get('y', 0)}")
            if "radius" in eff:
                parts.append(f"blur={eff['radius']}")
            if "spread" in eff:
                parts.append(f"spread={eff['spread']}")
            if "color" in eff:
                c = eff["color"]
                parts.append(
                    f"rgba({round(c['r']*255)},{round(c['g']*255)},{round(c['b']*255)},{round(c['a'], 3)})"
                )
            effects.append({
                "token": token,
                "type": type_map.get(etype, etype.lower()),
                "specs": " ".join(parts) if parts else "—",
            })

    comp_data = []
    for c in components:
        node = comp_nodes.get(c["node_id"])
        size = "—"
        variants: list[str] = []
        props_list: list[str] = []
        if node:
            doc = node.get("document", {})
            bbox = doc.get("absoluteBoundingBox") or {}
            if bbox:
                size = f"{round(bbox.get('width', 0))}x{round(bbox.get('height', 0))}"
            for prop_name, prop_def in (doc.get("componentPropertyDefinitions") or {}).items():
                ptype = prop_def.get("type", "")
                default = prop_def.get("defaultValue", "")
                values = prop_def.get("variantOptions", [])
                if values:
                    props_list.append(f"`{prop_name}`: {' | '.join(str(v) for v in values)} (default: {default})")
                else:
                    props_list.append(f"`{prop_name}`: {ptype} (default: {default})")
            if doc.get("type") == "COMPONENT_SET":
                variants = [child.get("name", "?") for child in doc.get("children", []) or []]
        comp_data.append({
            "name": c["name"],
            "desc": c.get("description", "") or "—",
            "size": size,
            "variants": variants,
            "props": props_list,
        })

    seen = set()
    unique_comps = []
    for c in comp_data:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique_comps.append(c)

    md = [
        f"# Design System — {file_name}",
        "",
        f"**Fonte:** Figma · file_key `{file_key}`",
        f"**Última modificação:** {last_modified}",
        f"**Páginas:** {', '.join(pages) if pages else '—'}",
        "",
        "## Cores",
        "",
        "| Token | Hex | Descrição |",
        "|---|---|---|",
    ]
    for c in colors:
        md.append(f"| `{c['token']}` | `{c['hex']}` | {c['desc']} |")
    md += [
        "",
        "## Tipografia",
        "",
        "| Token | Font | Size | Weight | Line height | Letter spacing |",
        "|---|---|---|---|---|---|",
    ]
    for t in typographies:
        md.append(
            f"| `{t['token']}` | {t['font']} | {t['size']} | {t['weight']} | {t['line_height']} | {t['letter_spacing']} |"
        )
    if effects:
        md += ["", "## Efeitos", "", "| Token | Tipo | Specs |", "|---|---|---|"]
        for e in effects:
            md.append(f"| `{e['token']}` | {e['type']} | {e['specs']} |")
    if grid_styles:
        md += ["", "## Grids", "", "| Token | Descrição |", "|---|---|"]
        for s in grid_styles:
            md.append(f"| `{_to_kebab(s['name'])}` | {s.get('description', '') or '—'} |")
    md += ["", "## Componentes", ""]
    for c in unique_comps:
        md += [
            f"### {c['name']}",
            "",
            f"- **Descrição:** {c['desc']}",
            f"- **Tamanho padrão:** {c['size']}",
        ]
        if c["variants"]:
            vs = ", ".join(c["variants"][:20])
            if len(c["variants"]) > 20:
                vs += f" ... (+{len(c['variants']) - 20} variantes)"
            md.append(f"- **Variantes:** {vs}")
        if c["props"]:
            md.append("- **Props:**")
            for p in c["props"]:
                md.append(f"  - {p}")
        md += ["", "---", ""]

    output = "\n".join(md)

    out = Path(output_path).expanduser().resolve() if output_path else (wd / "design-system.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output, encoding="utf-8")

    state["phases"]["finalize"] = "done"
    _save_state(wd, state)
    logger.info(f"=== PHASE FINALIZE DONE output={out} ===")

    return (
        f"Design system salvo em: {out}\n"
        f"Arquivo: {file_name} ({file_key})\n"
        f"Cores: {len(colors)} | Tipografias: {len(typographies)} | "
        f"Efeitos: {len(effects)} | Componentes: {len(unique_comps)} | Grids: {len(grid_styles)}"
    )


if __name__ == "__main__":
    mcp.run()
