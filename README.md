# HackBrasil Solano

Agente de WhatsApp dividido por regiões do Brasil, com memória compartilhada por região — no espírito do OpenStreetMap.

## Visão geral

O Solano é um agente no WhatsApp que atende a pessoa a partir da região onde ela está. No primeiro contato, pergunta cidade/estado e cria a conta só com **nome** e **telefone**. A partir daí, a conversa segue com o **agente regional** daquela área, que tem acesso mais fácil a informações relevantes para Sul, Sudeste, Centro-Oeste, Norte ou Nordeste.

Cada agente regional mantém uma **memória compartilhada** entre todas as pessoas da mesma região. As interações alimentam e enriquecem esse conhecimento ao longo do tempo, de forma colaborativa (inspirada no OSM).

## Como funciona

1. A pessoa envia a primeira mensagem no WhatsApp.
2. O agente pergunta de qual **cidade/estado** ela é.
3. A conta é criada com **nome** e **telefone**.
4. A conversa é roteada para o **agente da região** correspondente.
5. O agente regional responde com contexto local e, com o uso, a memória da região vai sendo atualizada.

## Memória compartilhada por região

O conhecimento não fica só na conversa individual. Tudo o que as pessoas da mesma região compartilham pode alimentar um acervo comum daquele território:

- **Por região:** cada uma das cinco regiões tem a própria memória.
- **Coletiva:** todas as pessoas daquela região contribuem para o mesmo conjunto de informações.
- **Estilo OSM:** as interações enriquecem o mapa de conhecimento local ao longo do tempo (ruas, serviços, hábitos, avisos — o que a própria região for ensinando).

Assim, quem chega depois se beneficia do que a comunidade já relatou.

## Regiões e exemplos de cidades

O Brasil é modelado nas cinco regiões oficiais. As cidades abaixo são **exemplos** (não um limite):

| Região | Exemplos de cidades |
| --- | --- |
| **Sul** | Porto Alegre, Curitiba, Florianópolis, Pelotas, Joinville |
| **Sudeste** | São Paulo, Rio de Janeiro, Belo Horizonte, Campinas, Vitória |
| **Centro-Oeste** | Brasília, Goiânia, Campo Grande, Cuiabá, Anápolis |
| **Norte** | Manaus, Belém, Porto Velho, Boa Vista, Macapá |
| **Nordeste** | Salvador, Recife, Fortaleza, São Luís, Natal |

![Cinco regiões do Brasil como círculos ligados, com cidades de exemplo e e-mails ilustrativos de agentes regionais](docs/regioes-brasil.png)

No diagrama, cada círculo é uma região; as setas apontam para cidades de exemplo. Também aparecem contatos ilustrativos de agentes regionais, por exemplo:

- Sudeste: `agente@chainsudrj.com`, `agente@chainsudsp.com`
- Nordeste: `agente@chainnordre.com`, `agente@chainnordna.com`

## Stack / status

Em construção no **HackBrasil**.

- **Backend:** API em FastAPI, neste repositório (`backend/`), com Postgres e a extensão **pgvector**.
- **Frontend:** Next.js, em projeto separado.
- **Canal do MVP:** Telegram.
- **Banco:** conexão por `DATABASE_URL` (SQLAlchemy assíncrono + Alembic).

A visão das seções acima descreve o produto. Usuários, regiões e a memória compartilhada entram nas issues seguintes; esta etapa sobe a API, o Postgres e a extensão `vector`.

## Backend local

Pré-requisitos: Docker (com Compose), Python 3.12+ e [uv](https://docs.astral.sh/uv/).

Na raiz do repositório:

```bash
cp .env.example .env
docker compose up -d
```

O serviço `db` sobe a imagem `pgvector/pgvector` e publica o Postgres em `localhost:5432`. As credenciais padrão estão no `.env.example` (`solano` / `solano`, banco `solano`). Se mudar usuário, senha ou porta, mantenha `DATABASE_URL` alinhada com o Compose.

Depois, instale o backend, aplique as migrations e suba a API:

```bash
cd backend
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

A migration inicial habilita a extensão `vector`.

Confira o healthcheck:

```bash
curl -s http://127.0.0.1:8000/health
```

Com o Postgres no ar e as migrations aplicadas, a resposta é `{"status":"ok","database":"connected"}`. Se o banco estiver fora, a rota responde `503` com `"database":"disconnected"`.

Testes (o Postgres precisa estar no ar, com `alembic upgrade head` já executado):

```bash
cd backend
uv run pytest
```

Sem uv, no diretório `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pytest
```

## Contribuindo / próximos passos

Este repositório começa pela ideia e pelo modelo regional. Próximos passos naturais:

- Definir o fluxo de primeiro contato (cidade/estado → conta nome + telefone).
- Implementar o roteamento para o agente de cada região.
- Desenhar a memória compartilhada por região (como as interações entram e como são consultadas).

Sugestões e PRs são bem-vindos — mantenha o escopo alinhado à ideia acima, sem inflar o produto.
