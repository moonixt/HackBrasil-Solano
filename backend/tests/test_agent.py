import json
from datetime import date

from sqlalchemy import select

from app.agent import agent as agent_module
from app.agent import memory
from app.agent.tools import ToolContext, run_tool
from app.core.config import get_settings
from app.db.models import HealthUnit, Suggestion, User
from app.domain.enums import Service
from app.domain.regions import Region
from app.telegram.handlers import handle_update
from tests.telegram_factories import text_update

SOURCE_LINE = "Fonte: Secretaria de Saúde do Recife (teste) · atualizado em 15/10/2026"


async def _user_in_recife(session, chat_id: int, neighborhood: str = "Boa Viagem") -> User:
    user = User(telegram_chat_id=chat_id, city="Recife", uf="PE", region=Region.NORDESTE, neighborhood=neighborhood)
    session.add(user)
    await session.flush()
    return user


async def _unit(session, key: str, name: str, neighborhood: str) -> None:
    session.add(
        HealthUnit(
            external_key=key,
            name=name,
            kind="UBS",
            city="Recife",
            city_normalized="recife",
            uf="PE",
            neighborhood=neighborhood,
            services=[Service.VACINACAO.value],
            opening_hours="Seg a sex, 7h às 17h",
            accessibility="Rampa na entrada",
            source="Secretaria de Saúde do Recife (teste)",
            updated_at=date(2026, 10, 15),
        )
    )
    await session.flush()


def _tool_call(name: str, arguments: dict) -> dict:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"id": f"call-{name}", "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}
        ],
    }


def _scripted_llm(monkeypatch, *replies: dict | None) -> list[list[dict]]:
    """Troca o LLM por respostas roteirizadas e devolve as conversas que ele recebeu."""
    seen: list[list[dict]] = []
    queue = list(replies)

    async def fake_chat(messages, tools=None):
        seen.append(list(messages))
        return queue.pop(0)

    monkeypatch.setattr(agent_module, "chat", fake_chat)
    monkeypatch.setattr(get_settings(), "llm_api_key", "chave-de-teste")
    return seen


async def _say(session, client, chat_id: int, text: str) -> str:
    await handle_update(text_update(chat_id, text), session, client)
    return client.sent[-1].text


# Sem LLM: o bot ainda responde pelos dados.


async def test_without_llm_first_question_asks_location_and_then_answers_from_records(
    session, fake_telegram_client
) -> None:
    await _unit(session, "a", "UBS Teste Boa Viagem", "Boa Viagem")
    await session.commit()

    assert "cidade e o estado" in await _say(session, fake_telegram_client, 3001, "onde me vacino?")
    assert "agente do Nordeste" in await _say(session, fake_telegram_client, 3001, "Recife, PE, Boa Viagem")

    reply = await _say(session, fake_telegram_client, 3001, "onde me vacino?")
    assert "UBS Teste Boa Viagem" in reply
    assert SOURCE_LINE in reply


async def test_without_llm_neighborhood_match_ignores_case_and_accents(session, fake_telegram_client) -> None:
    await _user_in_recife(session, 3002, neighborhood="  varzea ")
    await _unit(session, "a", "UBS Primeira Boa Viagem", "Boa Viagem")
    await _unit(session, "b", "UBS Da Várzea", "Várzea")
    await session.commit()

    reply = await _say(session, fake_telegram_client, 3002, "onde tem vacina?")

    assert reply.index("UBS Da Várzea") < reply.index("UBS Primeira Boa Viagem")


async def test_uncovered_city_gets_the_not_covered_message(session, fake_telegram_client) -> None:
    session.add(User(telegram_chat_id=3003, city="Osasco", uf="SP", region=Region.SUDESTE))
    await session.commit()

    assert "Osasco/SP" in await _say(session, fake_telegram_client, 3003, "onde me vacino?")


async def test_emergency_never_reaches_the_llm(session, fake_telegram_client, monkeypatch) -> None:
    seen = _scripted_llm(monkeypatch)
    await _user_in_recife(session, 3004)
    await session.commit()

    reply = await _say(session, fake_telegram_client, 3004, "meu pai está com dor no peito")

    assert "192" in reply
    assert seen == []


# Com LLM: agente com ferramentas.


async def test_agent_searches_the_network_and_sources_come_from_the_records(
    session, fake_telegram_client, monkeypatch
) -> None:
    await _user_in_recife(session, 3005)
    await _unit(session, "a", "UBS Teste Boa Viagem", "Boa Viagem")
    await session.commit()
    seen = _scripted_llm(
        monkeypatch,
        _tool_call("buscar_rede_de_saude", {"servico": "vacinacao"}),
        {"role": "assistant", "content": "Vá à **UBS Teste Boa Viagem**.\nFonte: inventada\n[FONTES]"},
    )

    reply = await _say(session, fake_telegram_client, 3005, "onde me vacino?")

    tool_result = json.loads(seen[1][-1]["content"])
    assert tool_result["unidades"][0]["nome"] == "UBS Teste Boa Viagem"
    assert reply == f"Vá à UBS Teste Boa Viagem.\n{SOURCE_LINE}"


