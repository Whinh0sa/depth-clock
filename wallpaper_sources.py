import random

# Comprehensive curated wallpaper collections optimized for 3D depth clocks
CURATED_WALLPAPERS = {
    "Curated Nature (Unsplash)": [
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1472214222541-d510753a8707?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1501854140801-50d01698950b?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1426604966848-d7adac402bff?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1433086966358-54859d0ed716?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1470813740244-df37b8c1edcb?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Space & Stars": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1538370965046-79c0d6907d47?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1464802686167-b939a6910659?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1481819613568-3701cbc70156?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Cities & Architecture": [
        "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1449034446853-66c86144b0ad?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1449844908441-8829872d2607?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1444723121867-7a241cacace9?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1517581177682-a085bb7ffb15?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Abstract": [
        "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1541701494587-cb58502866ab?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1546484396-fb3fc6f95f98?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1563089145-599997674dc9?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1500462918059-b1a0cb512f1d?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Minimalist": [
        "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1449247709967-d4461a6a6103?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1435820394963-a15297f976fd?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1507721999472-8ed4421c4af2?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1453928582365-b6ad33cbcf64?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1506744626753-97992928574c?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1483728642387-6c3ba6c6276b?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Animals": [
        "https://images.unsplash.com/photo-1543946207-39fdc172e1c3?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1456926631375-92c8ce872def?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1534567153574-2b12153a87f0?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1555169062-013468b47731?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1574144611814-484d8ee9638c?auto=format&fit=crop&q=80&w=1920"
    ]
}

WALLPAPER_SOURCE_OPTIONS = [
    "Picsum Photos (Random)",
    "Picsum Photos (Grayscale)",
    "Picsum Photos (Blur)",
    "Curated Nature (Unsplash)",
    "Curated Space & Stars",
    "Curated Cities & Architecture",
    "Curated Abstract",
    "Curated Minimalist",
    "Curated Animals"
]

def get_wallpaper_url(source, screen_w=1920, screen_h=1080):
    """
    Returns an image URL for the requested wallpaper source.
    """
    if source in CURATED_WALLPAPERS:
        return random.choice(CURATED_WALLPAPERS[source])
    else:
        sig = random.randint(1, 100000)
        url = f"https://picsum.photos/{screen_w}/{screen_h}?random={sig}"
        if source == "Picsum Photos (Grayscale)":
            url += "&grayscale"
        elif source == "Picsum Photos (Blur)":
            url += "&blur"
        elif source == "Picsum Photos (Grayscale & Blur)":
            url += "&grayscale&blur"
        return url
