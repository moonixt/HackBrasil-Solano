"""Chamada ao Claude (Anthropic) para a resposta final, quando ANTHROPIC_API_KEY existe."""

import anthropic

_MAX_TOKENS = 1024


async def call_claude(api_key: str, model: str, system_prompt: str, question: str) -> str:
    client = anthropic.AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=_MAX_TOKENS,
        system=system_prompt,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": question}],
    )
    return next((block.text for block in response.content if block.type == "text"), "")
