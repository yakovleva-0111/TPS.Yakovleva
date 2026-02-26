import json
import time
import uuid

import httpx

from bot.config import GIGACHAT_AUTH_KEY, GIGACHAT_MODEL, GIGACHAT_SCOPE, GIGACHAT_VERIFY_SSL


OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

_token = {"value": "", "expires_at": 0}


class GigaChatError(RuntimeError):
    pass


async def _access_token() -> str:
    if not GIGACHAT_AUTH_KEY:
        raise GigaChatError("GIGACHAT_AUTH_KEY is empty")

    now = int(time.time())
    if _token["value"] and now < (_token["expires_at"] - 30):
        return _token["value"]

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {GIGACHAT_AUTH_KEY}",
    }

    async with httpx.AsyncClient(timeout=30, verify=GIGACHAT_VERIFY_SSL) as client:
        r = await client.post(OAUTH_URL, headers=headers, data={"scope": GIGACHAT_SCOPE})

    if r.status_code >= 400:
        raise GigaChatError(f"oauth {r.status_code}: {r.text}")

    data = r.json()
    token = data.get("access_token")
    exp = data.get("expires_at")
    if not token or not exp:
        raise GigaChatError(f"bad oauth response: {data}")

    _token["value"] = token
    _token["expires_at"] = int(exp)
    return token


async def gigachat_chat_text(system: str, user: str) -> str:
    token = await _access_token()

    body = {
        "model": GIGACHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60, verify=GIGACHAT_VERIFY_SSL) as client:
        r = await client.post(CHAT_URL, headers=headers, json=body)

    if r.status_code >= 400:
        raise GigaChatError(f"chat {r.status_code}: {r.text}")

    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise GigaChatError(f"bad chat response: {data}") from e


async def gigachat_chat_json(system: str, user: str) -> dict:
    text = await gigachat_chat_text(system=system, user=user)
    try:
        return json.loads(text)
    except Exception as e:
        raise GigaChatError(f"model returned non-json: {text}") from e
