# Inventory API
![CI](https://github.com/stevencardenas615/inventory-api/actions/workflows/ci.yml/badge.svg)

A REST API for tracking products bought in bulk through manifests, from intake through sale. The idea comes from buying liquidation pallets: each pallet arrives with a manifest listing every product in it (item name, barcode, quantity, retail price), and the business needs to track what came in, what sold for how much, and what's still on the shelf. Each row in `products` is one physical unit, so a case of 12 blenders is 12 rows that sell one at a time.

**Live:** https://api.scardenas.tech/docs. The API is deployed (see [Deployment](#deployment)). Registration is closed on the live server, so the docs can be read there but every route except `/health` needs a token.

## Stack

FastAPI · PostgreSQL 16 (raw SQL via psycopg 3) · JWT auth (PyJWT, Argon2 via pwdlib) · pytest · uv · Docker · GitHub Actions · Traefik

## Running locally

Needs [uv](https://docs.astral.sh/uv/) and Docker.

1. Clone the repo and run `uv sync`.
2. `cp .env.example .env`. The example values match the local database in the next step.
3. `docker compose -f compose.dev.yml up -d --wait` starts Postgres 16 with two databases, `inventory` and `inventory_test`, and loads `schema.sql` into both.
4. `uv run fastapi dev app/main.py`, then open http://127.0.0.1:8000/docs.
5. Registration is closed by default. To create the first user, set `ALLOW_REGISTRATION=true` in `.env`, restart, register through `/docs`, then set it back to `false`.

To use your own Postgres instead of the Docker one: create both databases, load `schema.sql` into each, and put their URLs in `.env`. If that Postgres is on a remote server, open a tunnel first: `ssh -L 5432:localhost:5432 <server>`.

## Tests

Tests run against a separate database (`inventory_test`, same schema) over the real code paths, not mocks. The fixture empties the tables before and after every test, and it refuses to run unless the test database's name ends in `_test`, so a wrong URL can't wipe real data. The tests open registration themselves, so they don't depend on what `.env` says.

```bash
uv run pytest --cov=app --cov-report=term-missing
```

CI runs the same steps as "Running locally" on every pull request and prints the coverage table, and a second job builds the Docker image.

One test fires two sales of the same product at the same moment from two threads and checks that exactly one gets 200 and the other 409. That is the claim under "Selling is its own endpoint" below, tested instead of assumed.

## A short session

Real requests and responses from a test run, with the `Authorization: Bearer <token>` header left out. Money goes in and comes back as strings.

```text
POST /manifests  {"purchase_date": "2026-10-01", "cost": "500.00"}
200  {"purchase_date": "2026-10-01", "cost": "500.00", "manifest_id": 1, "entered_by": 1}

POST /products  {"manifest_id": 1, "barcode": "0123456789012", "product_name": "Blender",
                 "retail_price": "49.99", "list_price": "29.99", "status": "available"}
200  {"manifest_id": 1, "barcode": "0123456789012", "product_name": "Blender", "retail_price": "49.99",
      "list_price": "29.99", "product_id": 1, "status": "available", "sold_price": null, "sold_at": null}

POST /products/1/sell  {"sold_price": "27.50"}
200  {..., "product_id": 1, "status": "sold", "sold_price": "27.50", "sold_at": "2026-11-20T08:30:53.274499Z"}

POST /products/1/sell  {"sold_price": "27.50"}          the same product again
409  {"detail": "Product is sold, only available products can be sold"}

POST /products  {..., "product_name": "Toaster", "list_price": "-5"}
422  {"detail": [{"type": "greater_than_equal", "loc": ["body", "list_price"],
                  "msg": "Input should be greater than or equal to 0", "input": "-5", "ctx": {"ge": 0}}]}

GET /manifests/1/summary
200  {"manifest_id": 1, "cost": "500.00", "items": 1, "sold": 1, "available": 0, "not_available": 0,
      "revenue": "27.50", "profit": "-472.50"}
```

## Endpoints

| Method | Path | Auth |
|---|---|---|
| GET | `/health` | no |
| POST | `/auth/register` | no, but returns 403 unless `ALLOW_REGISTRATION=true` |
| POST | `/auth/token` | no |
| GET | `/auth/me` | yes |
| POST, GET | `/manifests` | yes |
| GET | `/manifests/{id}` | yes |
| GET | `/manifests/{id}/products` | yes |
| GET | `/manifests/{id}/summary` | yes |
| POST, GET | `/products` (`?status=` filter on GET) | yes |
| GET, PATCH, DELETE | `/products/{id}` | yes |
| POST | `/products/{id}/sell` | yes |

Full request and response shapes are in `/docs`. Bad input (negative money, more digits than `NUMERIC(10,2)` holds, empty names, a password under 8 characters) is rejected with 422 before it reaches the database.

## Design decisions

**Raw SQL instead of an ORM.** I chose raw SQL because I wanted to learn SQL itself and see every query the app runs. An ORM would have hidden the thing I was trying to learn, and the app is small enough that the queries stay readable. Values always go through `%s` placeholders, and the one place column names are dynamic (PATCH) uses `psycopg.sql.Identifier`, so nothing from a request is ever pasted into SQL text. SQLAlchemy is on the list for later.

**Soft delete.** Deleting a product sets `status = 'deleted'` instead of removing the row, so no product's history is ever lost. `GET /products` hides deleted rows because day to day you want what's actually in stock; `GET /products/{id}` still returns them so "what happened to item 12?" has an answer. Sold products can't be deleted at all (409), because they're sales records. `DELETE` is the only way in: create and PATCH don't accept `deleted`, and a deleted product can't be edited back to life.

**Selling is its own endpoint.** Selling sets three things at once: status becomes sold, sold_price is recorded, and sold_at is stamped by the database. The availability check is inside the UPDATE itself (WHERE ... AND status = 'available'), so two people can’t sell the same item at the same time: the database only changes the row if it’s still available, in one step. EditableStatus leaves sold out of create and PATCH, so the only way a product can become sold is through this endpoint, which means a sold product always has a price and a time. Selling an already-sold product returns 409, because the request is valid but the product’s current state conflicts with it.

**Everything requires a token except health, register, and token.** Health has to work for monitoring, and nobody can log in without token. Register has no token check either, but it is closed behind `ALLOW_REGISTRATION`, which defaults to off: the API is on the public internet, there are no roles yet, and an open register route would let anyone create an account with full access. I open it to create a user and close it again. Everything else is locked for two reasons: least privilege (nobody can change inventory without being a known user), and the start of an audit trail (`entered_by` on a manifest comes from the token, not the request body, so a client can't claim to be someone else).

**`ProductBase` / `ProductCreate` / `Product`.** `ProductCreate` is what a client is allowed to send: no id, no sold fields, only editable statuses. `Product` is what the server returns: everything, including the id Postgres generated and any status, including `sold`. `ProductBase` holds the fields they share. Create accepts less than the response returns because clients shouldn't be able to set things the server owns.

**Money.** Prices are NUMERIC(10,2) in Postgres and Decimal in Python, never float. Floats are approximations for example: 0.1 + 0.2 gives 0.30000000000000004, which is how money ends up off by a cent. JSON numbers are floats too, so the API returns prices as strings like "150.00" to keep the exact digits all the way to the client.

**The manifest summary is one query.** `GET /manifests/{id}/summary` answers the question the project started from: did this pallet pay for itself? It returns the cost, the revenue so far, the difference, and counts by status. Postgres does the adding with `count(*) FILTER (...)` and `sum()` over a `LEFT JOIN`, so a manifest with no products yet still returns a row of zeros instead of a 404.

## Deployment

The API runs on a VPS at https://api.scardenas.tech.

- **Container.** `Dockerfile` builds the image with uv from the lockfile, dependencies first so that layer is cached until they change. `compose.yml` runs it; secrets come from the server's `.env`, never the image.
- **HTTPS.** Traefik was already running on the server, so the API registers with it through the labels in `compose.yml` and Traefik gets the Let's Encrypt certificate. That replaced my first plan of nginx and a systemd service.
- **Database.** Postgres 16 runs on the same server, outside Docker. The container uses host networking so `localhost` in `DATABASE_URL` reaches it.
- **Releasing.** By hand for now: pull on the server, `docker compose up -d --build`, then check `/health` and the version at `/`.

## Known gaps

- No roles yet: every user can do everything. The next step is a `role` column and a `require_admin` dependency on top of `get_current_user`.
- Products have no `created_by` or `sold_by`, so the audit trail only covers manifests.
- No rate limiting, and login takes less time for a username that doesn't exist than for a wrong password.
- Tokens last 30 minutes with no refresh and no way to revoke one.
- One database connection per request, no pool.
- No migrations: `schema.sql` is loaded once, and a schema change on the server is done by hand.
- List routes return every row; there is no paging yet.

## Roadmap

- Roles and permissions
- Deploy from CI when main is green, instead of by hand
- Migrations
- Paging on the list routes
