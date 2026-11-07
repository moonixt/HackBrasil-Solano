from datetime import date

from app.db.models import HealthUnit, Suggestion, User
from app.domain.enums import OnboardingStep, Service
from app.domain.regions import Region
from app.telegram.handlers import handle_update
from tests.telegram_factories import text_update


async def _ready_user_in_recife(session, chat_id: int, neighborhood: str = "Boa Viagem") -> User:
    user = User(
        telegram_chat_id=chat_id,
        name="Maria",
        phone="+5581999998888",
        city="Recife",
        uf="PE",
        region=Region.NORDESTE,
        neighborhood=neighborhood,
        onboarding_step=OnboardingStep.READY,
    )
    session.add(user)
    await session.flush()
    return user


async def _seed_recife_unit(session) -> HealthUnit:
    unit = HealthUnit(
        external_key="test-ubs-boa-viagem",
        name="UBS Teste Boa Viagem",
        kind="UBS",
        city="Recife",
        city_normalized="recife",
        uf="PE",
        neighborhood="Boa Viagem",
        address="Rua de teste, 123",
        services=[Service.VACINACAO.value, Service.CONSULTA.value],
        opening_hours="Seg a sex, 7h às 17h",
        scheduling="Ordem de chegada",
        source="Secretaria de Saúde do Recife (teste)",
        updated_at=date(2026, 10, 15),
    )
    session.add(unit)
    await session.flush()
    return unit


async def test_vaccination_question_returns_boa_viagem_unit_with_source_line(
    session, fake_telegram_client
) -> None:
    chat_id = 2001
    await _ready_user_in_recife(session, chat_id)
    await _seed_recife_unit(session)
    await session.commit()

    await handle_update(text_update(chat_id, "onde consigo me vacinar?"), session, fake_telegram_client)

    reply = fake_telegram_client.sent[-1].text
    assert "UBS Teste Boa Viagem" in reply
    assert "Fonte:" in reply
    assert "15/10/2026" in reply


async def test_pending_suggestion_text_never_appears_in_an_answer(session, fake_telegram_client) -> None:
    chat_id = 2002
    user = await _ready_user_in_recife(session, chat_id)
    await _seed_recife_unit(session)
    session.add(
        Suggestion(user_id=user.id, city="Recife", uf="PE", text="MARCADOR-SECRETO-NUNCA-DEVE-APARECER")
    )
    await session.commit()

    await handle_update(text_update(chat_id, "onde consigo me vacinar?"), session, fake_telegram_client)

    reply = fake_telegram_client.sent[-1].text
    assert "MARCADOR-SECRETO" not in reply


async def test_user_in_uncovered_city_gets_not_covered_message(session, fake_telegram_client) -> None:
    chat_id = 2003
    user = User(
        telegram_chat_id=chat_id,
        city="São Paulo",
        uf="SP",
        region=Region.SUDESTE,
        neighborhood="Centro",
        onboarding_step=OnboardingStep.READY,
    )
    session.add(user)
    await session.commit()

    await handle_update(text_update(chat_id, "onde consigo me vacinar?"), session, fake_telegram_client)

    reply = fake_telegram_client.sent[-1].text.lower()
    assert "não tenho dados" in reply or "ainda não" in reply
    assert "136" in reply


async def test_emergency_phrase_returns_samu_and_no_unit(session, fake_telegram_client) -> None:
    chat_id = 2004
    await _ready_user_in_recife(session, chat_id)
    await _seed_recife_unit(session)
    await session.commit()

    await handle_update(text_update(chat_id, "estou com dor no peito"), session, fake_telegram_client)

    reply = fake_telegram_client.sent[-1].text
    assert "192" in reply
    assert "UBS Teste" not in reply


async def _seed_unit_in(session, key: str, name: str, neighborhood: str) -> None:
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
            source="Fonte de teste",
            updated_at=date(2026, 10, 15),
        )
    )


async def test_neighborhood_match_ignores_case_and_accents(session, fake_telegram_client) -> None:
    chat_id = 2010
    await _ready_user_in_recife(session, chat_id, neighborhood="  varzea ")
    await _seed_unit_in(session, "a-boa-viagem", "UBS Primeira Boa Viagem", "Boa Viagem")
    await _seed_unit_in(session, "b-varzea", "UBS Da Várzea", "Várzea")
    await session.commit()

    await handle_update(text_update(chat_id, "onde tem vacina?"), session, fake_telegram_client)

    reply = fake_telegram_client.sent[-1].text
    assert reply.index("UBS Da Várzea") < reply.index("UBS Primeira Boa Viagem")


async def test_claude_failure_still_answers_from_the_records(
    session, fake_telegram_client, monkeypatch
) -> None:
    import anthropic
    import httpx

    from app.agent import service as agent_service

    async def failing_claude(*_args, **_kwargs) -> str:
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))

    monkeypatch.setattr(agent_service, "call_claude", failing_claude)
    monkeypatch.setattr(agent_service.get_settings(), "anthropic_api_key", "chave-de-teste")

    chat_id = 2011
    await _ready_user_in_recife(session, chat_id)
    await _seed_recife_unit(session)
    await session.commit()

    await handle_update(text_update(chat_id, "onde consigo me vacinar?"), session, fake_telegram_client)

    reply = fake_telegram_client.sent[-1].text
    assert "UBS Teste Boa Viagem" in reply
    assert "Fonte:" in reply


async def test_non_text_message_after_onboarding_gets_help(session, fake_telegram_client) -> None:
    chat_id = 2012
    await _ready_user_in_recife(session, chat_id)
    await session.commit()

    sticker = {"update_id": 9, "message": {"message_id": 9, "chat": {"id": chat_id}, "from": {"id": chat_id}}}
    await handle_update(sticker, session, fake_telegram_client)

    assert "/ajuda" in fake_telegram_client.sent[-1].text
