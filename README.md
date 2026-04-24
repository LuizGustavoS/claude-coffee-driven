# claude-coffee-driven

Marketplace de plugins para o [Claude Code](https://claude.ai/code). Este repositório é a fonte do marketplace `coffee-driven` e contém plugins que estendem o Claude via slash commands e servidores MCP.

## Como instalar

Adicione o marketplace:

```bash
claude plugin marketplace add LuizGustavoS/claude-coffee-driven
```

Instale os plugins desejados:

```bash
claude plugin install gitflow@coffee-driven
claude plugin install cloudwatch@coffee-driven
claude plugin install bitbucket@coffee-driven
claude plugin install figma@coffee-driven
```

## Como atualizar

O Claude Code mantém um cache local do marketplace e dos plugins. Para receber mudanças publicadas neste repositório, primeiro atualize o índice do marketplace e depois os plugins.

1. **Atualize o índice do marketplace** (necessário quando novos plugins foram adicionados ou os metadados mudaram):

   ```bash
   claude plugin marketplace update coffee-driven
   ```

2. **Atualize os plugins instalados:**

   ```bash
   claude plugin update gitflow@coffee-driven
   claude plugin update cloudwatch@coffee-driven
   claude plugin update bitbucket@coffee-driven
   claude plugin update figma@coffee-driven
   ```

   Ou para atualizar todos os plugins instalados de uma vez:

   ```bash
   claude plugin update --all
   ```

## Plugins disponíveis

### gitflow

Slash commands para o fluxo de desenvolvimento com Bitbucket. Não tem dependências — funciona em qualquer projeto com git.

| Comando | O que faz |
|---|---|
| `/gitflow:commit` | Analisa as mudanças, pergunta o número do ticket e gera um commit em Conventional Commits (pt-br) |

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

### bitbucket

Servidor MCP para revisar Pull Requests no Bitbucket Cloud. O Claude busca o diff, commits e comentários do PR e conduz a revisão via `/bitbucket:code-review`.

**Pré-requisitos:**
- [uv](https://docs.astral.sh/uv/) instalado na máquina

**Configuração:** chame `/bitbucket:setup` no Claude Code — o agente guia a criação do token e salva as credenciais automaticamente.

Ou exporte manualmente as variáveis no ambiente (ex: `~/.zshrc`):

```bash
export BITBUCKET_USERNAME=seu-usuario
export BITBUCKET_API_TOKEN=seu-api-token
```

**Como usar:** chame `/bitbucket:code-review` e informe a URL do PR. O Claude busca os dados, analisa o código e pergunta se deseja postar o resultado como comentário ou aprovar o PR.

| Ferramenta MCP | Descrição |
|---|---|
| `get_pull_request` | Metadados do PR (título, autor, branches, estado) |
| `get_pull_request_diff` | Diff completo das mudanças |
| `get_pull_request_commits` | Lista de commits incluídos no PR |
| `get_pull_request_comments` | Comentários existentes no PR |
| `add_pull_request_comment` | Posta um comentário no PR |
| `approve_pull_request` | Aprova o PR como o usuário autenticado |

### figma

Servidor MCP para inspecionar arquivos do Figma via REST API. O Claude lê a estrutura do arquivo, componentes e estilos, e exporta imagens de frames via `/figma:inspect`.

**Pré-requisitos:**
- [uv](https://docs.astral.sh/uv/) instalado na máquina

**Configuração:** chame `/figma:setup` no Claude Code — o agente guia a geração do Personal Access Token e salva a credencial automaticamente.

Ou exporte manualmente a variável no ambiente (ex: `~/.zshrc`):

```bash
export FIGMA_ACCESS_TOKEN=seu-personal-access-token
```

**Como usar:** chame `/figma:inspect` e informe a URL do arquivo Figma. O Claude lista páginas/frames e conduz a inspeção a partir daí.

| Ferramenta MCP | Descrição |
|---|---|
| `get_file` | Estrutura do arquivo (páginas e frames) até a profundidade informada |
| `get_file_nodes` | Detalhes de nodes específicos (tipo, posição, tamanho, filhos) |
| `list_components` | Componentes publicados no arquivo |
| `list_styles` | Estilos publicados (cores, tipografia, efeitos, grades) |
| `export_images` | Exporta frames/nodes como PNG, JPG, SVG ou PDF (retorna URLs S3 temporárias) |

## Testar um servidor MCP localmente com o Inspector

Para validar um servidor MCP deste repositório sem precisar publicar/atualizar via Claude Code, use o [MCP Inspector](https://github.com/modelcontextprotocol/inspector). Ele sobe o servidor como subprocesso e abre uma UI no navegador para invocar cada tool manualmente.

No diretório do plugin, com as variáveis de ambiente necessárias no comando:

```bash
cd plugins/figma
FIGMA_ACCESS_TOKEN=seu-token npx @modelcontextprotocol/inspector uv run --project . python server.py
```

Para outros plugins deste repo basta trocar o diretório e as variáveis (ex: `cd plugins/bitbucket` com `BITBUCKET_USERNAME` / `BITBUCKET_API_TOKEN` / `BITBUCKET_WORKSPACES`).

O Inspector imprime a URL da UI no terminal (com token de sessão embutido). Na interface: clique **Connect** → aba **Tools** → **List Tools** → selecione uma tool, preencha os parâmetros e clique **Run Tool**.

Requer [Node.js](https://nodejs.org/) 18+ para o `npx` (o Inspector é baixado na primeira execução).
