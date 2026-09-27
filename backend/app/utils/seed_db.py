"""Database seeding utility to populate initial heritage monuments and architectural regions."""

import uuid
from app.database import SessionLocal
from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState


def seed_database():
    db = SessionLocal()
    try:
        # Check if monuments already exist
        existing_count = db.query(Monument).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} monuments. Skipping seed.")
            return

        print("Seeding initial heritage monuments and regions into Supabase...")

        # 1. Shore Temple, Mahabalipuram
        shore_temple = Monument(
            name="Shore Temple, Mahabalipuram",
            location_name="Mahabalipuram, Tamil Nadu",
            latitude=12.6163,
            longitude=80.1989,
            heritage_status="UNESCO World Heritage Site",
            importance_tier=1,
        )
        db.add(shore_temple)
        db.flush()

        st_regions = [
            Region(
                monument_id=shore_temple.id,
                name="East Vimana Plinth",
                category="foundation base",
                bounding_box={"x": 120, "y": 450, "width": 480, "height": 220},
            ),
            Region(
                monument_id=shore_temple.id,
                name="North Sanctuary Column Array",
                category="stone pillar column",
                bounding_box={"x": 200, "y": 250, "width": 300, "height": 200},
            ),
            Region(
                monument_id=shore_temple.id,
                name="Maritime Sea-Facing Wall Facade",
                category="masonry wall facade",
                bounding_box={"x": 50, "y": 180, "width": 550, "height": 320},
            ),
        ]
        db.add_all(st_regions)
        db.flush()

        # Initialize consensus states for regions
        for reg in st_regions:
            cs = ConsensusState(
                region_id=reg.id,
                version=1,
                cumulative_reliability=0.0,
                observation_count=0,
                structural_health_index=1.0,
            )
            db.add(cs)

        # 2. Brihadisvara Temple, Thanjavur
        brihadisvara = Monument(
            name="Brihadisvara Temple, Thanjavur",
            location_name="Thanjavur, Tamil Nadu",
            latitude=10.7828,
            longitude=79.1318,
            heritage_status="UNESCO World Heritage Site",
            importance_tier=1,
        )
        db.add(brihadisvara)
        db.flush()

        bt_regions = [
            Region(
                monument_id=brihadisvara.id,
                name="Vimana Tower Lower Tier",
                category="structural dome roof",
                bounding_box={"x": 150, "y": 100, "width": 400, "height": 300},
            ),
            Region(
                monument_id=brihadisvara.id,
                name="Nandi Mandapa Monolithic Column",
                category="stone pillar column",
                bounding_box={"x": 180, "y": 300, "width": 250, "height": 250},
            ),
        ]
        db.add_all(bt_regions)
        db.flush()

        for reg in bt_regions:
            cs = ConsensusState(
                region_id=reg.id,
                version=1,
                cumulative_reliability=0.0,
                observation_count=0,
                structural_health_index=1.0,
            )
            db.add(cs)

        # 3. Hampi Heritage Complex
        hampi = Monument(
            name="Hampi Heritage Complex (Stone Chariot)",
            location_name="Hampi, Karnataka",
            latitude=15.3350,
            longitude=76.4600,
            heritage_status="UNESCO World Heritage Site",
            importance_tier=1,
        )
        db.add(hampi)
        db.flush()

        hampi_regions = [
            Region(
                monument_id=hampi.id,
                name="Carved Wheel Axle & Base",
                category="carved stone sculpture",
                bounding_box={"x": 100, "y": 350, "width": 380, "height": 200},
            ),
            Region(
                monument_id=hampi.id,
                name="Chariot Canopy Frieze",
                category="decorative carved frieze",
                bounding_box={"x": 120, "y": 120, "width": 350, "height": 230},
            ),
        ]
        db.add_all(hampi_regions)
        db.flush()

        for reg in hampi_regions:
            cs = ConsensusState(
                region_id=reg.id,
                version=1,
                cumulative_reliability=0.0,
                observation_count=0,
                structural_health_index=1.0,
            )
            db.add(cs)

        db.commit()
        print("Database seeded successfully with initial monuments and architectural regions!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
