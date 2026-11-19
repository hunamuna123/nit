# Как развернуть «Нить»

Два варианта: локально (за 5 минут, для проверки и демо) и на сервере (VPS с доменом).

## Что нужно

- Docker с compose v2
- Node 22 или 24 + pnpm (`corepack enable`)
- Python 3.12 + [uv](https://docs.astral.sh/uv/)
- make, git

Порты: фронт 3000, бэк 8000, Postgres 5434, S3 9010. Postgres специально не на 5432, чтобы не конфликтовать с локальным.

## Локально

```bash
git clone <url-репозитория> nit && cd nit
cp backend/.env.example backend/.env   # можно пропустить, дефолты рабочие
make setup                             # зависимости, docker compose, миграции, демо данные
make dev                               # фронт :3000 + бэк :8000
```

- сайт: http://localhost:3000
- swagger: http://localhost:8000/api/docs
- вход: `demo@nit.demo` / `demo1234` (ещё `igor.vlasov@nit.demo` эксперт и `admin@nit.demo` админ, пароль тот же)

ИИ: впиши `OPENROUTER_API_KEY` в `backend/.env`. Без ключа всё работает, кроме ИИ кнопок. `AI_FAKE=true` включает заглушку без сети.

Остановить инфраструктуру: `make down` (данные остаются в docker volumes).

## На сервере

Схема на одной машине: наружу торчит только nginx, он ходит в Nuxt (:3000), а Nuxt сам проксирует `/api/*` в FastAPI (:8000) и `/media/*` в S3 (:9010). Postgres и S3 слушают только 127.0.0.1.

```
nginx :443 ──► Nuxt :3000 ──/api/**──► FastAPI :8000 ──► Postgres :5434
                          └─/media/**─► S3 (SeaweedFS) :9010
```

### 1. Код и зависимости

```bash
git clone <url-репозитория> /opt/nit && cd /opt/nit
make install
```

### 2. Postgres и S3

```bash
make up      # docker compose up -d --wait
```

Логины в `docker-compose.yml` (`nit` / `nit`) и ключи S3 в `backend/docker/seaweedfs/s3.json` дефолтные. Наружу они не открыты, но для прода лучше поменять и прописать те же значения в `backend/.env`.

### 3. backend/.env

```bash
cp backend/.env.example backend/.env
```

Что поменять:

| Переменная | Значение |
|---|---|
| `DEBUG` | `false` |
| `JWT_SECRET` | случайная строка: `openssl rand -hex 32` |
| `COOKIE_SECURE` | `true` (если сайт на https) |
| `CORS_ORIGINS` | `["https://твой-домен"]` |
| `DATABASE_URL` | если менял пароль Postgres |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | если менял ключи S3 |
| `OPENROUTER_API_KEY` | ключ OpenRouter, иначе ИИ выключен |

### 4. Миграции и данные

```bash
make migrate
make seed     # только если нужны демо данные
```

Внимание: `make seed` запускается с `--reset` и **сносит все данные в базе**. На живой базе не запускать.

### 5. Сборка фронта

```bash
make build    # результат в frontend/.output
```

Адреса прокси (`NUXT_API_PROXY_TARGET`, `NUXT_MEDIA_PROXY_TARGET`) вшиваются в сборку, их надо задавать при `make build`, а не при запуске. Дефолты `http://localhost:8000` и `http://localhost:9010/nit-media` подходят, если всё на одной машине.

### 6. systemd

`/etc/systemd/system/nit-api.service`:

```ini
[Unit]
Description=nit api
After=network.target docker.service

[Service]
WorkingDirectory=/opt/nit/backend
ExecStart=/usr/local/bin/uv run fastapi run --host 127.0.0.1 --port 8000
Restart=always
User=nit

[Install]
WantedBy=multi-user.target
```

`WorkingDirectory` важен: `.env` читается из текущей папки.

`/etc/systemd/system/nit-web.service`:

```ini
[Unit]
Description=nit web
After=network.target nit-api.service

[Service]
WorkingDirectory=/opt/nit/frontend
Environment=PORT=3000
Environment=HOST=127.0.0.1
ExecStart=/usr/bin/node .output/server/index.mjs
Restart=always
User=nit

[Install]
WantedBy=multi-user.target
```

Пути к `uv` и `node` проверь через `which uv` / `which node`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nit-api nit-web
```

### 7. nginx + https

```nginx
server {
    server_name твой-домен;
    client_max_body_size 10m;   # картинки шагов до 8 МБ

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo certbot --nginx -d твой-домен
```

### 8. Проверка

```bash
curl -s http://127.0.0.1:8000/api/health        # {"status":"ok"}
curl -s https://твой-домен/api/health           # то же самое через nuxt
```

Офлайн режим (PWA) работает только в прод сборке и только по https.

## Обновление

```bash
cd /opt/nit && git pull
make install
make migrate
make build
sudo systemctl restart nit-api nit-web
```

## Если что-то не так

- **Бэк не стартует, ругается на базу** - не поднят docker: `make up`, проверить `docker compose ps`.
- **Картинки шагов не грузятся** - не жив S3 на :9010. API при этом стартует, но загрузка падает.
- **Вход не держится** - сайт открыт по http, а стоит `COOKIE_SECURE=true`: браузер такую куку не сохранит.
- **`make test` падает** - тестам нужна база `nit_test`, её создаёт init скрипт compose при первом запуске. Если volume старый: `docker compose down -v && make up` (сотрёт данные).
- **Стили не применились после правки в dev** - `touch frontend/app/assets/css/main.css`.
