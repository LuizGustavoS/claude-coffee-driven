import boto3
import json
import time
from datetime import datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cloudwatch")


def get_client(aws_profile: str, aws_region: str):
    session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
    return session.client("logs")


def ts_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


@mcp.tool()
def list_log_groups(
    aws_profile: str,
    aws_region: str,
    prefix: str = "",
) -> str:
    """
    Lista os log groups disponíveis no CloudWatch.

    Args:
        aws_profile: Nome do profile AWS (~/.aws/credentials)
        aws_region: Região AWS (ex: sa-east-1, us-east-1)
        prefix: Filtro opcional por prefixo do nome do log group
    """
    client = get_client(aws_profile, aws_region)
    kwargs = {"limit": 50}
    if prefix:
        kwargs["logGroupNamePrefix"] = prefix

    groups = []
    paginator = client.get_paginator("describe_log_groups")
    for page in paginator.paginate(**kwargs):
        for g in page["logGroups"]:
            groups.append(g["logGroupName"])

    return "\n".join(groups) if groups else "Nenhum log group encontrado."


@mcp.tool()
def search_logs(
    aws_profile: str,
    aws_region: str,
    log_group: str,
    query: str,
    hours_ago: int = 1,
) -> str:
    """
    Executa uma query CloudWatch Logs Insights em um log group.

    Exemplos de query:
      - "fields @timestamp, @message | filter @message like /ERROR/ | limit 20"
      - "fields @timestamp, level, message | filter level = 'ERROR' | sort @timestamp desc | limit 50"
      - "stats count(*) as total by level"

    Args:
        aws_profile: Nome do profile AWS (~/.aws/credentials)
        aws_region: Região AWS (ex: sa-east-1, us-east-1)
        log_group: Nome do log group (ex: /ecs/ambar)
        query: Query no formato CloudWatch Logs Insights
        hours_ago: Janela de tempo em horas para trás (padrão: 1)
    """
    client = get_client(aws_profile, aws_region)
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours_ago)

    response = client.start_query(
        logGroupName=log_group,
        startTime=ts_ms(start),
        endTime=ts_ms(end),
        queryString=query,
    )
    query_id = response["queryId"]

    while True:
        result = client.get_query_results(queryId=query_id)
        status = result["status"]
        if status in ("Complete", "Failed", "Cancelled", "Timeout"):
            break
        time.sleep(0.5)

    if status != "Complete":
        return f"Query terminou com status: {status}"

    rows = result.get("results", [])
    if not rows:
        return "Nenhum resultado encontrado."

    lines = []
    for row in rows:
        fields = {f["field"]: f["value"] for f in row}
        lines.append(json.dumps(fields, ensure_ascii=False))

    stats = result.get("statistics", {})
    summary = f"\n\n({len(rows)} resultados | scanned: {stats.get('recordsScanned', '?')} registros)"
    return "\n".join(lines) + summary


@mcp.tool()
def get_recent_logs(
    aws_profile: str,
    aws_region: str,
    log_group: str,
    minutes_ago: int = 30,
    filter_pattern: str = "",
    limit: int = 50,
) -> str:
    """
    Busca eventos recentes de um log group com filtro opcional.

    Args:
        aws_profile: Nome do profile AWS (~/.aws/credentials)
        aws_region: Região AWS (ex: sa-east-1, us-east-1)
        log_group: Nome do log group (ex: /ecs/ambar)
        minutes_ago: Janela de tempo em minutos para trás (padrão: 30)
        filter_pattern: Padrão de filtro CloudWatch (ex: ERROR, "boleto pago", { $.level = "ERROR" })
        limit: Número máximo de eventos (padrão: 50)
    """
    client = get_client(aws_profile, aws_region)
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes_ago)

    kwargs = {
        "logGroupName": log_group,
        "startTime": ts_ms(start),
        "endTime": ts_ms(end),
        "limit": limit,
    }
    if filter_pattern:
        kwargs["filterPattern"] = filter_pattern

    response = client.filter_log_events(**kwargs)
    events = response.get("events", [])

    if not events:
        return "Nenhum evento encontrado."

    lines = []
    for e in events:
        ts = datetime.fromtimestamp(e["timestamp"] / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        lines.append(f"[{ts}] {e['message'].rstrip()}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
