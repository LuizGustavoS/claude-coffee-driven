Faça uma revisão completa de um Pull Request seguindo este fluxo:

1. Use `list_pull_requests_to_review` (sem informar workspace) para listar todos os PRs onde o usuário é revisor.

2. **Apresente a lista** ao usuário no formato:
   ```
   #<id> — <título>
     Repo: <repo> | <branch origem> → <branch destino>
     <url>
   ```
   Peça que informe o número ou URL do PR que deseja revisar. Aguarde.

3. Com o PR escolhido, extraia `workspace`, `repo_slug` e `pr_id`. Use `get_pull_request` para buscar os metadados: título, descrição, autor, branches e estado.

4. Use `get_pull_request_commits` para listar os commits incluídos no PR.

5. Use `get_pull_request_diff` para obter o diff completo das mudanças.

6. Use `get_pull_request_comments` para ver o feedback já existente no PR.

7. **Analise as mudanças** considerando:
   - Correção lógica e possíveis bugs
   - Qualidade do código (legibilidade, duplicação, complexidade)
   - Cobertura de casos de borda e tratamento de erros
   - Impacto em performance ou segurança
   - Consistência com o padrão do restante do código

8. **Apresente o resultado** neste formato:

```
## Resumo
<2-3 frases descrevendo o que o PR faz>

## Aprovação
✅ Aprovado / ⚠️ Aprovado com ressalvas / ❌ Mudanças necessárias

## Problemas críticos
- (itens que bloqueiam aprovação, ou "Nenhum")

## Sugestões
- (melhorias não bloqueantes)

## Perguntas
- (dúvidas sobre a intenção do código)
```

9. **Pergunte ao usuário** se deseja:
   - Postar o resumo como comentário no PR via `add_pull_request_comment`
   - Marcar o PR como aprovado via `approve_pull_request`

**Regras:**
- Só aprove com `approve_pull_request` se o usuário confirmar explicitamente
- Seja direto e objetivo — foco em problemas reais, não estilo pessoal
- Se o diff for muito grande, priorize os arquivos de maior risco
