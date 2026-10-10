"""Script to retain ONLY Ajanta Rock-Cut Caves, Brihadisvara Temple, and Hampi Heritage Complex with dedicated architectural region images."""

import os
import sys
import uuid
import shutil

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


ALLOWED_MONUMENTS = [
    {
        "name": "Ajanta Rock-Cut Caves",
        "location_name": "Aurangabad, Maharashtra",
        "latitude": 20.5519,
        "longitude": 75.7033,
        "heritage_status": "UNESCO World Heritage Site",
        "importance_tier": 1,
        "image_url": "/monuments/ajanta_caves.jpg",
        "regions": [
            {
                "name": "Cave 19 Chaitya Hall Facade",
                "category": "facade",
                "image_url": "/monuments/ajanta_cave19_chaitya.jpg",
                "bounding_box": {"x": 100, "y": 150, "width": 450, "height": 320}
            },
            {
                "name": "Cave 26 Stupa Rock Carving",
                "category": "sculpture",
                "image_url": "/monuments/ajanta_cave26_stupa.jpg",
                "bounding_box": {"x": 180, "y": 120, "width": 380, "height": 280}
            },
            {
                "name": "Cave 1 Pillared Monastic Verandah",
                "category": "pillar",
                "image_url": "/monuments/ajanta_cave1_verandah.jpg",
                "bounding_box": {"x": 80, "y": 200, "width": 500, "height": 260}
            },
            {
                "name": "Cave 2 Painted Sanctuary Ceiling",
                "category": "relief",
                "image_url": "/monuments/ajanta_cave2_paintings.jpg",
                "bounding_box": {"x": 140, "y": 80, "width": 420, "height": 300}
            },
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
            {
                "name": "Main 13-Tiered Vimana Tower",
                "category": "vimana",
                "image_url": "/monuments/brihadisvara_vimana.jpg",
                "bounding_box": {"x": 150, "y": 60, "width": 400, "height": 450}
            },
            {
                "name": "Nandi Mandapa Monolith",
                "category": "mandapa",
                "image_url": "/monuments/brihadisvara_nandi_mandapa.jpg",
                "bounding_box": {"x": 120, "y": 280, "width": 320, "height": 240}
            },
            {
                "name": "Eastern Gopuram Gateway",
                "category": "facade",
                "image_url": "/monuments/brihadisvara_gopuram.jpg",
                "bounding_box": {"x": 200, "y": 100, "width": 360, "height": 380}
            },
            {
                "name": "Southern Adhisthana Granite Inscriptions",
                "category": "relief",
                "image_url": "/monuments/brihadisvara_inscriptions.jpg",
                "bounding_box": {"x": 90, "y": 380, "width": 520, "height": 180}
            },
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
            {
                "name": "Vittala Temple Stone Chariot",
                "category": "sculpture",
                "image_url": "/monuments/hampi_stone_chariot.jpg",
                "bounding_box": {"x": 140, "y": 180, "width": 420, "height": 340}
            },
            {
                "name": "Musical Pillars Mandapa",
                "category": "pillar",
                "image_url": "/monuments/hampi_musical_pillars.jpg",
                "bounding_box": {"x": 100, "y": 120, "width": 460, "height": 300}
            },
            {
                "name": "Virupaksha Temple Gopuram",
                "category": "facade",
                "image_url": "/monuments/hampi_virupaksha_gopuram.jpg",
                "bounding_box": {"x": 180, "y": 50, "width": 350, "height": 450}
            },
            {
                "name": "Mahanavami Dibba Carved Frieze",
                "category": "relief",
                "image_url": "/monuments/hampi_mahanavami_dibba.jpg",
                "bounding_box": {"x": 60, "y": 240, "width": 540, "height": 220}
            },
            {
                "name": "Lotus Mahal Royal Pavilion",
                "category": "facade",
                "image_url": "/monuments/hampi_lotus_mahal.jpg",
                "bounding_box": {"x": 120, "y": 100, "width": 440, "height": 360}
            },
        ],
    },
]


