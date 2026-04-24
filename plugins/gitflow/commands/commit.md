Crie um commit com as mudanças atuais usando o agent `commit`.

1. **Delegue ao agent `commit`** chamando a tool `Agent` com:
   - `subagent_type`: `commit`
   - `description`: curta (3-5 palavras), ex: `Cria commit convencional`
   - `prompt`: instrua o agent a commitar as mudanças atuais. Se o usuário já informou o número do ticket na conversa, repasse-o no prompt para evitar a pergunta.

2. **Aguarde o retorno do agent** e repasse ao usuário exatamente o que ele retornar (hash e mensagem do commit criado, ou erro).

**Regras:**
- Não reimplemente o fluxo de commit aqui — o agent já cuida de `git status`, `git diff`, análise, mensagem e commit.
- Não execute comandos `git` diretamente neste comando.
- Se o agent falhar, mostre o erro cru ao usuário.
