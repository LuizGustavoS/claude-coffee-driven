Configure as credenciais do plugin Bitbucket no settings do Claude Code.

1. **Explique** ao usuário que o plugin precisa de um App Password do Bitbucket para funcionar e que as credenciais serão salvas em `~/.claude/settings.json`.

2. **Peça o username** do Bitbucket (geralmente o email de login). Aguarde.

3. **Peça os workspaces** do Bitbucket (slugs separados por vírgula, ex: `minha-empresa, outro-workspace`). Explique que o slug é o identificador da URL do workspace (bitbucket.org/**slug**/). Se o usuário tiver apenas um workspace, aceite um único valor. Aguarde.

4. **Peça o API Token**. Se o usuário não souber como gerar, instrua:
   - Acesse [bitbucket.org](https://bitbucket.org) e faça login
   - Clique na foto de perfil (canto superior direito) → **Account settings**
   - No menu do topo, clique em **Segurança** → **Criar e gerenciar tokens de API**
   - Clique em **Criar token de API com escopos**
   - Preencha o **Nome** (ex: `claude-code`)
   - Em **Expires on**, defina uma data de expiração (máximo 1 ano a partir de hoje)
   - Em **Tipo**, selecione **Bitbucket**
   - Selecione **exatamente** os seguintes escopos:

   | Escopo | Permissão | Necessário para |
   |--------|-----------|-----------------|
   | Account | Read | Identificar o usuário autenticado |
   | Repositories | Read | Listar repositórios do workspace |
   | Pull requests | Read | Ler PR, diff, commits e comentários |
   | Pull requests | Write | Postar comentários e aprovar PRs |

   - Clique em **Criar** e copie o token gerado (ele só aparece uma vez)
   Aguarde o usuário fornecer o token.

5. **Leia** o arquivo `~/.claude/settings.json`. Se não existir, trate como `{}`.

6. **Adicione ou atualize** o bloco `env` com as três variáveis:
   ```json
   "env": {
     "BITBUCKET_USERNAME": "<username informado>",
     "BITBUCKET_API_TOKEN": "<token informado>",
     "BITBUCKET_WORKSPACES": ["<workspace1>", "<workspace2>"]
   }
   ```
   Converta os slugs informados em um array JSON (um elemento por slug, sem espaços extras). Preserve todos os outros campos existentes no arquivo.

7. **Salve** o arquivo `~/.claude/settings.json` com o conteúdo atualizado.

8. **Confirme** ao usuário que a configuração foi salva e oriente a reiniciar o Claude Code para as credenciais entrarem em vigor.

**Regras:**
- Nunca exiba o token na resposta após salvar
- Se o arquivo já tiver `BITBUCKET_USERNAME`, `BITBUCKET_API_TOKEN` ou `BITBUCKET_WORKSPACES`, pergunte antes de sobrescrever
