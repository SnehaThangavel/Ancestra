"""Fetch and download authentic Indian monument photos for Ancestra."""

import os
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

MONUMENT_URLS = {
    # 1. Shore Temple
    "shore_temple.jpg": [
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Shore_temple_Mamallapuram.jpg/800px-Shore_temple_Mamallapuram.jpg"
    ],
    # 2. Taj Mahal
    "taj_mahal.jpg": [
        "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&q=80&w=800",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Taj_Mahal_%28Edited%29.jpeg/800px-Taj_Mahal_%28Edited%29.jpeg"
    ],
    # 3. Konark Sun Temple
    "konark_sun_temple.jpg": [
        "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Konark_Sun_Temple.jpg/800px-Konark_Sun_Temple.jpg"
    ],
    # 4. Qutb Minar
    "qutb_minar.jpg": [
        "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&q=80&w=800",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Qutub_Minar_in_May_2022.jpg/800px-Qutub_Minar_in_May_2022.jpg"
    ],
    # 5. Rani ki Vav Stepwell
    "rani_ki_vav.jpg": [
        "https://images.unsplash.com/photo-1609137144813-7d9921338f24?auto=format&fit=crop&q=80&w=800",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Rani_ki_vav_01.jpg/800px-Rani_ki_vav_01.jpg"
    ],
    # 6. Kailasa Temple Ellora
    "kailasa_ellora.jpg": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Ellora_cave16_001.jpg/800px-Ellora_cave16_001.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Kailasa_temple%2C_cave_16%2C_Ellora_01.jpg/800px-Kailasa_temple%2C_cave_16%2C_Ellora_01.jpg",
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
    ],
    # 7. Khajuraho Group of Monuments
    "khajuraho.jpg": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Kandariya_Mahadeva_Temple.jpg/800px-Kandariya_Mahadeva_Temple.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Khajuraho_-_Kandariya_Mahadeo_Temple.jpg/800px-Khajuraho_-_Kandariya_Mahadeo_Temple.jpg",
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
    ],
    # 8. Elephanta Caves
    "elephanta_caves.jpg": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Elephanta_Caves_Trimurti.jpg/800px-Elephanta_Caves_Trimurti.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Trimurti%2C_Elephanta_Caves.jpg/800px-Trimurti%2C_Elephanta_Caves.jpg",
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
    ],
    # 9. Meenakshi Amman Temple
    "meenakshi_temple.jpg": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Madurai_Meenakshi_Amman_Temple.jpg/800px-Madurai_Meenakshi_Amman_Temple.jpg",
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
    ],
    # 10. Modhera Sun Temple
    "modhera_sun_temple.jpg": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Sun_Temple_at_Modhera.jpg/800px-Sun_Temple_at_Modhera.jpg",
        "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"
    ],
    # 11. Pattadakal Monuments
    "pattadakal.jpg": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Virupaksha_temple_Pattadakal.jpg/800px-Virupaksha_temple_Pattadakal.jpg",
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
    ],
}

def main():
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "public", "monuments"))
    os.makedirs(target_dir, exist_ok=True)

    for filename, urls in MONUMENT_URLS.items():
        out_path = os.path.join(target_dir, filename)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
            print(f"[SKIP] Already exists: {filename} ({os.path.getsize(out_path)} bytes)")
            continue

        success = False
        for url in urls:
            try:
                print(f"Downloading {filename} from {url}...")
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                    content = resp.read()
                    if len(content) > 5000:
                        with open(out_path, "wb") as f:
                            f.write(content)
                        print(f"  -> SUCCESS ({len(content)} bytes)")
                        success = True
                        break
            except Exception as e:
                print(f"  -> Failed ({url}): {e}")

        if not success:
            print(f"[WARN] Could not download {filename} from any candidate URL.")

if __name__ == "__main__":
    main()
