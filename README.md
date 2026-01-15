## POC MedGemma (medgemma-4b-it) — API + UI

POC para integrar o modelo **MedGemma** em uma API **FastAPI** e uma UI web (HTML) simples.

### Estrutura

```
medgemma-poc/
├── main.py
├── src/
│   ├── api/routes/health_assistant.py
│   ├── core/config.py
│   ├── core/logging.py
│   ├── models/schemas.py
│   └── services/medgemma_service.py
├── frontend/
│   ├── index.html
│   ├── chat.html
│   ├── consulta.html
│   ├── triagem.html
│   ├── explicacao.html
│   ├── status.html
│   ├── logs.html
│   ├── metricas.html
│   ├── monitoramento.html
│   ├── config.html
│   ├── admin.html
│   └── suporte.html
└── requirements.txt
```

### Requisitos

- Python 3.9+ (recomendado 3.10/3.11)
- (Opcional) GPU NVIDIA + CUDA para acelerar inferência
- Token do Hugging Face (se o modelo exigir): `HF_TOKEN`

### Setup rápido

Crie e ative um ambiente virtual, depois instale dependências:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie seu arquivo `.env` a partir do template:

- Copie `env.example` para `.env` e preencha `HF_TOKEN` se necessário.

### Rodando a API

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Abra a UI em:

- `http://127.0.0.1:8000/ui/index.html`
- `http://127.0.0.1:8000/ui/chat.html`

### Endpoints (v1)

- `POST /api/v1/health/query`
- `POST /api/v1/health/triage`
- `POST /api/v1/health/explain`
- `GET /api/v1/health/status`
- `GET /api/v1/health/metrics`
- `GET /api/v1/health/logs`

### Exemplos cURL

Consulta geral:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/health/query ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Estou com dor de cabeça há 2 dias. O que devo observar?\",\"context\":null,\"language\":\"pt-BR\"}"
```

Triagem:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/health/triage ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Febre 39C, dor no corpo e falta de ar.\",\"context\":null,\"language\":\"pt-BR\"}"
```

Explicação:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/health/explain ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"O que é hipertensão?\",\"context\":null,\"language\":\"pt-BR\"}"
```

Status:

```bash
curl http://127.0.0.1:8000/api/v1/health/status
```

Logs:

```bash
curl "http://127.0.0.1:8000/api/v1/health/logs?limit=20"
```

Métricas:

```bash
curl "http://127.0.0.1:8000/api/v1/health/metrics"
```

### Rodando com Docker

Build + run:

```bash
docker compose up --build
```

Depois acesse: `http://127.0.0.1:8000/ui/index.html`

### Observações importantes

- **Disclaimer obrigatório**: todas as respostas incluem um aviso de que não substitui consulta médica.
- **Privacidade**: logs evitam armazenar conteúdo integral da mensagem (registram metadados e preview curto).
- **Primeira chamada pode demorar**: o modelo é carregado sob demanda (lazy). Use a página `/ui/admin.html` para warm-up.

### Troubleshooting rápido

- **Erro 503 “Modelo indisponível”**: geralmente falha ao carregar o modelo (token/VRAM/RAM). Verifique console/logs do servidor e teste:
  - `DEVICE=cpu` (mais lento, mas funciona sem GPU)
  - `DEVICE=cuda` (se houver GPU)
  - `USE_QUANTIZATION=true` (4-bit, normalmente só faz sentido em GPU)
- **UI fora do servidor**: se abrir HTML via Live Server/arquivo local, use a página `/ui/config.html` para setar `window.API_BASE_URL`.

