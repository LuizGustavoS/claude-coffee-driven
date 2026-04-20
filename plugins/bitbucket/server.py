import json
import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("bitbucket")

BASE_URL = "https://api.bitbucket.org/2.0"


def _auth() -> tuple[str, str]:
    return os.environ["BITBUCKET_USERNAME"], os.environ["BITBUCKET_API_TOKEN"]


def _workspaces() -> list[str]:
    raw = os.environ["BITBUCKET_WORKSPACES"]
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        return [w.strip() for w in raw.split(",") if w.strip()]


def _current_account_id() -> str:
    return _api("GET", "/user").json()["account_id"]


def _api(method: str, path: str, **kwargs):
    r = httpx.request(method, f"{BASE_URL}{path}", auth=_auth(), **kwargs)
    r.raise_for_status()
    return r


@mcp.tool()
def get_pull_request(workspace: str, repo_slug: str, pr_id: int) -> str:
    """
    Retorna os metadados de um Pull Request no Bitbucket Cloud.

    Args:
        workspace: Slug do workspace no Bitbucket (ex: minha-empresa)
        repo_slug: Slug do repositório (ex: meu-repo)
        pr_id: ID numérico do Pull Request
    """
    data = _api("GET", f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}").json()
    reviewers = data.get("reviewers", [])
    reviewers_str = ", ".join(r["display_name"] for r in reviewers) if reviewers else "(nenhum)"
    return (
        f"Título: {data['title']}\n"
        f"Descrição: {data.get('description') or '(sem descrição)'}\n"
        f"Autor: {data['author']['display_name']}\n"
        f"Revisores: {reviewers_str}\n"
        f"Branch origem: {data['source']['branch']['name']}\n"
        f"Branch destino: {data['destination']['branch']['name']}\n"
        f"Estado: {data['state']}\n"
        f"Criado em: {data['created_on']}\n"
        f"URL: {data['links']['html']['href']}"
    )


