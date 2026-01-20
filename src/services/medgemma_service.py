from __future__ import annotations

import hashlib
import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional, Tuple

from loguru import logger

from src.core.config import Settings, get_settings

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover
    torch = None  # type: ignore


DISCLAIMER_PTBR = (
    "Esta é uma orientação automatizada e não substitui a consulta com um profissional de saúde."
)


SYSTEM_PROMPT_GENERAL_PTBR = (
    "Você é um assistente de TRIAGEM EM SAÚDE (pré-atendimento), focado em coletar informações, "
    "identificar sinais de alerta (red flags) e orientar o próximo passo (ex.: emergência, urgência, rotina). "
    "Você NÃO faz diagnóstico definitivo, NÃO define tratamento, mas pode prescreve medicamentos MIP (Medicamentos Isentos de Prescrição) se necessário. "
    "Seu trabalho é: (1) entender a queixa, (2) fazer perguntas objetivas para completar dados, "
    "(3) sinalizar possíveis riscos com base em sintomas e (4) recomendar o nível de procura de atendimento. "
    "\n\n"
    "Prioridade máxima: segurança. Se houver sinais compatíveis com emergência (ex.: dor no peito intensa, "
    "falta de ar importante, desmaio, sinais de AVC, confusão mental, sangramento importante, "
    "reação alérgica grave, convulsão, piora rápida, dor muito forte, rigidez de nuca com febre, "
    "ideação suicida, intoxicação), oriente procurar pronto atendimento/urgência imediatamente "
    "e não continue com triagem longa."
    "\n\n"
    "Em cada resposta, siga EXATAMENTE este formato em TEXTO PURO (sem Markdown):"
    "\n"
    "(faça de 2 a 5 perguntas curtas e diretas para confirmar o diagnóstico e orientar o próximo passo)\n"
    "3) SINAIS DE ALERTA: (se houver, liste em uma frase o(s) sinal(is) e por que preocupa; se não houver, diga 'não identificados por enquanto')\n"
    "4) PRÓXIMO PASSO RECOMENDADO: (EMERGENCIA/URGENTE/ROTINA/INSUFICIENTE) + recomendação objetiva\n"
    "\n\n"
    "Regras de conversa: mantenha continuidade, não se reapresente, não invente informações. "
    "Se faltarem dados essenciais, use 'INSUFICIENTE' e pergunte. "
    "Responda sempre em português brasileiro, em texto puro."
)

SYSTEM_PROMPT_TRIAGE_PTBR = (
    "Você é um assistente de saúde treinado para fazer triagem inicial de sintomas.\n"
    "Sua função é:\n"
    "- Coletar informações sobre sintomas\n"
    "- Fazer perguntas clarificadoras quando necessário\n"
    "- Indicar o nível de urgência (verde/amarelo/vermelho)\n"
    "- NUNCA dar diagnósticos definitivos\n"
    "- Sempre recomendar buscar um profissional de saúde\n\n"
    "Responda sempre em português brasileiro de forma clara e empática.\n"
    "Mantenha continuidade entre as mensagens (não se reapresente a cada resposta).\n"
    "Responda em TEXTO PURO (sem Markdown)."
)

SYSTEM_PROMPT_EXPLAIN_PTBR = (
    "Você é um assistente de saúde especializado em explicar termos médicos de forma simples.\n"
    "Explique o termo solicitado de maneira que uma pessoa leiga possa entender.\n"
    "Use analogias do dia a dia quando apropriado.\n"
    "Responda em português brasileiro.\n"
    "Responda em TEXTO PURO (sem Markdown)."
)


@dataclass
class GenerationResult:
    text: str
    processing_time_ms: float
    model_used: str


