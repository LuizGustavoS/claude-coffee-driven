Faça um commit com as mudanças atuais seguindo este fluxo:

1. Execute `git status` para ver arquivos modificados e não rastreados.
2. Execute `git diff` para ver todas as mudanças staged e unstaged.
3. Execute `git log --oneline -5` para ver o estilo de commits recentes.
4. **Pergunte ao usuário o número do ticket** (ex: PROJ-123). Aguarde a resposta antes de continuar.
5. Analise as mudanças e escreva uma mensagem de commit seguindo **Conventional Commits em pt-br**:
   - Prefixos: `feat`, `fix`, `refactor`, `style`, `docs`, `test`, `chore`, `perf`
   - O escopo é o módulo/contexto da mudança (ex: auth, boleto, ted), não o ticket
   - Se o usuário informou um ticket: `tipo(escopo): descrição curta e direta em pt-br [TICKET]`
   - Se o usuário não informou ticket: `tipo(escopo): descrição curta e direta em pt-br`
   - Exemplo com ticket: `feat(ambar): adicionado coluna fg_ted_bloqueio_reenvio na tabela de ted [IMB-1998]`
   - Corpo opcional se necessário para explicar o "por quê"
6. Adicione os arquivos relevantes ao stage (prefira arquivos específicos a `git add -A`).
7. Faça o commit com a mensagem via HEREDOC, incluindo o rodapé:

```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

8. Execute `git status` para confirmar que o commit foi criado.

**Regras:**
- Nunca faça commit de arquivos sensíveis (.env, credenciais)
- Nunca use `--no-verify`
- Crie sempre um commit NOVO (nunca use `--amend` a menos que o usuário peça)
- Se um hook de pre-commit falhar, corrija o problema e crie um novo commit
