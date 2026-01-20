# Documentação dos Parâmetros do Arquivo .env

Este documento explica todos os parâmetros de configuração disponíveis no arquivo `.env` do projeto MedGemma POC.

---

## 📋 Índice

- [Parâmetros de Execução do Modelo](#parâmetros-de-execução-do-modelo)
- [Parâmetros de Geração](#parâmetros-de-geração)
- [Parâmetros de API](#parâmetros-de-api)
- [Parâmetros de Logging](#parâmetros-de-logging)
- [Exemplo Completo](#exemplo-completo)
- [Recomendações](#recomendações)

---

## 🖥️ Parâmetros de Execução do Modelo

### `DEVICE=auto`

**O que é:** Define o dispositivo onde o modelo será executado.

**Valores possíveis:**
- `auto` - Detecta automaticamente (usa GPU se disponível, senão CPU)
- `cpu` - Força uso da CPU (mais lento, mas funciona em qualquer máquina)
- `cuda` - Força uso da GPU NVIDIA (mais rápido, requer GPU compatível)

**Recomendação:** Deixe `auto` para usar GPU automaticamente quando disponível.

**Exemplo:**
```env
DEVICE=auto
```

---

### `USE_QUANTIZATION=false`

**O que é:** Ativa quantização 4-bit para reduzir o uso de memória.

**Valores possíveis:**
- `true` ou `1` - Ativa quantização (reduz memória, pode perder um pouco de qualidade)
- `false` ou `0` - Desativa quantização (padrão, melhor qualidade)

**Quando usar:** Útil quando você tem GPU com pouca VRAM ou quer rodar modelos grandes.

**Observação:** Geralmente só funciona em GPU (não em CPU).

**Exemplo:**
```env
USE_QUANTIZATION=false
```

---

## 🎯 Parâmetros de Geração

### `MAX_NEW_TOKENS=512`

**O que é:** Número máximo de tokens que o modelo pode gerar em uma resposta.

**Valores típicos:**
- `128-256` - Respostas curtas (pode cortar mensagens)
- `512` - Respostas médias (recomendado)
- `768-1024` - Respostas longas (pode demorar mais)

**Importante:** Este é o valor base. Em CPU, o sistema usa o menor entre este valor e `CPU_MAX_NEW_TOKENS`.

**Exemplo:**
```env
MAX_NEW_TOKENS=512
```

---

### `CPU_MAX_NEW_TOKENS=512`

**O que é:** Limite máximo de tokens quando o modelo roda em CPU (override para CPU).

**Por que existe:** Em CPU a geração é mais lenta, então este limite evita esperas muito longas.

**Valores típicos:**
- `128-256` - Respostas curtas (pode cortar)
- `512` - Respostas médias (recomendado)
- `768-1024` - Respostas longas (pode demorar muito)

**Importante:** Se suas respostas estão cortando no meio, aumente este valor.

**Exemplo:**
```env
CPU_MAX_NEW_TOKENS=512
```

---

### `CPU_MAX_TIME_S=30`

**O que é:** Tempo máximo (em segundos) que o modelo pode levar para gerar uma resposta quando roda em CPU.

**Por que existe:** Evita que o sistema trave se a geração demorar muito.

**Valores típicos:**
- `20-30` - Rápido, mas pode cortar respostas longas
- `60` - Equilibrado (recomendado)
- `90-120` - Permite respostas mais longas

**Importante:** Se a resposta está cortando antes de terminar, aumente este valor.

**Exemplo:**
```env
CPU_MAX_TIME_S=60
```

---

### `TEMPERATURE=0.3`

**O que é:** Controla a "aleatoriedade" ou "criatividade" das respostas do modelo.

**Escala:** `0.0` a `2.0` (geralmente usa-se `0.0` a `1.0`)

**Valores:**
- `0.0-0.3` - Mais determinístico, respostas mais consistentes (recomendado para saúde)
- `0.4-0.7` - Mais variado, respostas mais criativas
- `0.8-1.0+` - Muito criativo (pode ser menos preciso)

**Recomendação:** Para respostas médicas, use valores baixos (`0.2-0.3`) para maior consistência.

**Exemplo:**
```env
TEMPERATURE=0.3
```

---

### `TOP_P=0.9`

**O que é:** Controla a diversidade das respostas através de "nucleus sampling" (amostragem do núcleo).

**Escala:** `0.0` a `1.0`

**Valores:**
- `0.1-0.5` - Mais focado, respostas mais conservadoras
- `0.6-0.9` - Equilibrado (recomendado)
- `0.95-1.0` - Mais diverso (pode ser menos preciso)

**Como funciona:** Considera apenas os tokens mais prováveis até acumular `TOP_P` da probabilidade total.

**Recomendação:** Para saúde, use `0.8-0.9` para um bom equilíbrio.

**Exemplo:**
```env
TOP_P=0.9
```

---

## 🌐 Parâmetros de API

### `API_HOST=127.0.0.1`

**O que é:** Endereço IP onde a API será hospedada.

**Valores típicos:**
- `127.0.0.1` - Apenas localhost (padrão, mais seguro)
- `0.0.0.0` - Todas as interfaces (para acesso externo)

**Exemplo:**
```env
API_HOST=127.0.0.1
```

---

### `API_PORT=8000`

**O que é:** Porta onde a API será hospedada.

**Valores típicos:**
- `8000` - Porta padrão
- Qualquer porta disponível (ex: `3000`, `5000`, `8080`)

**Exemplo:**
```env
API_PORT=8000
```

---

### `ALLOWED_ORIGINS=`

**O que é:** Lista de origens permitidas para CORS (separadas por vírgula).

**Valores:**
- Vazio ou `*` - Permite todas as origens
- Lista específica: `http://localhost:3000,https://meusite.com`

**Exemplo:**
```env
ALLOWED_ORIGINS=
# ou
ALLOWED_ORIGINS=http://localhost:3000,https://meusite.com
```

---

### `RATE_LIMIT_PER_MINUTE=30`

**O que é:** Número máximo de requisições permitidas por minuto por IP.

**Valores típicos:**
- `10-30` - Conservador (recomendado para POC)
- `60-120` - Moderado
- `200+` - Alto (apenas para uso interno)

**Exemplo:**
```env
RATE_LIMIT_PER_MINUTE=30
```

---

## 🔐 Parâmetros de Autenticação

### `HF_TOKEN=seu_token_aqui`

**O que é:** Token de acesso do Hugging Face (obrigatório para modelos "gated").

**Como obter:**
1. Crie uma conta em https://huggingface.co/join
2. Solicite acesso ao modelo em https://huggingface.co/google/medgemma-4b-it
3. Gere um token em https://huggingface.co/settings/tokens
4. Cole o token aqui

**Importante:** Sem este token, o modelo não carregará (erro 401).

**Exemplo:**
```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📝 Parâmetros de Modelo

### `MODEL_ID=google/medgemma-4b-it`

**O que é:** ID do modelo a ser usado no Hugging Face.

**Valores:**
- `google/medgemma-4b-it` - Modelo padrão (requer token)
- Outros modelos compatíveis do Hugging Face

**Exemplo:**
```env
MODEL_ID=google/medgemma-4b-it
```

---

## 📊 Parâmetros de Logging

### `LOG_LEVEL=INFO`

**O que é:** Nível de detalhamento dos logs.

**Valores possíveis:**
- `DEBUG` - Muito detalhado (desenvolvimento)
- `INFO` - Informativo (padrão, recomendado)
- `WARNING` - Apenas avisos e erros
- `ERROR` - Apenas erros

**Exemplo:**
```env
LOG_LEVEL=INFO
```

---

### `LOG_DIR=./data/logs`

**O que é:** Diretório onde os arquivos de log serão salvos.

**Valores:**
- Caminho relativo: `./data/logs`
- Caminho absoluto: `C:/logs/medgemma`

**Exemplo:**
```env
LOG_DIR=./data/logs
```

---

## 📄 Exemplo Completo

Aqui está um exemplo completo de arquivo `.env`:

```env
# ============================================
# TOKEN DO HUGGING FACE (OBRIGATÓRIO)
# ============================================
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================
# CONFIGURAÇÃO DO MODELO
# ============================================
MODEL_ID=google/medgemma-4b-it
DEVICE=auto
USE_QUANTIZATION=false

# ============================================
# PARÂMETROS DE GERAÇÃO
# ============================================
MAX_NEW_TOKENS=512
TEMPERATURE=0.3
TOP_P=0.9

# ============================================
# LIMITES PARA CPU
# ============================================
CPU_MAX_NEW_TOKENS=512
CPU_MAX_TIME_S=60

# ============================================
# CONFIGURAÇÃO DA API
# ============================================
API_HOST=127.0.0.1
API_PORT=8000
ALLOWED_ORIGINS=
RATE_LIMIT_PER_MINUTE=30

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
LOG_DIR=./data/logs
```

---

## 💡 Recomendações

### Para Respostas Completas (Evitar Cortes)

Se suas respostas estão cortando no meio, ajuste:

```env
CPU_MAX_NEW_TOKENS=768
CPU_MAX_TIME_S=60
MAX_NEW_TOKENS=768
```

### Para Respostas Mais Rápidas (CPU)

Se você quer respostas mais rápidas em CPU (mas podem ser mais curtas):

```env
CPU_MAX_NEW_TOKENS=256
CPU_MAX_TIME_S=30
MAX_NEW_TOKENS=256
```

### Para Respostas Mais Consistentes (Saúde)

Para respostas médicas mais precisas e consistentes:

```env
TEMPERATURE=0.2
TOP_P=0.8
```

### Para Respostas Mais Criativas

Para respostas mais variadas (não recomendado para saúde):

```env
TEMPERATURE=0.7
TOP_P=0.95
```

---

## ⚠️ Observações Importantes

1. **Após alterar o `.env`**, você precisa **reiniciar o servidor** para as mudanças terem efeito.

2. **O arquivo `.env` não deve ser commitado** no Git (já deve estar no `.gitignore`).

3. **Valores em variáveis de ambiente** do sistema operacional têm prioridade sobre o arquivo `.env`.

4. **Para CPU**, os valores `CPU_MAX_NEW_TOKENS` e `CPU_MAX_TIME_S` são críticos para evitar cortes.

5. **O token do Hugging Face** é obrigatório para modelos "gated" como o MedGemma.

---

## 🔗 Links Úteis

- [Documentação do Hugging Face](https://huggingface.co/docs)
- [Documentação do Transformers](https://huggingface.co/docs/transformers)
- [Modelo MedGemma](https://huggingface.co/google/medgemma-4b-it)

---

**Última atualização:** Janeiro 2025
