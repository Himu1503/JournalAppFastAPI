# Bloging API

Small FastAPI project for users and journal entries, with JWT authentication.

## Features

- User signup and login
- JWT-based auth (`Bearer` token)
- Create and fetch journal entries per user
- Basic pytest test suite
- Request/event logging

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- PyJWT
- pytest
- uv

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Start PostgreSQL (for example with Docker Compose):

```bash
docker compose up -d
```

3. Run the API:

```bash
uv run fastapi dev
```

App will run on `http://127.0.0.1:8000`.

## Environment Variables

Create a `.env` file (or export variables in your shell):

```env
JWT_SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bloging_db
```

Notes:
- `JWT_SECRET_KEY` should be long and random in production.
- Current `database.py` uses a hardcoded DB URL; if you want, we can wire it to read `DATABASE_URL` from env directly.

## Auth Flow

1. Create user: `POST /user`
2. Login: `POST /auth/login`
3. Copy `access_token` and send header:

```text
Authorization: Bearer <token>
```

4. Create journal entry:
   - `POST /journal/{user_id}`

## Useful Endpoints

- `GET /` health check
- `POST /user` create user
- `POST /auth/login` login and get token
- `GET /user/{id}` get user (auth required)
- `POST /journal/{user_id}` create journal (auth required)
- `GET /journal?user_id=<id>` list journals (auth required)
- `GET /journal/{id}` get one journal (auth required)

## Run Tests

```bash
uv run pytest -q
```
