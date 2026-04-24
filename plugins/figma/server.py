import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("figma")

BASE_URL = "https://api.figma.com/v1"


def _headers() -> dict:
    return {"X-Figma-Token": os.environ["FIGMA_ACCESS_TOKEN"]}


def _api(method: str, path: str, **kwargs):
    r = httpx.request(method, f"{BASE_URL}{path}", headers=_headers(), **kwargs)
    r.raise_for_status()
    return r


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


if __name__ == "__main__":
    mcp.run()
