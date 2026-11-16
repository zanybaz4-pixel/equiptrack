"""Create explicitly requested synthetic accounts with generated passwords."""
import os
from secrets import token_urlsafe

from sqlalchemy import create_engine, text

from app.security import hasher

DEMO_ACCOUNTS = (
    ("custodian@example.invalid", "Demo Custodian", "admin", None),
    ("student@example.invalid", "Demo Student", "borrower", "student"),
    ("faculty@example.invalid", "Demo Faculty", "borrower", "faculty"),
)


def main():
    url = os.environ.get("MIGRATION_DATABASE_URL")
    if not url:
        raise SystemExit("Set MIGRATION_DATABASE_URL before provisioning demonstration accounts.")
    engine = create_engine(url, hide_parameters=True)
    created = []
    with engine.begin() as db:
        for email, name, role, kind in DEMO_ACCOUNTS:
            password = token_urlsafe(18)
            result = db.execute(text("""INSERT INTO users
                (email, full_name, password_hash, role, borrower_type)
                VALUES (:email, :name, :password_hash, :role, :kind)
                ON CONFLICT (email) DO NOTHING RETURNING id"""),
                {"email": email, "name": name, "password_hash": hasher.hash(password),
                 "role": role, "kind": kind})
            if result.scalar_one_or_none() is not None:
                created.append((email, password))
    for email, password in created:
        print(f"{email}  {password}")
    if not created:
        print("Demo accounts already exist. Existing passwords were preserved.")


if __name__ == "__main__":
    main()
