Configure as credenciais do plugin Figma no settings do Claude Code.

1. **Explique** ao usuário que o plugin precisa de um Personal Access Token (PAT) do Figma e do ID do time padrão para funcionar, e que ambos serão salvos em `~/.claude/settings.json`.

2. **Peça o token**. Se o usuário não souber como gerar, instrua:
   - Acesse [figma.com](https://www.figma.com) e faça login
   - Clique na foto de perfil (canto superior direito) → **Settings**
   - Aba **Security** → seção **Personal access tokens** → **Generate new token**
   - Dê um nome (ex: `claude-code`) e defina uma data de expiração
   - Em **Scopes**, marque no mínimo:

   | Escopo | Permissão | Necessário para |
   |--------|-----------|-----------------|
   | File content | Read-only | Ler estrutura de arquivos, frames e nodes |
   | File metadata | Read-only | Ler nome, versão e data de modificação |
   | Library assets | Read-only | Listar componentes e estilos publicados |

   - Clique em **Generate token** e copie o token (ele só aparece uma vez).
   Aguarde o usuário fornecer o token.

3. **Peça o `team_id`** do time padrão. A API REST do Figma não expõe um endpoint para listar os times do usuário — então ele precisa pegar manualmente:
   - Acesse [figma.com](https://www.figma.com) logado
   - Clique no nome do time na sidebar esquerda
   - A URL vai ser algo tipo `https://www.figma.com/files/team/1234567890123456789/Nome-do-Time`
   - O `team_id` é o número entre `/team/` e o próximo `/`

   Aguarde o usuário fornecer o id.

4. **Leia** o arquivo `~/.claude/settings.json`. Se não existir, trate como `{}`.

5. **Adicione ou atualize** o bloco `env` com as variáveis:
   ```json
   "env": {
     "FIGMA_ACCESS_TOKEN": "<token informado>",
     "FIGMA_TEAM_ID": "<team_id informado>"
   }
   ```
   Preserve todos os outros campos existentes no arquivo.

6. **Salve** o arquivo `~/.claude/settings.json` com o conteúdo atualizado.

7. **Confirme** ao usuário que a configuração foi salva e oriente a reiniciar o Claude Code para as credenciais entrarem em vigor.

**Regras:**
- Nunca exiba o token na resposta após salvar
- Se o arquivo já tiver `FIGMA_ACCESS_TOKEN` ou `FIGMA_TEAM_ID`, pergunte antes de sobrescrever
