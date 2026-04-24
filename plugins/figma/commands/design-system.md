Extraia o design system de um arquivo Figma usando o agent `design-system`.

1. **Receba a entrada** do usuário. Aceite qualquer um destes formatos:
   - URL completa do arquivo (`https://www.figma.com/design/<file_key>/...` ou `https://www.figma.com/file/<file_key>/...`)
   - `file_key` direto
   - `project_id` (para escolher o arquivo de design system dentro do projeto)

   Se o usuário não informou nada, peça e aguarde.

2. **Delegue ao agent `design-system`** chamando a tool `Agent` com:
   - `subagent_type`: `design-system`
   - `description`: curta (3-5 palavras), ex: `Extrai design system Figma`
   - `prompt`: contendo a entrada recebida (URL, `file_key` ou `project_id`) e, se o usuário informou, o caminho de saída desejado.

3. **Aguarde o retorno do agent** e repasse ao usuário exatamente o que ele retornar — o caminho do arquivo gerado e o resumo com as contagens (cores, tipografias, efeitos, componentes, grids).

**Regras:**
- Não reimplemente o fluxo de extração aqui — o agent já faz isso.
- Não chame as MCP tools do Figma diretamente neste comando.
- Se o agent falhar, mostre o erro cru ao usuário.
