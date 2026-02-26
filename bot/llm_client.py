import json
import uuid
import time
import httpx

from bot.config import (
    GIGACHAT_AUTH_KEY,
    GIGACHAT_SCOPE,
    GIGACHAT_MODEL,
    GIGACHAT_VERIFY_SSL,
)

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

_token_cache = {"access_token": None, "expires_at": 0}

class LLMError(Exception):
    pass

async def _get_access_token() -> str:
    now = int(time.time())
    if _token_cache["access_token"] and now < (_token_cache["expires_at"] - 30):
        return _token_cache["access_token"]

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {GIGACHAT_AUTH_KEY}",
    }
    data = {"scope": GIGACHAT_SCOPE}

    async with httpx.AsyncClient(timeout=30, verify=GIGACHAT_VERIFY_SSL) as client:
        r = await client.post(OAUTH_URL, headers=headers, data=data)

    if r.status_code >= 400:
        raise LLMError(f"GigaChat OAuth HTTP {r.status_code}: {r.text}")

    payload = r.json()
    token = payload.get("access_token")
    exp = payload.get("expires_at")
    if not token or not exp:
        raise LLMError(f"Bad OAuth response: {payload}")

    _token_cache["access_token"] = token
    _token_cache["expires_at"] = int(exp)
    return token

async def gigachat_chat_json(system: str, user: str) -> dict:
    access_token = await _get_access_token()

    body = {
        "model": GIGACHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient(timeout=60, verify=GIGACHAT_VERIFY_SSL) as client:
        r = await client.post(CHAT_URL, headers=headers, json=body)

    if r.status_code >= 400:
        raise LLMError(f"GigaChat chat HTTP {r.status_code}: {r.text}")

    data = r.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except Exception:
        raise LLMError(f"Unexpected chat response: {data}")

    try:
        return json.loads(text)
    except Exception as e:
        raise LLMError(f"Model returned non-JSON: {text}") from e