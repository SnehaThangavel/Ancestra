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

    for s in sites:
        short_name = s["name"].split(",")[0].split(" ")[0]
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
                image_url=s["image_url"],
            )
            db.add(m)
            db.commit()
            db.refresh(m)
            print(f"Created Monument: {m.name} ({m.id})")
            mon_id = m.id
        else:
            mon_id = existing.id
            if not existing.image_url:
                existing.image_url = s["image_url"]
                db.commit()
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
                    image_url=r.get("image_url"),
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
            elif not reg_existing.image_url and r.get("image_url"):
                reg_existing.image_url = r.get("image_url")
                db.commit()

    db.close()
    print("Seeding complete! 14 heritage monuments and regions populated.")


if __name__ == "__main__":
    seed()

