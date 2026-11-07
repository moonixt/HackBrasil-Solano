"""Chamada à Groq (API compatível com a da OpenAI) para a resposta final, quando GROQ_API_KEY existe."""

import httpx

_URL = "https://api.groq.com/openai/v1/chat/completions"
_MAX_TOKENS = 1024


async def call_groq(
    api_key: str,
    model: str,
    system_prompt: str,
    question: str,
    http_client: httpx.AsyncClient | None = None,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "max_completion_tokens": _MAX_TOKENS,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    if http_client is None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(_URL, json=payload, headers=headers)
    else:
        response = await http_client.post(_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"].get("content") or ""