class MedGemmaService:
    _instance: Optional["MedGemmaService"] = None

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._tokenizer = None
        self._model = None
        self._pipeline = None
        self._device = "cpu"
        self._model_loaded = False
        self._quantized = False
        self._load_error: Optional[str] = None
        self._created_at = time.time()

        # Cache simples (LRU) para prompts repetidos
        self._cache: "OrderedDict[str, str]" = OrderedDict()
        self._cache_max_items = 128

    @classmethod
    def get_instance(cls) -> "MedGemmaService":
        if cls._instance is None:
            cls._instance = MedGemmaService()
        return cls._instance

    def uptime_s(self) -> float:
        return max(0.0, time.time() - self._created_at)

    def is_loaded(self) -> bool:
        return self._model_loaded

    def device(self) -> str:
        return self._device

    def use_quantization(self) -> bool:
        return bool(self._quantized)

    def load_error(self) -> Optional[str]:
        return self._load_error

    def _pick_device(self) -> str:
        cfg = (self._settings.device or "auto").strip().lower()
        if torch is None:
            return "cpu"
        if cfg == "cpu":
            return "cpu"
        if cfg == "cuda":
            return "cuda" if torch.cuda.is_available() else "cpu"
        # auto
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _hf_kwargs(self) -> dict:
        if not self._settings.hf_token:
            return {}
        # Compatibilidade: algumas versões usam `token`, outras `use_auth_token`.
        return {"token": self._settings.hf_token}

    def load_model(self) -> None:
        if self._model_loaded:
            return

        start = time.time()
        if torch is None:
            self._load_error = "Dependência ausente: torch"
            raise RuntimeError("Dependência ausente: torch. Instale requirements.txt para habilitar o modelo.")
        self._device = self._pick_device()
        self._quantized = False
        self._load_error = None

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

            logger.info(
                "Carregando modelo: model_id={} device={} use_quantization={}",
                self._settings.model_id,
                self._device,
                self._settings.use_quantization,
            )

            tokenizer_kwargs = self._hf_kwargs()
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(self._settings.model_id, **tokenizer_kwargs)
            except TypeError:
                # fallback antigo
                if "token" in tokenizer_kwargs:
                    tokenizer_kwargs = {"use_auth_token": tokenizer_kwargs["token"]}
                self._tokenizer = AutoTokenizer.from_pretrained(self._settings.model_id, **tokenizer_kwargs)

            model_kwargs = {}

            if self._device == "cuda":
                model_kwargs["torch_dtype"] = torch.float16
                model_kwargs["device_map"] = "auto"
            else:
                model_kwargs["torch_dtype"] = torch.float32

            if self._device == "cuda" and self._settings.use_quantization:
                try:
                    qconfig = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                    )
                    model_kwargs["quantization_config"] = qconfig
                    model_kwargs["device_map"] = "auto"
                    self._quantized = True
                except Exception as e:
                    logger.warning("Falha ao habilitar quantização 4-bit; seguindo sem quantização. err={}", str(e))

            model_hf_kwargs = self._hf_kwargs()
            try:
                self._model = AutoModelForCausalLM.from_pretrained(
                    self._settings.model_id,
                    **model_kwargs,
                    **model_hf_kwargs,
                )
            except TypeError:
                if "token" in model_hf_kwargs:
                    model_hf_kwargs = {"use_auth_token": model_hf_kwargs["token"]}
                self._model = AutoModelForCausalLM.from_pretrained(
                    self._settings.model_id,
                    **model_kwargs,
                    **model_hf_kwargs,
                )

            self._model.eval()

            # Pipeline para simplificar geração com device_map (CPU/GPU/sharding).
            pipe_kwargs = {
                "model": self._model,
                "tokenizer": self._tokenizer,
            }
            if self._device == "cuda":
                pipe_kwargs["device_map"] = "auto"
            else:
                # pipeline em CPU
                pipe_kwargs["device"] = -1

            self._pipeline = pipeline("text-generation", **pipe_kwargs)

            self._model_loaded = True
            logger.info(
                "Modelo carregado com sucesso em {:.0f}ms (device={}, quantized={})",
                (time.time() - start) * 1000,
                self._device,
                self._quantized,
            )
        except Exception as e:
            self._model_loaded = False
            self._load_error = str(e)
            logger.exception("Falha ao carregar modelo: {}", str(e))
            raise

    def _cache_get(self, key: str) -> Optional[str]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def _cache_set(self, key: str, value: str) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_max_items:
            self._cache.popitem(last=False)

    def _make_prompt(self, prompt: str, system_prompt: Optional[str], context: Optional[str]) -> str:
        sys = system_prompt or SYSTEM_PROMPT_GENERAL_PTBR
        user = prompt.strip()
        if context:
            user = f"Contexto adicional:\n{context.strip()}\n\nPergunta:\n{user}"

        # Preferir chat template, se o tokenizer suportar.
        if hasattr(self._tokenizer, "apply_chat_template"):
            messages = [{"role": "system", "content": sys}, {"role": "user", "content": user}]
            try:
                return self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                # fallback: concat simples
                pass

        return f"SISTEMA:\n{sys}\n\nUSUÁRIO:\n{user}\n\nASSISTENTE:\n"

    def _cache_key(self, prompt: str, system_prompt: Optional[str], context: Optional[str]) -> str:
        raw = f"{system_prompt or ''}\n---\n{context or ''}\n---\n{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _clean_generated_text(self, text: str) -> str:
        """
        Limpa e ajusta o texto gerado para evitar cortes no meio de palavras ou frases.
        Garante que o texto termine de forma adequada.
        """
        if not text:
            return text

        text = text.strip()

        # Se o texto terminar com pontuação adequada, considera completo
        if text and text[-1] in ".!?:;":
            return text

        # Se o texto terminar com letra/dígito (possível corte no meio da palavra)
        # Verifica se há pontuação próxima ao final que indique fim natural
        if text and text[-1].isalnum():
            # Procura os últimos sinais de pontuação que indicam fim natural
            punct_chars = [".", "!", "?", ":", ";", ","]
            last_punct = -1
            for punct in punct_chars:
                pos = text.rfind(punct)
                if pos > last_punct:
                    last_punct = pos

            # Se encontrou pontuação nos últimos 50 caracteres, mantém até ela (mais conservador)
            if last_punct > 0 and last_punct > len(text) - 50:
                text = text[: last_punct + 1].strip()
                return text

            # Se não encontrou pontuação próxima, procura o último espaço
            # e remove a palavra incompleta apenas se estiver muito próxima do final
            last_space = text.rfind(" ")
            if last_space > 0 and last_space > len(text) - 15:
                # Remove apenas a última palavra quebrada (mais conservador)
                text = text[:last_space].strip()
                # Não adiciona reticências automaticamente para não confundir o usuário

        return text

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
    ) -> GenerationResult:
        """
        Gera resposta do modelo (lazy loading).
        Retorna apenas o texto do assistente; o disclaimer é adicionado na camada da API.
        """
        if not self._model_loaded:
            self.load_model()

        cache_key = self._cache_key(prompt, system_prompt, context)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return GenerationResult(
                text=cached,
                processing_time_ms=0.0,
                model_used=self._settings.model_id,
            )

        prompt_text = self._make_prompt(prompt=prompt, system_prompt=system_prompt, context=context)

        # Proteções para execução em CPU (POC):
        # - limitar tokens para evitar travas longas
        # - limitar tempo para sempre retornar (mesmo que parcial)
        max_new_tokens = int(self._settings.max_new_tokens)
        max_time_s: Optional[float] = None

        if self._device == "cpu":
            # Aumentado o limite padrão para 512 tokens (mais razoável para respostas completas)
            # Permite respostas mais completas sem quebrar no meio das palavras
            max_new_tokens = min(max_new_tokens, int(os.getenv("CPU_MAX_NEW_TOKENS", "512")))
            try:
                max_time_s = float(os.getenv("CPU_MAX_TIME_S", "60"))  # Aumentado para 60s
            except ValueError:
                max_time_s = 60.0

        t0 = time.time()
        gen_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": (self._settings.temperature > 0),
            "temperature": self._settings.temperature,
            "top_p": self._settings.top_p,
            "return_full_text": False,
        }
        if max_time_s is not None:
            gen_kwargs["max_time"] = max_time_s

        outputs = self._pipeline(prompt_text, **gen_kwargs)
        dt_ms = (time.time() - t0) * 1000

        # Pipeline retorna lista[dict]; pegamos generated_text
        text = ""
        try:
            text = (outputs[0].get("generated_text") or "").strip()
        except Exception:
            text = str(outputs).strip()

        # Garantir que o texto termine de forma adequada (evitar corte no meio de palavras/frases)
        text = self._clean_generated_text(text)

        self._cache_set(cache_key, text)
        return GenerationResult(
            text=text,
            processing_time_ms=dt_ms,
            model_used=self._settings.model_id,
        )