def clean_and_seed():
    db = SessionLocal()
    try:
        print("Synchronizing monuments and regions...")
        
        # Remove any extraneous monuments
        allowed_keys = ["ajanta", "brihad", "brihadisvara", "brihadeshvarar", "hampi"]
        all_monuments = db.query(Monument).all()
        for m in all_monuments:
            if not any(k in m.name.lower() for k in allowed_keys):
                print(f"Deleting monument: {m.name}")
                db.delete(m)
        db.flush()

        remaining_monuments = db.query(Monument).all()
        rem_map = {}
        for m in remaining_monuments:
            for k in ["ajanta", "brihad", "hampi"]:
                if k in m.name.lower():
                    rem_map[k] = m
                    break

        for site_data in ALLOWED_MONUMENTS:
            key = "ajanta" if "ajanta" in site_data["name"].lower() else ("brihad" if "brihad" in site_data["name"].lower() else "hampi")
            mon = rem_map.get(key)
            if not mon:
                mon = Monument(
                    id=uuid.uuid4(),
                    name=site_data["name"],
                    location_name=site_data["location_name"],
                    latitude=site_data["latitude"],
                    longitude=site_data["longitude"],
                    heritage_status=site_data["heritage_status"],
                    importance_tier=site_data["importance_tier"],
                    image_url=site_data["image_url"],
                )
                db.add(mon)
                db.flush()
                rem_map[key] = mon
            else:
                mon.name = site_data["name"]
                mon.location_name = site_data["location_name"]
                mon.latitude = site_data["latitude"]
                mon.longitude = site_data["longitude"]
                mon.heritage_status = site_data["heritage_status"]
                mon.importance_tier = site_data["importance_tier"]
                mon.image_url = site_data["image_url"]

            # Manage regions: remove old/duplicate regions not in target list
            target_region_names = [r["name"].lower() for r in site_data["regions"]]
            existing_regions = db.query(Region).filter(Region.monument_id == mon.id).all()
            
            # Delete duplicate or non-matching regions
            for er in existing_regions:
                # normalize name comparison
                matched = False
                for tr_name in target_region_names:
                    if tr_name[:12] in er.name.lower() or er.name.lower()[:12] in tr_name:
                        matched = True
                        break
                if not matched:
                    print(f"Deleting outdated region: {er.name}")
                    db.delete(er)
            db.flush()

            # Now add or update target regions
            current_regions = db.query(Region).filter(Region.monument_id == mon.id).all()
            reg_map = {r.name.lower()[:12]: r for r in current_regions}

            for r_data in site_data["regions"]:
                reg_prefix = r_data["name"].lower()[:12]
                reg = reg_map.get(reg_prefix)
                if not reg:
                    reg = Region(
                        id=uuid.uuid4(),
                        monument_id=mon.id,
                        name=r_data["name"],
                        category=r_data["category"],
                        image_url=r_data["image_url"],
                        bounding_box=r_data["bounding_box"],
                    )
                    db.add(reg)
                    db.flush()
                    reg_map[reg_prefix] = reg
                    print(f"  Added region: {reg.name} -> {reg.image_url}")
                else:
                    reg.name = r_data["name"]
                    reg.category = r_data["category"]
                    reg.image_url = r_data["image_url"]
                    reg.bounding_box = r_data["bounding_box"]
                    print(f"  Updated region: {reg.name} -> {reg.image_url}")

                # Ensure ConsensusState exists
                cs = db.query(ConsensusState).filter(ConsensusState.region_id == reg.id).first()
                if not cs:
                    cs = ConsensusState(
                        region_id=reg.id,
                        version=1,
                        cumulative_reliability=0.92,
                        observation_count=3,
                        structural_health_index=0.88,
                    )
                    db.add(cs)

        db.commit()

        # Print final status
        print("\n================ DATABASE MONUMENTS & REGIONS ================")
        for m in db.query(Monument).all():
            print(f"\nMonument: {m.name} ({m.image_url})")
            regs = db.query(Region).filter(Region.monument_id == m.id).all()
            for r in regs:
                print(f"   -> [REG-{str(r.id)[:4].upper()}] {r.name} -> {r.image_url}")
        print("===============================================================")

    except Exception as e:
        db.rollback()
        print(f"Error during clean and seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clean_and_seed()
