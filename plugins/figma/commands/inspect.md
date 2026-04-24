Inspecione um arquivo do Figma seguindo este fluxo:

1. Se o usuário não informou a URL ou a `file_key`, peça a URL do arquivo no Figma.
   Extraia a `file_key` da URL — ela aparece entre `/file/` ou `/design/` e o próximo `/`:
   - `https://www.figma.com/design/<file_key>/Nome-do-arquivo?node-id=...`
   - `https://www.figma.com/file/<file_key>/Nome-do-arquivo`

2. Chame `get_file` com a `file_key` (depth padrão = 2) para apresentar a estrutura do arquivo: páginas e frames principais. Mostre ao usuário no formato:
   ```
   Arquivo: <nome>
   Última modificação: <timestamp>

   Páginas e frames:
     [<id>] <nome> (<tipo>)
       [<id>] <nome> (<tipo>)
   ```

3. **Pergunte ao usuário** o que deseja fazer em seguida:
   - **Inspecionar um frame ou node específico** → peça o(s) id(s) e use `get_file_nodes` com `node_ids` em CSV.
   - **Listar componentes** do arquivo → use `list_components`.
   - **Listar estilos** (cores, tipografia, efeitos) → use `list_styles`.
   - **Exportar imagens** de um ou mais frames/nodes → peça os ids, formato (`png`, `jpg`, `svg`, `pdf`) e escala se for raster. Use `export_images`.

4. Para **exportação**, apresente as URLs retornadas uma por linha (`node_id → url`) e **avise** que são URLs S3 temporárias — expiram em cerca de 30 dias e devem ser baixadas/copiadas antes disso.

5. Para **estilos** ou **componentes**, se o usuário pedir, formate como **design tokens** (ex: bloco JSON/CSS/SCSS) com nome em kebab-case e o identificador/key para referência.

**Regras:**
- Se `get_file` retornar uma árvore muito rasa ou muito profunda para o caso, sugira reexecutar com `depth` ajustado.
- IDs de node no Figma aparecem na URL como `node-id=1-2` mas a API espera `1:2` — converta `-` em `:` antes de passar para as tools.
- Nunca exponha o `FIGMA_ACCESS_TOKEN` em respostas.
