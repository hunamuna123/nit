.PHONY: install up down migrate seed setup dev dev-front dev-back lint fmt test typecheck types build

install:
	cd frontend && pnpm install
	cd backend && uv sync

# постгрес на 5434, s3 на 9010
up:
	docker compose up -d --wait

down:
	docker compose down

migrate:
	cd backend && uv run alembic upgrade head

# демо данные, вход demo@nit.demo / demo1234
seed:
	cd backend && uv run python -m app.seed.run --reset

# все с нуля
setup: install up migrate seed

dev:
	$(MAKE) -j2 dev-back dev-front

dev-front:
	cd frontend && pnpm dev

dev-back:
	cd backend && uv run fastapi dev --port 8000

# бэк должен быть запущен
types:
	cd frontend && pnpm gen:api

build:
	cd frontend && pnpm build

lint:
	cd frontend && pnpm lint
	cd backend && uv run ruff check . && uv run ruff format --check .

typecheck:
	cd frontend && pnpm typecheck
	cd backend && uv run pyright

fmt:
	cd frontend && pnpm lint:fix
	cd backend && uv run ruff format . && uv run ruff check --fix .

# нужен make up, база nit_test
test:
	cd backend && uv run pytest
