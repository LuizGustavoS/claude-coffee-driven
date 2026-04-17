# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este repositório

Marketplace local de plugins para o Claude Code. Contém plugins que estendem as capacidades do Claude via slash commands e servidores MCP.

Os plugins deste repositório são publicados no repositório externo `LuizGustavoS/claude-coffee-driven`, que é a fonte configurada no `settings.json`.

## Estrutura de um plugin

Cada plugin em `plugins/` segue esta estrutura:

```
plugins/<nome>/
├── .claude-plugin/
│   └── plugin.json       # Metadados: nome, versão, comandos registrados
└── commands/             # (se for slash commands) arquivos .md com os prompts
    └── *.md
```

Ou para plugins MCP:

```
plugins/<nome>/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json             # Configuração do servidor MCP
├── server.py             # Implementação do servidor
└── pyproject.toml        # Dependências Python (gerenciado com uv)
```

## Registro no marketplace

O arquivo `/.claude-plugin/marketplace.json` é o índice central. Ao criar um novo plugin, registrá-lo aqui com `name`, `description` e `path`.

O `settings.json` na raiz ativa os plugins e aponta o marketplace para o repositório GitHub.

## Plugin: cloudwatch

Servidor MCP em Python que expõe ferramentas de consulta ao AWS CloudWatch Logs.

**Rodar o servidor localmente:**
```bash
cd plugins/cloudwatch
uv run python server.py
```

**Ferramentas expostas:**
- `list_log_groups` — lista grupos de logs com filtro opcional por prefixo
- `search_logs` — executa queries no CloudWatch Logs Insights
- `get_recent_logs` — busca eventos recentes com filtro por padrão

Requer credenciais AWS configuradas no ambiente (`AWS_PROFILE` ou variáveis `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`).

## Plugin: gitflow

Plugin de slash commands (sem código executável). Define guias de workflow em Markdown para:
- `/commit` — fluxo de conventional commits com referência a ticket Bitbucket
- `/code-review` — processo de revisão de pull requests
