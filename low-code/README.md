# Automação low-code — n8n

Fluxo: **Webhook (trigger)** → **Discord (saída observável)**.

O agente (`agent/low_code.py::notify_low_code`) chama esse webhook ao
final de cada execução, com um resumo em JSON (PR, contagem de arquivos,
se houve prompt injection, se o comentário foi publicado). A lógica de
revisão continua inteira na aplicação — o n8n só recebe o resultado
pronto e o encaminha para o Discord.

## Passo a passo para reproduzir

1. Crie uma conta gratuita em [n8n.cloud](https://n8n.cloud) (ou rode via
   Docker: `docker run -it --rm -p 5678:5678 n8nio/n8n`).
2. Crie um novo workflow.
3. Adicione um nó **Webhook**:
   - Method: `POST`
   - Path: algo como `pr-review-agent`
   - Copie a "Production URL" gerada.
4. Crie um Webhook de canal no Discord (Configurações do canal →
   Integrações → Webhooks → Novo Webhook → copiar URL).
5. Adicione um nó **Discord** (ou **HTTP Request** apontando pra URL do
   webhook do Discord) conectado à saída do nó Webhook, formatando a
   mensagem a partir do JSON recebido, por exemplo:
   ```
   PR #{{$json["pr_number"]}} ({{$json["owner"]}}/{{$json["repo"]}}) revisado.
   Arquivos analisados: {{$json["files_analyzed"]}}
   Prompt injection detectado: {{$json["injection_detected"]}}
   Comentário publicado: {{$json["comment_posted"]}}
   ```
6. Ative o workflow.
7. Cole a Production URL do Webhook em `N8N_WEBHOOK_URL` no `.env` do
   projeto.
8. Rode o agente normalmente (`python main.py <owner/repo> <PR>`) — a
   notificação chega no Discord ao final da execução.

## Exportação do workflow

`workflow.json` neste diretório é a exportação do workflow configurado
(Menu do workflow → Download).
