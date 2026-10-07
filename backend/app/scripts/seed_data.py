"""Seed script to populate standard Indian heritage sites and architectural regions in Postgres."""

import uuid
from app.database import SessionLocal
from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState


def seed():
    db = SessionLocal()
    sites = [
        {
            "name": "Shore Temple, Mahabalipuram",
            "location_name": "Mahabalipuram, Tamil Nadu",
            "latitude": 12.6167,
            "longitude": 80.1983,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "regions": [
                {"name": "East-Facing Rajasimhesvara Vimana", "category": "vimana"},
                {"name": "Southern Adhisthana Plinth", "category": "facade"},
                {"name": "Western Small Shrine Mandapa", "category": "mandapa"},
                {"name": "North Enclosure Carved Relief", "category": "relief"},
            ],
        },
        {
            "name": "Brihadisvara Temple, Thanjavur",
            "location_name": "Thanjavur, Tamil Nadu",
            "latitude": 10.7828,
            "longitude": 79.1318,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "regions": [
                {"name": "Main 13-Tiered Vimana Tower", "category": "vimana"},
                {"name": "Nandi Mandapa Monolith", "category": "mandapa"},
                {"name": "Eastern Gopuram Gateway", "category": "facade"},
            ],
        },
        {
            "name": "Hampi Heritage Complex",
            "location_name": "Hampi, Karnataka",
            "latitude": 15.3350,
            "longitude": 76.4600,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "regions": [
                {"name": "Vittala Temple Stone Chariot", "category": "sculpture"},
                {"name": "Musical Pillars Mandapa", "category": "pillar"},
                {"name": "Virupaksha Temple Gopuram", "category": "facade"},
            ],
        },
        {
            "name": "Konark Sun Temple",
            "location_name": "Konark, Odisha",
            "latitude": 19.8876,
            "longitude": 86.0945,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "regions": [
                {"name": "Jagamohana Pyramidal Roof Steps", "category": "roof"},
                {"name": "South Carved Stone Wheel", "category": "relief"},
                {"name": "Natamandira Dance Hall Pillars", "category": "pillar"},
            ],
        },
    ]

    for s in sites:
        short_name = s["name"].split(",")[0]
        existing = db.query(Monument).filter(Monument.name.ilike(f"%{short_name}%")).first()
        if not existing:
            m = Monument(
                id=uuid.uuid4(),
                name=s["name"],
                location_name=s["location_name"],
                latitude=s["latitude"],
                longitude=s["longitude"],
                heritage_status=s["heritage_status"],
                importance_tier=s["importance_tier"],
            )
            db.add(m)
            db.commit()
            db.refresh(m)
            print(f"Created Monument: {m.name} ({m.id})")
            mon_id = m.id
        else:
            mon_id = existing.id
            print(f"Existing Monument: {existing.name} ({existing.id})")

        for r in s["regions"]:
            reg_name_prefix = r["name"][:12]
            reg_existing = (
                db.query(Region)
                .filter(Region.monument_id == mon_id, Region.name.ilike(f"%{reg_name_prefix}%"))
                .first()
            )
            if not reg_existing:
                reg = Region(
                    id=uuid.uuid4(),
                    monument_id=mon_id,
                    name=r["name"],
                    category=r["category"],
                )
                db.add(reg)
                db.commit()
                db.refresh(reg)

                # Create initial consensus state v1 with health 1.0
                cs = ConsensusState(
                    id=uuid.uuid4(),
                    region_id=reg.id,
                    version=1,
                    observation_count=0,
                    structural_health_index=1.0,
                )
                db.add(cs)
                db.commit()
                print(f"  Created Region: {reg.name} ({reg.id})")

    db.close()


if __name__ == "__main__":
    seed()
