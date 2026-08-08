import os

from fastapi import APIRouter, HTTPException, Request
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field

from app.services import chat_limiter
from app.services.chat_knowledge import build_system_prompt
from app.services.store import store

router = APIRouter()

CHAT_MODEL = "gemini-flash-latest"  # бесплатный тир через Google AI Studio; алиас на актуальную flash-модель
MAX_HISTORY_TURNS = 8  # сколько последних пар сообщений отдаём модели


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)
    lang: str = "ru"


@router.post("/chat")
def chat(payload: ChatIn, request: Request):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail={
            "detail": "Чат-бот временно недоступен: не настроен GEMINI_API_KEY на сервере.",
            "code": "CHAT_NOT_CONFIGURED",
        })

    client_ip = request.client.host if request.client else "unknown"
    if chat_limiter.rate_limited(client_ip):
        raise HTTPException(status_code=429, detail={
            "detail": f"Превышен лимит сообщений — не более {chat_limiter.RATE_LIMIT_PER_HOUR} в час",
            "code": "RATE_LIMITED",
        })

    system_prompt = build_system_prompt(store, lang=payload.lang)
    history = payload.history[-MAX_HISTORY_TURNS * 2:]
    # Gemini использует роль "model" вместо "assistant"
    contents = [
        types.Content(role=("model" if m.role == "assistant" else "user"), parts=[types.Part(text=m.content)])
        for m in history
    ]
    contents.append(types.Content(role="user", parts=[types.Part(text=payload.message)]))

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024,
            ),
        )
    except genai_errors.APIError as e:
        raise HTTPException(status_code=502, detail={
            "detail": "Ошибка при обращении к Gemini API", "code": "CHAT_UPSTREAM_ERROR",
        }) from e

    reply = response.text
    if not reply:
        raise HTTPException(status_code=422, detail={
            "detail": "Не удалось ответить на этот вопрос.", "code": "CHAT_REFUSAL",
        })

    return {"reply": reply}
