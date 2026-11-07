import json

import httpx

from app.agent.groq import call_groq


async def test_call_groq_sends_system_and_question_and_returns_content() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "Vá à UBS Exemplo."}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        reply = await call_groq("chave", "modelo-x", "regras", "onde vacinar?", http_client=client)

    assert reply == "Vá à UBS Exemplo."
    assert seen["auth"] == "Bearer chave"
    assert seen["body"]["model"] == "modelo-x"
    assert seen["body"]["messages"] == [
        {"role": "system", "content": "regras"},
        {"role": "user", "content": "onde vacinar?"},
    ]
