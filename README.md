# Inventory API

A REST API for tracking products bought in bulk through manifests, from intake through sale. The idea comes from buying liquidation pallets: each pallet arrives with a manifest listing every product in it (item name, barcode, quantity, retail price), and the business needs to track what came in, what sold for how much, and what's still on the shelf.

## Stack

FastAPI · PostgreSQL 16 (raw SQL via psycopg 3) · JWT auth (PyJWT, Argon2 via pwdlib) · pytest · uv

## Running locally

1. Clone the repo and run `uv sync`.
2. Copy `.env.example` to `.env` and fill in `DATABASE_URL`, `TEST_DATABASE_URL`, and `JWT_SECRET` (`openssl rand -hex 32` generates a secret).
3. Create the database and load `schema.sql` into it.
4. If Postgres is on a remote server, open a tunnel: `ssh -L 5432:localhost:5432 <server>`.
5. `uv run fastapi dev app/main.py`, then open http://127.0.0.1:8000/docs.

## Tests

Tests run against a separate database (`inventory_test`, same schema) over the real code paths, not mocks. Each test starts from empty tables and the fixture truncates them afterwards.

```bash
uv run pytest --cov=app --cov-report=term-missing
```

23 tests, 88% coverage as of Oct 17, 2026.

## Endpoints

| Method | Path | Auth |
|---|---|---|
| GET | `/health` | no |
| POST | `/auth/register` | no |
| POST | `/auth/token` | no |
| GET | `/auth/me` | yes |
| POST, GET | `/manifests` | yes |
| GET | `/manifests/{id}` | yes |
| GET | `/manifests/{id}/products` | yes |
| POST, GET | `/products` (`?status=` filter on GET) | yes |
| GET, PATCH, DELETE | `/products/{id}` | yes |
| POST | `/products/{id}/sell` | yes |

Full request and response shapes are in `/docs`.

## Design decisions

**Raw SQL instead of an ORM.** I chose raw SQL because I wanted to learn SQL itself and see every query the app runs. An ORM would have hidden the thing I was trying to learn, and the app is small enough that the queries stay readable. Values always go through `%s` placeholders, and the one place column names are dynamic (PATCH) uses `psycopg.sql.Identifier`, so nothing from a request is ever pasted into SQL text. SQLAlchemy is on the list for later.

**Soft delete.** Deleting a product sets `status = 'deleted'` instead of removing the row, so no product's history is ever lost. `GET /products` hides deleted rows because day to day you want what's actually in stock; `GET /products/{id}` still returns them so "what happened to item 12?" has an answer. Sold products can't be deleted at all (409), because they're sales records.

**Selling is its own endpoint.** Selling sets three things at once: status becomes sold, sold_price is recorded, and sold_at is stamped by the database. The availability check is inside the UPDATE itself (WHERE ... AND status = 'available'), so two people can’t sell the same item at the same time: the database only changes the row if it’s still available, in one step. EditableStatus leaves sold out of create and PATCH, so the only way a product can become sold is through this endpoint, which means a sold product always has a price and a time. Selling an already-sold product returns 409, because the request is valid but the product’s current state conflicts with it.

**Everything requires a token except health, register, and token.** Health has to work for monitoring, and nobody can log in without register and token. Everything else is locked for two reasons: least privilege (nobody can change inventory without being a known user), and the start of an audit trail (`entered_by` on a manifest comes from the token, not the request body, so a client can't claim to be someone else).

**`ProductBase` / `ProductCreate` / `Product`.** `ProductCreate` is what a client is allowed to send: no id, no sold fields, only editable statuses. `Product` is what the server returns: everything, including the id Postgres generated and any status, including `sold`. `ProductBase` holds the fields they share. Create accepts less than the response returns because clients shouldn't be able to set things the server owns.

**Money.** Prices are NUMERIC(10,2) in Postgres and Decimal in Python, never float. Floats are approximations for example: 0.1 + 0.2 gives 0.30000000000000004, which is how money ends up off by a cent. JSON numbers are floats too, so the API returns prices as strings like "150.00" to keep the exact digits all the way to the client.

## Known gaps

- No roles yet: every user can do everything. The next step is a `role` column and a `require_admin` dependency on top of `get_current_user`.
- Products have no `created_by` or `sold_by`, so the audit trail only covers manifests.
- No rate limiting.

## Roadmap

- Deploy to a VPS behind nginx (systemd service, HTTPS)
- Docker image and GitHub Actions CI (tests on every push)
- Roles and permissions