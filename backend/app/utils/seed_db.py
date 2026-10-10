"""Database seeding utility to populate initial heritage monuments and architectural regions."""

import uuid
from app.database import SessionLocal
from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState


def seed_database():
    db = SessionLocal()
    try:
        existing_count = db.query(Monument).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} monuments. Skipping seed.")
            return

        print("Seeding initial heritage monuments and regions into Postgres...")

        # 1. Ajanta Rock-Cut Caves
        ajanta = Monument(
            name="Ajanta Rock-Cut Caves",
            location_name="Aurangabad, Maharashtra",
            latitude=20.5519,
            longitude=75.7033,
            heritage_status="UNESCO World Heritage Site",
            importance_tier=1,
            image_url="/monuments/ajanta_caves.jpg",
        )
        db.add(ajanta)
        db.flush()

        ajanta_regions = [
            Region(
                monument_id=ajanta.id,
                name="Cave 19 Chaitya Hall Facade",
                category="facade",
                image_url="/monuments/ajanta_cave19_chaitya.jpg",
                bounding_box={"x": 100, "y": 150, "width": 450, "height": 320},
            ),
            Region(
                monument_id=ajanta.id,
                name="Cave 26 Stupa Rock Carving",
                category="sculpture",
                image_url="/monuments/ajanta_cave26_stupa.jpg",
                bounding_box={"x": 180, "y": 120, "width": 380, "height": 280},
            ),
            Region(
                monument_id=ajanta.id,
                name="Cave 1 Pillared Monastic Verandah",
                category="pillar",
                image_url="/monuments/ajanta_cave1_verandah.jpg",
                bounding_box={"x": 80, "y": 200, "width": 500, "height": 260},
            ),
            Region(
                monument_id=ajanta.id,
                name="Cave 2 Painted Sanctuary Ceiling",
                category="relief",
                image_url="/monuments/ajanta_cave2_paintings.jpg",
                bounding_box={"x": 140, "y": 80, "width": 420, "height": 300},
            ),
        ]
        db.add_all(ajanta_regions)
        db.flush()

        for reg in ajanta_regions:
            cs = ConsensusState(
                region_id=reg.id,
                version=1,
                cumulative_reliability=0.92,
                observation_count=3,
                structural_health_index=0.90,
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
            image_url="/monuments/brihadisvara_temple.jpg",
        )
        db.add(brihadisvara)
        db.flush()

        bt_regions = [
            Region(
                monument_id=brihadisvara.id,
                name="Main 13-Tiered Vimana Tower",
                category="vimana",
                image_url="/monuments/brihadisvara_vimana.jpg",
                bounding_box={"x": 150, "y": 60, "width": 400, "height": 450},
            ),
            Region(
                monument_id=brihadisvara.id,
                name="Nandi Mandapa Monolith",
                category="mandapa",
                image_url="/monuments/brihadisvara_nandi_mandapa.jpg",
                bounding_box={"x": 120, "y": 280, "width": 320, "height": 240},
            ),
            Region(
                monument_id=brihadisvara.id,
                name="Eastern Gopuram Gateway",
                category="facade",
                image_url="/monuments/brihadisvara_gopuram.jpg",
                bounding_box={"x": 200, "y": 100, "width": 360, "height": 380},
            ),
            Region(
                monument_id=brihadisvara.id,
                name="Southern Adhisthana Granite Inscriptions",
                category="relief",
                image_url="/monuments/brihadisvara_inscriptions.jpg",
                bounding_box={"x": 90, "y": 380, "width": 520, "height": 180},
            ),
        ]
        db.add_all(bt_regions)
        db.flush()

        for reg in bt_regions:
            cs = ConsensusState(
                region_id=reg.id,
                version=1,
                cumulative_reliability=0.95,
                observation_count=4,
                structural_health_index=0.88,
            )
            db.add(cs)

        # 3. Hampi Heritage Complex
        hampi = Monument(
            name="Hampi Heritage Complex",
            location_name="Hampi, Karnataka",
            latitude=15.3350,
            longitude=76.4600,
            heritage_status="UNESCO World Heritage Site",
            importance_tier=1,
            image_url="/monuments/hampi_complex.jpg",
        )
        db.add(hampi)
        db.flush()

        hampi_regions = [
            Region(
                monument_id=hampi.id,
                name="Vittala Temple Stone Chariot",
                category="sculpture",
                image_url="/monuments/hampi_stone_chariot.jpg",
                bounding_box={"x": 140, "y": 180, "width": 420, "height": 340},
            ),
            Region(
                monument_id=hampi.id,
                name="Musical Pillars Mandapa",
                category="pillar",
                image_url="/monuments/hampi_musical_pillars.jpg",
                bounding_box={"x": 100, "y": 120, "width": 460, "height": 300},
            ),
            Region(
                monument_id=hampi.id,
                name="Virupaksha Temple Gopuram",
                category="facade",
                image_url="/monuments/hampi_virupaksha_gopuram.jpg",
                bounding_box={"x": 180, "y": 50, "width": 350, "height": 450},
            ),
            Region(
                monument_id=hampi.id,
                name="Mahanavami Dibba Carved Frieze",
                category="relief",
                image_url="/monuments/hampi_mahanavami_dibba.jpg",
                bounding_box={"x": 60, "y": 240, "width": 540, "height": 220},
            ),
            Region(
                monument_id=hampi.id,
                name="Lotus Mahal Royal Pavilion",
                category="facade",
                image_url="/monuments/hampi_lotus_mahal.jpg",
                bounding_box={"x": 120, "y": 100, "width": 440, "height": 360},
            ),
        ]
        db.add_all(hampi_regions)
        db.flush()

        for reg in hampi_regions:
            cs = ConsensusState(
                region_id=reg.id,
                version=1,
                cumulative_reliability=0.89,
                observation_count=2,
                structural_health_index=0.85,
            )
            db.add(cs)

        db.commit()
        print("Database seeded successfully with the 3 heritage monuments and regions!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
