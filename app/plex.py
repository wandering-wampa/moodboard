import os
import requests
from xml.etree import ElementTree as ET

PLEX_URL = os.environ["PLEX_URL"]
PLEX_TOKEN = os.environ["PLEX_TOKEN"]
PLEX_MACHINE = os.environ["PLEX_MACHINE_ID"]


def _get(path):
    r = requests.get(f"{PLEX_URL}{path}", params={"X-Plex-Token": PLEX_TOKEN}, timeout=10)
    r.raise_for_status()
    return ET.fromstring(r.text)


def get_movies():
    root = _get("/library/sections/1/all")
    out = []
    for v in root.findall("Video"):
        genres = [g.attrib["tag"] for g in v.findall("Genre")]
        out.append({
            "id": v.attrib["ratingKey"],
            "title": v.attrib.get("title", ""),
            "year": v.attrib.get("year", ""),
            "summary": v.attrib.get("summary", "")[:300],
            "genres": genres,
            "thumb": f"/img/plex/{v.attrib['ratingKey']}" if v.attrib.get("thumb") else None,
            "deep_link": f"{PLEX_URL}/web/index.html#!/server/{PLEX_MACHINE}/details?key=/library/metadata/{v.attrib['ratingKey']}",
        })
    return out


def get_shows():
    root = _get("/library/sections/2/all")
    out = []
    for d in root.findall("Directory"):
        genres = [g.attrib["tag"] for g in d.findall("Genre")]
        out.append({
            "id": d.attrib["ratingKey"],
            "title": d.attrib.get("title", ""),
            "year": d.attrib.get("year", ""),
            "summary": d.attrib.get("summary", "")[:300],
            "genres": genres,
            "thumb": f"/img/plex/{d.attrib['ratingKey']}" if d.attrib.get("thumb") else None,
            "deep_link": f"{PLEX_URL}/web/index.html#!/server/{PLEX_MACHINE}/details?key=/library/metadata/{d.attrib['ratingKey']}",
        })
    return out
