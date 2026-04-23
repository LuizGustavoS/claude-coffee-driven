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

5. Use `get_pull_request_diff` para obter o diff completo das mudanças. Se o resultado do diff contiver um redirecionamento (redirect) ou URL em vez do conteúdo, informe ao usuário que ele precisa acessar a pasta do projeto localmente para que o diff funcione corretamente, e então apresente um resumo parcial com base nos commits e metadados disponíveis (título, descrição, commits).

6. Use `get_pull_request_comments` para ver o feedback já existente no PR.

7. **Analise as mudanças** considerando:
   - Correção lógica e possíveis bugs
   - Qualidade do código (legibilidade, duplicação, complexidade)
   - Cobertura de casos de borda e tratamento de erros
   - Impacto em performance ou segurança
   - Consistência com o padrão do restante do código

   Para cada observação (problema ou sugestão), **registre o local exato** onde ela se aplica: `path` (caminho do arquivo no repo) e `line` (número da linha no arquivo após a mudança, conforme o diff). Se o comentário se referir a uma linha removida, registre `line_side: "from"`; caso contrário use `"to"` (padrão).

8. **Apresente o resultado** neste formato:

```
## Resumo
<2-3 frases descrevendo o que o PR faz>

## Aprovação
✅ Aprovado / ⚠️ Aprovado com ressalvas / ❌ Mudanças necessárias

## Problemas críticos
- `path/do/arquivo.py:42` — descrição do problema
- (ou "Nenhum")

## Sugestões
- `path/do/arquivo.py:87` — melhoria não bloqueante

## Perguntas
- `path/do/arquivo.py:12` — dúvida sobre a intenção do código
- (perguntas sem linha associada podem ficar sem referência)
```

9. **Pergunte ao usuário** se deseja:
   - Postar os comentários no PR — **cada item de "Problemas críticos", "Sugestões" e "Perguntas" com linha associada deve ser postado como um comentário inline separado** via `add_pull_request_comment` (informando `path`, `line` e, quando aplicável, `line_side`). Apenas o "Resumo" (e eventuais perguntas gerais sem linha) vai como comentário geral, omitindo `path` e `line`.
   - Marcar o PR como aprovado via `approve_pull_request`
   - Solicitar mudanças via `request_changes_pull_request` (quando há problemas críticos)

**Regras:**
- Ao postar, faça um `add_pull_request_comment` por item — não concatene vários problemas num único bloco de texto
- Só aprove com `approve_pull_request` se o usuário confirmar explicitamente
- Só solicite mudanças com `request_changes_pull_request` se o usuário confirmar explicitamente
- Seja direto e objetivo — foco em problemas reais, não estilo pessoal
- Se o diff for muito grande, priorize os arquivos de maior risco
