import os
from decimal import Decimal

from sqlalchemy import select
from dotenv import load_dotenv
from app.core.enum import UserRole
from app.core.pshashing import hash_password
from app.database.db import SessionLocal
from app.models.dentists_model import Dentist
from app.models.treatments_model import Treatment
from app.models.users import User

load_dotenv()
DENTISTS = [
    {
        "name": "Dr. Maya Patel",
        "age": 38,
        "gender": "female",
        "email": "maya.patel@gmail.com",
        "phone": "555-0101",
        "address": "12 Main Street",
        "specialization": "Orthodontics",
        "qualification": "DDS, MS Orthodontics",
        "experience_years": 10,
        "bio": "Specializes in orthodontic care.",
    },
    {
        "name": "Dr. Arun Kumar",
        "age": 42,
        "gender": "male",
        "email": "arun.kumar@gmail.com",
        "phone": "555-0102",
        "address": "24 Oak Avenue",
        "specialization": "Endodontics",
        "qualification": "BDS, MDS Endodontics",
        "experience_years": 14,
        "bio": "Focuses on root canal treatment.",
    },
]

TREATMENTS = [
    {
        "name": "Dental Cleaning",
        "description": "Routine cleaning and polishing.",
        "duration_minutes": 45,
        "fee": Decimal("75.00"),
    },
    {
        "name": "Dental Filling",
        "description": "Tooth restoration using a filling.",
        "duration_minutes": 60,
        "fee": Decimal("150.00"),
    },
    {
        "name": "Root Canal",
        "description": "Endodontic treatment for an infected tooth.",
        "duration_minutes": 90,
        "fee": Decimal("650.00"),
    },
]


def main() -> None:
    dentist_password = os.getenv("DENTISTPASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    missing = [
        name
        for name, value in (
            ("DENTISTPASSWORD", dentist_password),
            ("ADMIN_EMAIL", admin_email),
            ("ADMIN_PASSWORD", admin_password),
        )
        if not value
    ]
    if missing:
        raise SystemExit(f"Set required environment variables: {', '.join(missing)}")

    dentists_created = 0
    dentists_skipped = 0
    treatments_created = 0
    treatments_skipped = 0
    admin_created = False

    with SessionLocal.begin() as db:
        # Create dentist login accounts and profiles.
        for dentist_data in DENTISTS:
            existing_user = db.scalar(
                select(User).where(User.email == dentist_data["email"])
            )
            if existing_user:
                print(f"Skipped existing dentist email: {dentist_data['email']}")
                dentists_skipped += 1
                continue

            user = User(
                name=dentist_data["name"],
                age=dentist_data["age"],
                gender=dentist_data["gender"],
                email=dentist_data["email"],
                phone=dentist_data["phone"],
                password_hash=hash_password(dentist_password),
                role=UserRole.DENTIST.value,
            )
            db.add(user)
            db.flush()

            profile_fields = {
                key: value
                for key, value in dentist_data.items()
                if key not in {"name", "age", "gender", "email", "phone"}
            }
            db.add(Dentist(user_id=user.id, **profile_fields))
            dentists_created += 1

        # Create treatment catalog entries.
        for treatment_data in TREATMENTS:
            existing_treatment = db.scalar(
                select(Treatment).where(Treatment.name == treatment_data["name"])
            )
            if existing_treatment:
                print(f"Skipped existing treatment: {treatment_data['name']}")
                treatments_skipped += 1
                continue

            db.add(Treatment(**treatment_data))
            treatments_created += 1

        # Create the admin login account.
        existing_admin = db.scalar(
            select(User).where(User.email == admin_email)
        )
        if existing_admin:
            print(f"Skipped existing admin email: {admin_email}")
        else:
            db.add(
                User(
                    name=os.getenv("ADMIN_NAME", "Dental Admin"),
                    age=30,
                    gender="male",
                    email=admin_email,
                    phone=None,
                    password_hash=hash_password(admin_password),
                    role=UserRole.ADMIN.value,
                )
            )
            admin_created = True

    print(
        "Seed complete: "
        f"dentists {dentists_created} created/{dentists_skipped} skipped; "
        f"treatments {treatments_created} created/{treatments_skipped} skipped; "
        f"admin {'created' if admin_created else 'skipped'}."
    )


if __name__ == "__main__":
    main()