@mcp.tool()
def get_pull_request_diff(workspace: str, repo_slug: str, pr_id: int) -> str:
    """
    Retorna o diff completo de um Pull Request no Bitbucket Cloud.

    Args:
        workspace: Slug do workspace no Bitbucket
        repo_slug: Slug do repositório
        pr_id: ID numérico do Pull Request
    """
    return _api("GET", f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/diff").text


@mcp.tool()
def get_pull_request_commits(workspace: str, repo_slug: str, pr_id: int) -> str:
    """
    Lista os commits incluídos em um Pull Request no Bitbucket Cloud.

    Args:
        workspace: Slug do workspace no Bitbucket
        repo_slug: Slug do repositório
        pr_id: ID numérico do Pull Request
    """
    data = _api("GET", f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/commits").json()
    lines = []
    for c in data.get("values", []):
        short = c["hash"][:8]
        msg = c["message"].split("\n")[0]
        author = c["author"].get("user", {}).get("display_name") or c["author"].get("raw", "?")
        lines.append(f"{short} — {msg} ({author})")
    return "\n".join(lines) if lines else "Nenhum commit encontrado."


@mcp.tool()
def get_pull_request_comments(workspace: str, repo_slug: str, pr_id: int) -> str:
    """
    Lista os comentários de um Pull Request no Bitbucket Cloud.

    Args:
        workspace: Slug do workspace no Bitbucket
        repo_slug: Slug do repositório
        pr_id: ID numérico do Pull Request
    """
    data = _api("GET", f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/comments").json()
    lines = []
    for c in data.get("values", []):
        author = c["author"]["display_name"]
        content = c["content"]["raw"]
        created = c["created_on"]
        inline = c.get("inline")
        if inline:
            loc = f"{inline.get('path', '?')}:{inline.get('to', '?')}"
            lines.append(f"[{created}] {author} em {loc}:\n  {content}")
        else:
            lines.append(f"[{created}] {author}:\n  {content}")
    return "\n\n".join(lines) if lines else "Nenhum comentário encontrado."


@mcp.tool()
def add_pull_request_comment(workspace: str, repo_slug: str, pr_id: int, content: str) -> str:
    """
    Adiciona um comentário geral em um Pull Request no Bitbucket Cloud.

    Args:
        workspace: Slug do workspace no Bitbucket
        repo_slug: Slug do repositório
        pr_id: ID numérico do Pull Request
        content: Texto do comentário (suporta Markdown)
    """
    data = _api(
        "POST",
        f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/comments",
        json={"content": {"raw": content}},
    ).json()
    return f"Comentário adicionado (id: {data['id']})"


@mcp.tool()
def list_my_pull_requests(workspace: str = "", state: str = "OPEN") -> str:
    """
    Lista os Pull Requests do usuário autenticado em todos os repositórios de um workspace.
    Se workspace não for informado, busca em todos os workspaces configurados em BITBUCKET_WORKSPACES.

    Args:
        workspace: Slug do workspace no Bitbucket (ex: minha-empresa). Deixe vazio para usar os workspaces configurados.
        state: Estado dos PRs — OPEN, MERGED, DECLINED ou ALL (padrão: OPEN)
    """
    workspaces = [workspace] if workspace else _workspaces()
    account_id = _current_account_id()
    params: dict = {"pagelen": 50, "q": f'author.account_id="{account_id}"'}
    if state != "ALL":
        params["q"] += f' AND state="{state}"'

    lines = []
    for ws in workspaces:
        url = f"{BASE_URL}/repositories/{ws}"
        while url:
            repos_data = httpx.request("GET", url, auth=_auth(), params={"pagelen": 100}).json()
            for repo in repos_data.get("values", []):
                slug = repo["slug"]
                pr_url = f"{BASE_URL}/repositories/{ws}/{slug}/pullrequests"
                pr_resp = httpx.request("GET", pr_url, auth=_auth(), params=params)
                if pr_resp.status_code != 200:
                    continue
                for pr in pr_resp.json().get("values", []):
                    lines.append(
                        f"[#{pr['id']}] {pr['title']}\n"
                        f"  Workspace: {ws} | Repo: {slug} | Estado: {pr['state']}\n"
                        f"  {pr['source']['branch']['name']} → {pr['destination']['branch']['name']}\n"
                        f"  {pr['links']['html']['href']}"
                    )
            url = repos_data.get("next")

    label = workspace or ", ".join(workspaces)
    return "\n\n".join(lines) if lines else f"Nenhum PR encontrado em '{label}' com estado '{state}'."


@mcp.tool()
def list_pull_requests_to_review(workspace: str = "", state: str = "OPEN") -> str:
    """
    Lista os Pull Requests onde o usuário autenticado é revisor, em todos os repositórios de um workspace.
    Se workspace não for informado, busca em todos os workspaces configurados em BITBUCKET_WORKSPACES.

    Args:
        workspace: Slug do workspace no Bitbucket (ex: minha-empresa). Deixe vazio para usar os workspaces configurados.
        state: Estado dos PRs — OPEN, MERGED, DECLINED ou ALL (padrão: OPEN)
    """
    workspaces = [workspace] if workspace else _workspaces()
    account_id = _current_account_id()
    params: dict = {"pagelen": 50, "q": f'reviewers.account_id="{account_id}"'}
    if state != "ALL":
        params["q"] += f' AND state="{state}"'

    lines = []
    for ws in workspaces:
        url = f"{BASE_URL}/repositories/{ws}"
        while url:
            repos_data = httpx.request("GET", url, auth=_auth(), params={"pagelen": 100}).json()
            for repo in repos_data.get("values", []):
                slug = repo["slug"]
                pr_url = f"{BASE_URL}/repositories/{ws}/{slug}/pullrequests"
                pr_resp = httpx.request("GET", pr_url, auth=_auth(), params=params)
                if pr_resp.status_code != 200:
                    continue
                for pr in pr_resp.json().get("values", []):
                    lines.append(
                        f"[#{pr['id']}] {pr['title']}\n"
                        f"  Workspace: {ws} | Repo: {slug} | Estado: {pr['state']}\n"
                        f"  Autor: {pr['author']['display_name']}\n"
                        f"  {pr['source']['branch']['name']} → {pr['destination']['branch']['name']}\n"
                        f"  {pr['links']['html']['href']}"
                    )
            url = repos_data.get("next")

    label = workspace or ", ".join(workspaces)
    return "\n\n".join(lines) if lines else f"Nenhum PR para revisar em '{label}' com estado '{state}'."


@mcp.tool()
def approve_pull_request(workspace: str, repo_slug: str, pr_id: int) -> str:
    """
    Aprova um Pull Request no Bitbucket Cloud como o usuário autenticado.

    Args:
        workspace: Slug do workspace no Bitbucket
        repo_slug: Slug do repositório
        pr_id: ID numérico do Pull Request
    """
    data = _api("POST", f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/approve").json()
    return f"PR aprovado por {data['user']['display_name']}"


@mcp.tool()
def request_changes_pull_request(workspace: str, repo_slug: str, pr_id: int) -> str:
    """
    Solicita mudanças em um Pull Request no Bitbucket Cloud como o usuário autenticado.

    Args:
        workspace: Slug do workspace no Bitbucket
        repo_slug: Slug do repositório
        pr_id: ID numérico do Pull Request
    """
    data = _api("POST", f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/request-changes").json()
    return f"Mudanças solicitadas por {data['user']['display_name']}"


if __name__ == "__main__":
    mcp.run()
