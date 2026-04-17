Você tem acesso ao servidor MCP `cloudwatch` para investigar logs no AWS CloudWatch Logs.

**Ferramentas disponíveis:**
- `list_log_groups` — lista log groups (com filtro opcional por prefixo)
- `search_logs` — executa query no CloudWatch Logs Insights (mais poderoso, permite agregações)
- `get_recent_logs` — busca eventos recentes com filtro por padrão de texto

**Fluxo padrão:**

1. Se o usuário não informou o `aws_profile`, pergunte qual profile AWS usar (ex: `default`, `producao`). Aguarde a resposta.
2. Se o usuário não informou a `aws_region`, pergunte ou assuma `sa-east-1` para projetos brasileiros.
3. Se o usuário não informou o log group, use `list_log_groups` para listar os disponíveis e pergunte qual usar. Se o usuário mencionou um serviço ou aplicação, filtre pelo nome com o parâmetro `prefix`.
4. Com profile, região e log group definidos, execute a busca adequada:
   - Para busca simples por texto/padrão: use `get_recent_logs` com `filter_pattern`
   - Para análise, contagem ou queries complexas: use `search_logs` com query Insights

**Exemplos de queries Insights úteis:**
```
# Últimos erros
fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20

# Erros por tipo
stats count(*) as total by errorCode | sort total desc

# Latência média
stats avg(duration) as avg_ms by bin(5m)

# Logs de uma requisição específica
fields @timestamp, @message | filter @message like /request-id-aqui/
```

**Regras:**
- Sempre apresente os resultados de forma legível, agrupando erros semelhantes quando houver muitos
- Se a query retornar muitos resultados, sugira filtros mais específicos
- Se o status retornar `Timeout` ou `Failed`, tente uma janela de tempo menor (`hours_ago`)
- O CloudWatch sempre armazena timestamps em UTC. Converta **sempre** para UTC-3 (horário de Brasília) ao exibir qualquer horário para o usuário
