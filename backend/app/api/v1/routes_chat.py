import os

import anthropic
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services import chat_limiter
from app.services.chat_knowledge import build_system_prompt
from app.services.store import store

router = APIRouter()

CHAT_MODEL = "claude-opus-5"
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
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail={
            "detail": "Чат-бот временно недоступен: не настроен ANTHROPIC_API_KEY на сервере.",
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
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": payload.message})

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=CHAT_MODEL,
            max_tokens=1024,
            system=system_prompt,
            output_config={"effort": "low"},
            messages=messages,
        )
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail={
            "detail": "Ошибка при обращении к Claude API", "code": "CHAT_UPSTREAM_ERROR",
        }) from e

    if response.stop_reason == "refusal":
        raise HTTPException(status_code=422, detail={
            "detail": "Не удалось ответить на этот вопрос.", "code": "CHAT_REFUSAL",
        })

    reply = "".join(block.text for block in response.content if block.type == "text")
    return {"reply": reply}
