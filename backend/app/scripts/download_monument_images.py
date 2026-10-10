"""Download authentic images of Indian heritage monuments from Wikipedia using httpx."""

import os
import sys
import httpx

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models.monument import Monument

MONUMENT_PAGES = [
    {
        "slug": "shore_temple",
        "wiki_title": "Shore_Temple",
        "name": "Shore Temple, Mahabalipuram",
    },
    {
        "slug": "brihadisvara_temple",
        "wiki_title": "Brihadisvara_Temple",
        "name": "Brihadisvara Temple, Thanjavur",
    },
    {
        "slug": "hampi_complex",
        "wiki_title": "Vittala_Temple,_Hampi",
        "name": "Hampi Heritage Complex",
    },
    {
        "slug": "konark_sun_temple",
        "wiki_title": "Konark_Sun_Temple",
        "name": "Konark Sun Temple",
    },
    {
        "slug": "taj_mahal",
        "wiki_title": "Taj_Mahal",
        "name": "Taj Mahal Monument Complex",
    },
    {
        "slug": "khajuraho",
        "wiki_title": "Khajuraho_Group_of_Monuments",
        "name": "Khajuraho Group of Monuments",
    },
    {
        "slug": "kailasa_ellora",
        "wiki_title": "Kailasa_Temple,_Ellora",
        "name": "Kailasa Temple, Ellora Caves",
    },
    {
        "slug": "ajanta_caves",
        "wiki_title": "Ajanta_Caves",
        "name": "Ajanta Rock-Cut Caves",
    },
    {
        "slug": "qutb_minar",
        "wiki_title": "Qutb_Minar",
        "name": "Qutb Minar Complex",
    },
    {
        "slug": "meenakshi_temple",
        "wiki_title": "Meenakshi_Temple",
        "name": "Meenakshi Amman Temple",
    },
    {
        "slug": "rani_ki_vav",
        "wiki_title": "Rani_ki_Vav",
        "name": "Rani ki Vav Stepwell",
    },
    {
        "slug": "modhera_sun_temple",
        "wiki_title": "Sun_Temple,_Modhera",
        "name": "Sun Temple, Modhera",
    },
    {
        "slug": "elephanta_caves",
        "wiki_title": "Elephanta_Caves",
        "name": "Elephanta Caves",
    },
    {
        "slug": "pattadakal",
        "wiki_title": "Pattadakal",
        "name": "Pattadakal Monuments Complex",
    },
]


def main():
    root_dir = os.path.dirname(backend_dir)
    frontend_monuments_dir = os.path.join(root_dir, "frontend", "public", "monuments")
    backend_uploads_dir = os.path.join(backend_dir, "uploads", "monuments")

    os.makedirs(frontend_monuments_dir, exist_ok=True)
    os.makedirs(backend_uploads_dir, exist_ok=True)

    db = SessionLocal()
    existing_monuments = db.query(Monument).all()
    mon_map = {m.name.split(",")[0].split(" ")[0].lower(): m for m in existing_monuments}

    headers = {
        "User-Agent": "AncestraHeritageBot/1.0 (https://ancestra.ai; team@ancestra.ai) python-httpx/0.27"
    }

    client = httpx.Client(headers=headers, timeout=20.0, follow_redirects=True)

    print("=== Downloading Verified Authentic Indian Monument Images ===", flush=True)

    for item in MONUMENT_PAGES:
        slug = item["slug"]
        name = item["name"]
        wiki_title = item["wiki_title"]

        target_fe = os.path.join(frontend_monuments_dir, f"{slug}.jpg")
        target_be = os.path.join(backend_uploads_dir, f"{slug}.jpg")
        local_path = f"/monuments/{slug}.jpg"

        print(f"\n[+] Fetching {name} ({wiki_title})...", flush=True)
        try:
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
            resp = client.get(summary_url)
            if resp.status_code != 200:
                print(f"    Failed summary fetch: HTTP {resp.status_code}", flush=True)
                continue

            data = resp.json()
            img_url = None
            if "originalimage" in data and "source" in data["originalimage"]:
                img_url = data["originalimage"]["source"]
            elif "thumbnail" in data and "source" in data["thumbnail"]:
                img_url = data["thumbnail"]["source"]

            if not img_url:
                print(f"    No image URL found in Wikipedia summary", flush=True)
                continue

            print(f"    Downloading: {img_url}", flush=True)
            img_resp = client.get(img_url)
            if img_resp.status_code == 200 and len(img_resp.content) > 1000:
                with open(target_fe, "wb") as f:
                    f.write(img_resp.content)
                with open(target_be, "wb") as f:
                    f.write(img_resp.content)
                print(f"    Successfully saved {slug}.jpg ({len(img_resp.content)} bytes)", flush=True)

                # Update database
                short_name = name.split(",")[0].split(" ")[0].lower()
                m = mon_map.get(short_name)
                if m:
                    m.image_url = local_path
                    print(f"    Updated DB row for '{m.name}' -> '{local_path}'", flush=True)
            else:
                print(f"    Failed image download: HTTP {img_resp.status_code}", flush=True)
        except Exception as err:
            print(f"    Error processing {name}: {err}", flush=True)

    db.commit()
    db.close()
    client.close()
    print("\n[SUCCESS] All authentic monument photos downloaded locally to /monuments/!", flush=True)


if __name__ == "__main__":
    main()
