# claude-coffee-driven

Marketplace de plugins para o [Claude Code](https://claude.ai/code). Este repositório é a fonte do marketplace `coffee-driven` e contém plugins que estendem o Claude via slash commands e servidores MCP.

## Plugins disponíveis

### gitflow

Slash commands para o fluxo de desenvolvimento com Bitbucket. Não tem dependências — funciona em qualquer projeto com git.

| Comando | O que faz |
|---|---|
| `/gitflow:commit` | Analisa as mudanças, pergunta o número do ticket e gera um commit em Conventional Commits (pt-br) |
| `/gitflow:code-review` | Guia uma revisão de pull request no Bitbucket |

**Como usar:** abra o Claude Code em qualquer repositório git e chame o comando desejado. O Claude conduz o fluxo interativamente.

### cloudwatch

Servidor MCP para investigar logs no AWS CloudWatch Logs. O Claude acessa a AWS diretamente e conduz a investigação via `/cloudwatch:logs`.

**Pré-requisitos:**
- [uv](https://docs.astral.sh/uv/) instalado na máquina
- Credenciais AWS configuradas em `~/.aws/credentials` (via `aws configure` ou SSO)

**Como usar:** chame `/cloudwatch:logs` e o Claude vai perguntar o profile AWS, a região e o log group. A partir daí ele lista, filtra e analisa os logs usando as ferramentas abaixo.

| Ferramenta MCP | Descrição |
|---|---|
| `list_log_groups` | Lista log groups com filtro opcional por prefixo |
| `search_logs` | Executa queries no CloudWatch Logs Insights (agregações, filtros complexos) |
| `get_recent_logs` | Busca eventos recentes com filtro por padrão de texto |

## Como instalar

Adicione o marketplace:

```bash
claude plugin marketplace add LuizGustavoS/claude-coffee-driven
```

Instale os plugins desejados:

```bash
claude plugin install gitflow@coffee-driven
claude plugin install cloudwatch@coffee-driven
```

## Como atualizar

O Claude Code instala os plugins a partir de um commit específico do GitHub e os armazena em cache local. Para receber mudanças publicadas neste repositório, rode:

```bash
claude plugin update gitflow@coffee-driven
claude plugin update cloudwatch@coffee-driven
```

Ou para atualizar todos os plugins instalados de uma vez:

```bash
claude plugin update --all
```
