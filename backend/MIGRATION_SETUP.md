# ============================================================
#  MIGRATION SETUP INSTRUCTIONS
#  Run these commands once you have your Supabase DATABASE_URL.
# ============================================================

# Step 1 — Create backend/.env (copy from .env.example and fill in values)
# Generate a strong secret key with:
#   python3 -c "import secrets; print(secrets.token_hex(32))"

DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
SECRET_KEY=REPLACE_WITH_GENERATED_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================================
# Step 2 — Run the Alembic migration
# ============================================================
#
#   cd backend
#   source venv/bin/activate
#   alembic revision --autogenerate -m "create_users_table"
#   alembic upgrade head
#
# This creates the `users` table in your Supabase database.
# ============================================================
