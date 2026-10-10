"""Seed script to populate standard Indian heritage sites and architectural regions in Postgres."""

import os
import sys
import uuid

# Ensure backend root on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation
from app.models.validation import AnomalyValidation
from app.models.work_order import WorkOrder
from app.models.consensus_state import ConsensusState


def seed():
    db = SessionLocal()
    sites = [
        {
            "name": "Ajanta Rock-Cut Caves",
            "location_name": "Aurangabad, Maharashtra",
            "latitude": 20.5519,
            "longitude": 75.7033,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "/monuments/ajanta_caves.jpg",
            "regions": [
                {"name": "Cave 19 Chaitya Hall Facade", "category": "facade", "image_url": "/monuments/ajanta_cave19_chaitya.jpg"},
                {"name": "Cave 26 Stupa Rock Carving", "category": "sculpture", "image_url": "/monuments/ajanta_cave26_stupa.jpg"},
                {"name": "Cave 1 Pillared Monastic Verandah", "category": "pillar", "image_url": "/monuments/ajanta_cave1_verandah.jpg"},
                {"name": "Cave 2 Painted Sanctuary Ceiling", "category": "relief", "image_url": "/monuments/ajanta_cave2_paintings.jpg"},
            ],
        },
        {
            "name": "Brihadisvara Temple, Thanjavur",
            "location_name": "Thanjavur, Tamil Nadu",
            "latitude": 10.7828,
            "longitude": 79.1318,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "/monuments/brihadisvara_temple.jpg",
            "regions": [
                {"name": "Main 13-Tiered Vimana Tower", "category": "vimana", "image_url": "/monuments/brihadisvara_vimana.jpg"},
                {"name": "Nandi Mandapa Monolith", "category": "mandapa", "image_url": "/monuments/brihadisvara_nandi_mandapa.jpg"},
                {"name": "Eastern Gopuram Gateway", "category": "facade", "image_url": "/monuments/brihadisvara_gopuram.jpg"},
                {"name": "Southern Adhisthana Granite Inscriptions", "category": "relief", "image_url": "/monuments/brihadisvara_inscriptions.jpg"},
            ],
        },
        {
            "name": "Hampi Heritage Complex",
            "location_name": "Hampi, Karnataka",
            "latitude": 15.3350,
            "longitude": 76.4600,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "/monuments/hampi_complex.jpg",
            "regions": [
                {"name": "Vittala Temple Stone Chariot", "category": "sculpture", "image_url": "/monuments/hampi_stone_chariot.jpg"},
                {"name": "Musical Pillars Mandapa", "category": "pillar", "image_url": "/monuments/hampi_musical_pillars.jpg"},
                {"name": "Virupaksha Temple Gopuram", "category": "facade", "image_url": "/monuments/hampi_virupaksha_gopuram.jpg"},
                {"name": "Mahanavami Dibba Carved Frieze", "category": "relief", "image_url": "/monuments/hampi_mahanavami_dibba.jpg"},
                {"name": "Lotus Mahal Royal Pavilion", "category": "facade", "image_url": "/monuments/hampi_lotus_mahal.jpg"},
            ],
        },
    ]

    existing_monuments = db.query(Monument).all()
    mon_map = {m.name.split(",")[0].split(" ")[0].lower(): m for m in existing_monuments}

    for s in sites:
        short_name = s["name"].split(",")[0].split(" ")[0].lower()
        m = mon_map.get(short_name)
        if not m:
            m = Monument(
                id=uuid.uuid4(),
                name=s["name"],
                location_name=s["location_name"],
                latitude=s["latitude"],
                longitude=s["longitude"],
                heritage_status=s["heritage_status"],
                importance_tier=s["importance_tier"],
                image_url=s["image_url"],
            )
            db.add(m)
            mon_map[short_name] = m
            print(f"Adding Monument: {m.name}")
        else:
            m.name = s["name"]
            m.location_name = s["location_name"]
            m.latitude = s["latitude"]
            m.longitude = s["longitude"]
            m.image_url = s["image_url"]

    db.flush()

    existing_regions = db.query(Region).all()
    reg_map = {(r.monument_id, r.name[:12].lower()): r for r in existing_regions}

    for s in sites:
        short_name = s["name"].split(",")[0].split(" ")[0].lower()
        m = mon_map.get(short_name)
        if not m:
            continue

        for r in s["regions"]:
            reg_key = (m.id, r["name"][:12].lower())
            existing_reg = reg_map.get(reg_key)
            if not existing_reg:
                reg = Region(
                    id=uuid.uuid4(),
                    monument_id=m.id,
                    name=r["name"],
                    category=r["category"],
                    image_url=r.get("image_url"),
                )
                db.add(reg)
                reg_map[reg_key] = reg
            else:
                existing_reg.image_url = r.get("image_url")
                existing_reg.category = r.get("category")

    db.commit()
    db.close()
    print("Seed complete: Ajanta Caves, Brihadisvara Temple, and Hampi Heritage Complex with region images populated.")


if __name__ == "__main__":
    seed()
