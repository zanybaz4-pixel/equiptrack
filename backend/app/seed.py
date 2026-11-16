"""Explicit, idempotent synthetic catalog seed. No real people or default logins."""
import os

from sqlalchemy import create_engine, text

CATEGORIES = [
    ("Presentation", "Equipment for classroom talks and school presentations."),
    ("Computing", "Portable computing equipment for supervised academic use."),
    ("Audio & Video", "Recording, documentation, and sound equipment."),
    ("Laboratory", "Equipment for supervised science activities."),
]
ITEMS = [
    ("ET-PJ-001", "Classroom projector", "Presentation", "HD projector with HDMI cable and carry case.", "Resource Center · Shelf A", "good", "serviceable"),
    ("ET-PJ-002", "Portable projection screen", "Presentation", "Tripod-mounted screen for indoor presentations.", "Resource Center · Shelf A", "good", "serviceable"),
    ("ET-LT-001", "Student laptop", "Computing", "14-inch laptop with charger and protective sleeve.", "ICT Room · Cabinet 1", "good", "serviceable"),
    ("ET-LT-002", "Faculty laptop", "Computing", "15-inch laptop for classroom instruction.", "ICT Room · Cabinet 1", "fair", "serviceable"),
    ("ET-CM-001", "Digital camera", "Audio & Video", "Camera kit with battery, memory card, and strap.", "Resource Center · Shelf B", "good", "serviceable"),
    ("ET-MC-001", "Wireless microphone kit", "Audio & Video", "Two microphones with receiver and carrying case.", "Resource Center · Shelf B", "good", "serviceable"),
    ("ET-SP-001", "Portable speaker", "Audio & Video", "Rechargeable speaker for small indoor activities.", "Resource Center · Shelf B", "damaged", "maintenance"),
    ("ET-MS-001", "Compound microscope", "Laboratory", "Teaching microscope with cover and slide holder.", "Science Lab · Cabinet 2", "good", "serviceable"),
]


def main():
    url = os.environ.get("MIGRATION_DATABASE_URL")
    if not url:
        raise SystemExit("Set MIGRATION_DATABASE_URL; seeding requires the migration owner.")
    engine = create_engine(url, hide_parameters=True)
    with engine.begin() as db:
        for name, description in CATEGORIES:
            db.execute(text("INSERT INTO equipment_categories (name, description) VALUES (:name, :description) ON CONFLICT (name) DO NOTHING"),
                       {"name": name, "description": description})
        for code, name, category, description, location, condition, status in ITEMS:
            db.execute(text("""INSERT INTO equipment_items
                (asset_code, name, category_id, description, location, condition, service_status)
                SELECT :code, :name, id, :description, :location, :condition, :status
                FROM equipment_categories WHERE name = :category
                ON CONFLICT (asset_code) DO NOTHING"""),
                       dict(code=code, name=name, category=category, description=description,
                            location=location, condition=condition, status=status))
    print("Synthetic catalog seed complete. Existing items were preserved.")


if __name__ == "__main__":
    main()
