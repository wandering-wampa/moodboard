import os
import requests

KOMGA_URL = os.environ.get("KOMGA_URL", "http://komga:25600")
KOMGA_AUTH = (os.environ["KOMGA_USER"], os.environ["KOMGA_PASS"])
KOMGA_PUBLIC = os.environ.get("KOMGA_PUBLIC_URL", "http://localhost:25600")


def get_series():
    r = requests.get(
        f"{KOMGA_URL}/api/v1/series",
        auth=KOMGA_AUTH,
        params={"unpaged": "true", "deleted": "false"},
        timeout=10,
    )
    r.raise_for_status()

    out = []
    for s in r.json().get("content", []):
        meta = s.get("metadata", {})
        if s["name"] in ("Extras", "Variant Covers", "! Unsorted"):
            continue
        out.append({
            "id": s["id"],
            "title": meta.get("title") or s["name"],
            "genres": meta.get("genres", []),
            "summary": (meta.get("summary") or "")[:200],
            "thumb": f"/img/komga/{s['id']}",
            "deep_link": f"{KOMGA_PUBLIC}/series/{s['id']}",
        })
    return out
