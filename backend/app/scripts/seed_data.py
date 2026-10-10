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
            "image_url": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "East-Facing Rajasimhesvara Vimana", "category": "vimana", "image_url": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"},
                {"name": "Southern Adhisthana Plinth", "category": "facade", "image_url": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"},
                {"name": "Western Small Shrine Mandapa", "category": "mandapa", "image_url": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"},
                {"name": "North Enclosure Carved Relief", "category": "relief", "image_url": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Brihadisvara Temple, Thanjavur",
            "location_name": "Thanjavur, Tamil Nadu",
            "latitude": 10.7828,
            "longitude": 79.1318,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1600100397608-f090742f4949?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Main 13-Tiered Vimana Tower", "category": "vimana", "image_url": "https://images.unsplash.com/photo-1600100397608-f090742f4949?auto=format&fit=crop&q=80&w=800"},
                {"name": "Nandi Mandapa Monolith", "category": "mandapa", "image_url": "https://images.unsplash.com/photo-1600100397608-f090742f4949?auto=format&fit=crop&q=80&w=800"},
                {"name": "Eastern Gopuram Gateway", "category": "facade", "image_url": "https://images.unsplash.com/photo-1600100397608-f090742f4949?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Hampi Heritage Complex",
            "location_name": "Hampi, Karnataka",
            "latitude": 15.3350,
            "longitude": 76.4600,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1627894099419-f5ebba5e3f42?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Vittala Temple Stone Chariot", "category": "sculpture", "image_url": "https://images.unsplash.com/photo-1627894099419-f5ebba5e3f42?auto=format&fit=crop&q=80&w=800"},
                {"name": "Musical Pillars Mandapa", "category": "pillar", "image_url": "https://images.unsplash.com/photo-1627894099419-f5ebba5e3f42?auto=format&fit=crop&q=80&w=800"},
                {"name": "Virupaksha Temple Gopuram", "category": "facade", "image_url": "https://images.unsplash.com/photo-1627894099419-f5ebba5e3f42?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Konark Sun Temple",
            "location_name": "Konark, Odisha",
            "latitude": 19.8876,
            "longitude": 86.0945,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Jagamohana Pyramidal Roof Steps", "category": "roof", "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"},
                {"name": "South Carved Stone Wheel", "category": "relief", "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"},
                {"name": "Natamandira Dance Hall Pillars", "category": "pillar", "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Taj Mahal Monument Complex",
            "location_name": "Agra, Uttar Pradesh",
            "latitude": 27.1751,
            "longitude": 78.0421,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Main Marble Onion Dome", "category": "dome", "image_url": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&q=80&w=800"},
                {"name": "South-West Corner Minaret", "category": "pillar", "image_url": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&q=80&w=800"},
                {"name": "Central Pishtaq Archway", "category": "arch", "image_url": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Khajuraho Group of Monuments",
            "location_name": "Chhatarpur, Madhya Pradesh",
            "latitude": 24.8318,
            "longitude": 79.9199,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Kandariya Mahadeva Shikhara", "category": "vimana", "image_url": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&q=80&w=800"},
                {"name": "Lakshmana Temple Outer Frieze", "category": "frieze", "image_url": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Kailasa Temple, Ellora Caves",
            "location_name": "Aurangabad, Maharashtra",
            "latitude": 20.0268,
            "longitude": 75.1792,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1620766165457-a8025baa82e0?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Monolithic Rock-Cut Vimana", "category": "vimana", "image_url": "https://images.unsplash.com/photo-1620766165457-a8025baa82e0?auto=format&fit=crop&q=80&w=800"},
                {"name": "Nandi Shrine Monolithic Pillar", "category": "pillar", "image_url": "https://images.unsplash.com/photo-1620766165457-a8025baa82e0?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Ajanta Rock-Cut Caves",
            "location_name": "Aurangabad, Maharashtra",
            "latitude": 20.5519,
            "longitude": 75.7033,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Cave 1 Chaitya Hall Facade", "category": "facade", "image_url": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&q=80&w=800"},
                {"name": "Cave 26 Stupa Rock Carving", "category": "sculpture", "image_url": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Qutb Minar Complex",
            "location_name": "Mehrauli, New Delhi",
            "latitude": 28.5244,
            "longitude": 77.1855,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Fluted Sandstone Minar Balcony", "category": "facade", "image_url": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&q=80&w=800"},
                {"name": "Alai Darwaza Inscription Arch", "category": "arch", "image_url": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Meenakshi Amman Temple",
            "location_name": "Madurai, Tamil Nadu",
            "latitude": 9.9195,
            "longitude": 78.1193,
            "heritage_status": "National Monument",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Southern Raja Gopuram Tier", "category": "facade", "image_url": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"},
                {"name": "Ayiram Kaal Mandapa Pillars", "category": "pillar", "image_url": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Rani ki Vav Stepwell",
            "location_name": "Patan, Gujarat",
            "latitude": 23.8589,
            "longitude": 72.1013,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 1,
            "image_url": "https://images.unsplash.com/photo-1609137144813-7d9921338f24?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Level 4 Multi-Storey Pavilion", "category": "pillar", "image_url": "https://images.unsplash.com/photo-1609137144813-7d9921338f24?auto=format&fit=crop&q=80&w=800"},
                {"name": "Vishnu Sheshashayi Relief Wall", "category": "relief", "image_url": "https://images.unsplash.com/photo-1609137144813-7d9921338f24?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Sun Temple, Modhera",
            "location_name": "Mehsana, Gujarat",
            "latitude": 23.5835,
            "longitude": 72.1330,
            "heritage_status": "National Monument",
            "importance_tier": 2,
            "image_url": "https://images.unsplash.com/photo-1600100397608-f010f443b793?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Sabha Mandapa Carved Columns", "category": "pillar", "image_url": "https://images.unsplash.com/photo-1600100397608-f010f443b793?auto=format&fit=crop&q=80&w=800"},
                {"name": "Surya Kund Stepped Reservoir", "category": "facade", "image_url": "https://images.unsplash.com/photo-1600100397608-f010f443b793?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Elephanta Caves",
            "location_name": "Gharapuri, Maharashtra",
            "latitude": 18.9633,
            "longitude": 72.9315,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 2,
            "image_url": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Trimurti Sadashiva Colossal Relief", "category": "sculpture", "image_url": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&q=80&w=800"},
                {"name": "Main Cave Linga Shrine Dwarapalas", "category": "pillar", "image_url": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&q=80&w=800"},
            ],
        },
        {
            "name": "Pattadakal Monuments Complex",
            "location_name": "Bagalkot, Karnataka",
            "latitude": 15.9490,
            "longitude": 75.8160,
            "heritage_status": "UNESCO World Heritage Site",
            "importance_tier": 2,
            "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800",
            "regions": [
                {"name": "Virupaksha Dravidian Shikhara", "category": "vimana", "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"},
                {"name": "Mallikarjuna Temple Carved Frieze", "category": "frieze", "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"},
            ],
        },
    ]

    # Pre-fetch existing monuments and regions in one query
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
        elif not m.image_url:
            m.image_url = s["image_url"]

    db.flush()

    existing_regions = db.query(Region).all()
    reg_set = {(r.monument_id, r.name[:12].lower()) for r in existing_regions}

    for s in sites:
        short_name = s["name"].split(",")[0].split(" ")[0].lower()
        m = mon_map.get(short_name)
        if not m:
            continue

        for r in s["regions"]:
            reg_key = (m.id, r["name"][:12].lower())
            if reg_key not in reg_set:
                reg = Region(
                    id=uuid.uuid4(),
                    monument_id=m.id,
                    name=r["name"],
                    category=r["category"],
                    image_url=r.get("image_url"),
                )
                db.add(reg)
                reg_set.add(reg_key)

    # Seed initial observation & anomaly findings if table is empty
    from app.models.observation import Observation
    from app.models.validation import AnomalyValidation
    from app.models.work_order import WorkOrder

    existing_anomalies_count = db.query(AnomalyValidation).count()
    if existing_anomalies_count == 0:
        all_regs = db.query(Region).all()
        for idx, reg in enumerate(all_regs[:6]):
            obs = Observation(
                id=uuid.uuid4(),
                monument_id=reg.monument_id,
                region_id=reg.id,
                image_url=reg.image_url or "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
                blur_score=0.92,
                sharpness_score=0.88,
                overall_quality_score=0.90,
                is_valid_quality=True,
                registration_success=True,
                registration_confidence=0.95,
                reliability_score=0.89,
            )
            db.add(obs)

            is_severe = idx == 0
            is_medium = idx == 1 or idx == 2
            severity_score = 0.45 if is_severe else (0.28 if is_medium else 0.08)
            anomaly_type = "crack" if is_severe else ("surface_deterioration" if is_medium else "discoloration")
            
            val = AnomalyValidation(
                id=uuid.uuid4(),
                region_id=reg.id,
                anomaly_type=anomaly_type,
                ssim_delta=0.22 if is_severe else 0.12,
                severity_score=severity_score,
                corroboration_count=3 if is_severe else 1,
                corroborating_observation_ids=[obs.id],
                is_confirmed=True,
                defect_polygon={
                    "bounding_boxes": [[140, 180, 260, 210]] if is_severe else [[200, 300, 180, 150]],
                    "ssim_score": 0.78 if is_severe else 0.88,
                    "severity_score": severity_score,
                },
            )
            db.add(val)

            if is_severe or is_medium:
                wo = WorkOrder(
                    id=uuid.uuid4(),
                    validation_id=val.id,
                    urgency_index=0.85 if is_severe else 0.55,
                    status="assigned" if is_severe else "pending",
                    assigned_team="Dr. A. Sharma (ASI Lead)",
                    recommended_action=f"Structural stabilization and surface repair for {anomaly_type.replace('_', ' ')} on {reg.name}.",
                )
                db.add(wo)
        print("  Seeded baseline observations, anomalies, and work orders.")

    db.commit()
    db.close()
    print("Fast batch seeding complete! Monuments, regions, and anomalies populated.")


if __name__ == "__main__":
    seed()
    seed()