async def test_agent_saves_location_said_in_free_text(session, fake_telegram_client, monkeypatch) -> None:
    _scripted_llm(
        monkeypatch,
        _tool_call("salvar_localizacao", {"cidade": "Recife", "uf": "pe", "bairro": "Várzea"}),
        {"role": "assistant", "content": "Anotado, você está com o agente do Nordeste."},
    )

    await _say(session, fake_telegram_client, 3006, "moro em recife, na várzea")

    user = (await session.execute(select(User).where(User.telegram_chat_id == 3006))).scalar_one()
    assert (user.city, user.uf, user.region, user.neighborhood) == ("Recife", "PE", Region.NORDESTE, "Várzea")


async def test_agent_remembers_the_previous_turn(session, fake_telegram_client, monkeypatch) -> None:
    await _user_in_recife(session, 3007)
    await session.commit()
    seen = _scripted_llm(
        monkeypatch,
        {"role": "assistant", "content": "Leve documento com foto."},
        {"role": "assistant", "content": "Não precisa agendar."},
    )

    await _say(session, fake_telegram_client, 3007, "que documentos levo?")
    await _say(session, fake_telegram_client, 3007, "e precisa agendar?")

    contents = [message["content"] for message in seen[1]]
    assert "que documentos levo?" in contents
    assert "Leve documento com foto." in contents
    memory.forget(3007)


async def test_agent_failure_falls_back_to_the_records(session, fake_telegram_client, monkeypatch) -> None:
    await _user_in_recife(session, 3008)
    await _unit(session, "a", "UBS Teste Boa Viagem", "Boa Viagem")
    await session.commit()
    _scripted_llm(monkeypatch, None)

    reply = await _say(session, fake_telegram_client, 3008, "onde me vacino?")

    assert "UBS Teste Boa Viagem" in reply
    assert SOURCE_LINE in reply


async def test_pending_suggestion_never_reaches_the_llm(session, fake_telegram_client, monkeypatch) -> None:
    user = await _user_in_recife(session, 3009)
    await _unit(session, "a", "UBS Teste Boa Viagem", "Boa Viagem")
    session.add(Suggestion(user_id=user.id, city="Recife", uf="PE", text="MARCADOR-PENDENTE"))
    await session.commit()
    seen = _scripted_llm(
        monkeypatch,
        _tool_call("buscar_rede_de_saude", {}),
        {"role": "assistant", "content": "ok"},
    )

    await _say(session, fake_telegram_client, 3009, "o que tem perto?")

    assert "MARCADOR-PENDENTE" not in json.dumps(seen, ensure_ascii=False)


async def test_agent_registers_a_suggestion_as_pending(session, fake_telegram_client, monkeypatch) -> None:
    await _user_in_recife(session, 3010)
    await session.commit()
    _scripted_llm(
        monkeypatch,
        _tool_call("registrar_sugestao", {"texto": "A UBS agora abre às 7h"}),
        {"role": "assistant", "content": "Obrigado! Fica pendente até ser verificada."},
    )

    await _say(session, fake_telegram_client, 3010, "a UBS agora abre às 7h")

    suggestion = (await session.execute(select(Suggestion))).scalar_one()
    assert (suggestion.text, suggestion.status.value) == ("A UBS agora abre às 7h", "pending")


async def test_tools_reject_bad_arguments_with_a_readable_error(session) -> None:
    ctx = ToolContext(session=session, user=User(telegram_chat_id=1))

    assert "erro" in await run_tool(ctx, "salvar_localizacao", '{"cidade": "Recife", "uf": "XX"}')
    assert "erro" in await run_tool(ctx, "buscar_rede_de_saude", "{}")
    assert "erro" in await run_tool(ctx, "nao_existe", "{}")
    assert "erro" in await run_tool(ctx, "salvar_localizacao", "{nao é json")


async def test_web_answer_keeps_only_sources_the_search_returned(session, fake_telegram_client, monkeypatch) -> None:
    session.add(User(telegram_chat_id=3011, city="Osasco", uf="SP", region=Region.SUDESTE))
    await session.commit()
    search_output = "L4: 【0†Campanha de vacinação†osasco.sp.gov.br】\nL5: URL: https://exa.ai/search?q=vacina"
    _scripted_llm(
        monkeypatch,
        {
            "role": "assistant",
            "content": (
                "Segundo a prefeitura, todas as UBS vacinam 【0†L4】.\n"
                "| Tipo | Unidade |\n|---|---|\n| UBS | Maria Pia |\n"
                "Fonte: Prefeitura de Osasco (osasco.sp.gov.br) · 10/04/2026\n"
                "Fonte: Blog qualquer (exemplo.com)"
            ),
            "executed_tools": [{"type": "browser_search", "output": search_output}],
        },
    )

    reply = await _say(session, fake_telegram_client, 3011, "onde me vacino?")

    assert reply == (
        "Segundo a prefeitura, todas as UBS vacinam.\n"
        "• UBS – Maria Pia\n"
        "Fonte: Prefeitura de Osasco (osasco.sp.gov.br) · 10/04/2026"
    )


def test_web_search_tool_is_offered_only_when_enabled(monkeypatch) -> None:
    from app.agent.tools import agent_tools

    settings = get_settings()
    monkeypatch.setattr(settings, "llm_web_search", True)
    assert {"type": "browser_search"} in agent_tools()
    monkeypatch.setattr(settings, "llm_web_search", False)
    assert {"type": "browser_search"} not in agent_tools()
