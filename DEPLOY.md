# Как развернуть «Нить»

Два варианта: локально (для разработки и демо) и на сервере в Docker.

## Локально

Нужны Docker с compose v2, Node 22/24 + pnpm (`corepack enable`), Python 3.12 + [uv](https://docs.astral.sh/uv/), make.

```bash
git clone <url-репозитория> nit && cd nit
cp backend/.env.example backend/.env   # впиши GIGACHAT_AUTH_KEY
make setup                             # зависимости, postgres + s3 в докере, миграции, демо данные
make dev                               # фронт :3000 + бэк :8000
```

- сайт: http://localhost:3000
- swagger: http://localhost:8000/api/docs
- вход: `demo@nit.demo` / `demo1234` (ещё `igor.vlasov@nit.demo` эксперт и `admin@nit.demo` админ, пароль тот же)

ИИ:
- **GigaChat** (черновики, улучшение шагов, проверка, разбор узких мест, подсказки). Ключ авторизации берётся в личном кабинете GigaChat API на developers.sber.ru, кладётся в `GIGACHAT_AUTH_KEY`. Без ключа всё работает, кроме ИИ кнопок. `AI_FAKE=true` включает заглушку без сети.
- **Эмбеддинги** для умного поиска считает открытая модель Сбера `ai-forever/ru-en-RoSBERTa` прямо в бэке. При первом запуске она качается с HuggingFace (~1.5 ГБ) в `~/.cache/huggingface`. Выключить: `EMBEDDINGS_ENABLED=false`, тогда поиск работает без семантики.

Порты: Postgres 5434, S3 9010 (не 5432, чтобы не конфликтовать с локальным постгресом).

## На сервере (Docker)

Всё поднимается одним compose-файлом `docker-compose.prod.yml`: postgres, s3 (SeaweedFS), api (FastAPI), web (Nuxt) и caddy. Наружу открыт только caddy на 80/443: он сам получает сертификат Let's Encrypt для домена и отдаёт сайт по https. Web проксирует `/api/*` в api и `/media/*` в s3.

```
:443 caddy ──► web (Nuxt) ──/api/**──► api (FastAPI) ──► db (Postgres + pgvector)
                          └─/media/**─► s3 (SeaweedFS)        └──► GigaChat API
```

Нужен только Docker с compose v2 и ~6 ГБ места (образ api с torch ~2 ГБ + модель).

### 1. Код и секреты

```bash
git clone <url-репозитория> ~/nit && cd ~/nit
cp .env.prod.example .env.prod
chmod 600 .env.prod
```

Заполни `.env.prod`:

| Переменная | Что это |
|---|---|
| `POSTGRES_PASSWORD` | пароль базы, любой: `openssl rand -hex 16` |
| `JWT_SECRET` | секрет сессий: `openssl rand -hex 32` |
| `GIGACHAT_AUTH_KEY` | ключ авторизации GigaChat API |
| `AI_MODEL` | `GigaChat-2-Max` (или `GigaChat-2-Pro`, `GigaChat-2`) |
| `SITE_DOMAIN` | домен сайта, например `nit.envision.press` |
| `CORS_ORIGINS` | `["https://домен"]` |
| `COOKIE_SECURE` | `true` (сайт по https) |

Перед запуском A-запись домена должна смотреть на сервер, а порты 80 и 443 быть свободны: по ним Caddy получает сертификат. Если домен за прокси Cloudflare (оранжевое облако), поставь там режим SSL «Full».

### 2. Запуск

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Первая сборка идёт 5-10 минут. Миграции api накатывает сам при старте. Модель эмбеддингов качается при первом старте api в volume `models` (пара минут), пока она грузится, поиск работает без семантики.

### 3. Демо данные (по желанию)

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec api python -m app.seed.run --reset
```

Внимание: `--reset` **сносит все данные в базе**. На живой базе не запускать.

### 4. Проверка

```bash
curl -s https://домен/api/health            # {"status":"ok"}
curl -s https://домен/api/ai/status         # {"enabled":true,"model":"GigaChat-2-Max",...}
```

Сайт: `https://домен/`, swagger: `https://домен/api/docs`. Запросы на http и на голый IP редиректятся на домен.

Контейнерам выставлены лимиты (api — 2 CPU и 3 ГБ, torch в 2 потока; web — 1 CPU), чтобы стек не забивал хост.

### Обновление

```bash
cd ~/nit && git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Данные (база, картинки, модель) лежат в docker volumes `nit-prod_db-data`, `nit-prod_s3-data`, `nit-prod_models` и переживают пересборку. `down -v` их сотрёт.

### Логи и остановка

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f api
docker compose -f docker-compose.prod.yml --env-file .env.prod down
```

## Если что-то не так

- **ИИ отвечает 503** - не задан `GIGACHAT_AUTH_KEY`. **502** - GigaChat не ответил или вернул кривой JSON, кнопку можно нажать ещё раз.
- **Эмбеддинги GigaChat** (`Embeddings`, `EmbeddingsGigaR`) на бесплатном ключе отдают 402, поэтому семантика на локальной RoSBERTa.
- **api падает с `Illegal instruction`** - старый процессор без SSE4.2 (например, AMD Phenom II). numpy поэтому закреплён на 1.26 (`numpy<2`), а эмбеддинги считаются через transformers напрямую, без sentence-transformers (он тянет scipy под numpy 2). Не обновляй numpy до 2.x, если прод на таком железе.
- **Сервер слабый по памяти** - модель эмбеддингов занимает ~1.6 ГБ RAM. Если не влезает, ставь `EMBEDDINGS_ENABLED=false`.
- **Сертификат Сбера** - GigaChat подписан корневым сертификатом Минцифры, он лежит в `backend/app/certs/` и подключается в коде, ставить его в систему не нужно.
- **Вход не держится** - сайт открыт по http, а стоит `COOKIE_SECURE=true`.
- **`make test` падает** - тестам нужна база `nit_test`, её создаёт init скрипт compose при первом запуске. Если volume старый: `docker compose down -v && make up` (сотрёт данные).
- **Офлайн режим (PWA)** работает только по https или на localhost.
