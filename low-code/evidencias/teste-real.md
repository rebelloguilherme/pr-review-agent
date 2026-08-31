# Evidência real — integração n8n

Workflow publicado em n8n Cloud: `pr-review-agent - notificacao Discord`
(Webhook POST -> HTTP Request para o webhook do Discord).

Teste via `agent/low_code.py::notify_low_code` (chamada real, não mockada):

```
trace_id: rebelloguilherme/pr-review-agent#99
evento: low_code.notified
url: https://gdata.app.n8n.cloud/webhook/pr-review-agent
timestamp: 2026-08-31T23:07:37Z
```

Execução no n8n: "Succeeded in 441ms" — os dois nós (Webhook, HTTP Request)
completaram com sucesso, mensagem publicada no canal do Discord.
