# elchemist-api

Local Setup Guide

Repo: https://github.com/danielclamor/elchemist-api

Requirements:
- Python
- Docker

## 1. Clone the repo

```bash
git clone https://github.com/danielclamor/elchemist-api.git
cd elchemist-api
```

## 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

## 3. Install dependencies

If `requirements.txt` has been fixed and pushed:

```bash
pip install -r requirements.txt
```

If not, install the real dependencies directly:

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic python-dotenv strawberry-graphql
```

Then regenerate the file so it matches what's actually installed:

```bash
pip freeze > requirements.txt
```

## 4. Configure your `.env`

Make a `.env` file and copy contents from `.env.example`. Change the values of the variables.

## 5. Create a PostgreSQL Docker container

Make sure to create a `.env` file and fill out necessary variables and values. Run these commands in your terminal:

```bash
docker compose up -d
docker compose ps
docker compose logs db
docker compose exec db psql -U <user> -d elchemist_db
```

## 6. Grant user privileges

```sql
GRANT ALL PRIVILEGES ON DATABASE elchemist_db TO <user>;
```

If you hit permission errors later when Alembic tries to create tables, also run this while connected to the new database:

```sql
GRANT ALL ON SCHEMA public TO <user>;
```

## 7. Run the migrations

```bash
alembic upgrade head
```

This builds the schema inside the empty database using the migration scripts in `alembic/versions/`.

## 8. Start the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Check the GraphQL endpoint (commonly `/graphql` with Strawberry + FastAPI) in your browser to confirm it's serving.

## Troubleshooting

- **`ModuleNotFoundError`** → dependencies from Step 3 aren't fully installed.
- **`password authentication failed`** → check the `DATABASE_URL` value from `.env`.
- **`permission denied for schema public`** → run the `GRANT ALL ON SCHEMA public` command from Step 6.
- **Alembic can't find `DATABASE_URL`** → check that `alembic/env.py` calls `load_dotenv()` / reads `os.getenv`; otherwise set `sqlalchemy.url` directly in `alembic.ini`.
