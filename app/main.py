import os
import time
import logging
import requests as _requests
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from plex import get_movies, get_shows, PLEX_URL, PLEX_TOKEN
from calibre import get_books, CALIBRE_DB
from komga import get_series, KOMGA_AUTH, KOMGA_URL
from claude_client import get_recommendations

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

CALIBRE_WEB_URL = os.environ.get("CALIBRE_WEB_URL", "http://calibre-web-automated:8083")

app = FastAPI()

_cache = {"data": None, "ts": 0}
CACHE_TTL = 1800


def get_library():
    now = time.time()
    if _cache["data"] is None or now - _cache["ts"] > CACHE_TTL:
        log.info("Refreshing library cache...")
        _cache["data"] = {
            "movies": get_movies(),
            "shows": get_shows(),
            "books": get_books(),
            "comics": get_series(),
        }
        _cache["ts"] = now
        log.info(
            f"Library loaded: {len(_cache['data']['movies'])} movies, "
            f"{len(_cache['data']['shows'])} shows, "
            f"{len(_cache['data']['books'])} books, "
            f"{len(_cache['data']['comics'])} comics"
        )
    return _cache["data"]


class MoodRequest(BaseModel):
    mood: str


@app.post("/recommend")
async def recommend(req: MoodRequest):
    if not req.mood.strip():
        raise HTTPException(400, "Mood cannot be empty")
    try:
        lib = get_library()
        recs = get_recommendations(
            req.mood,
            lib["movies"],
            lib["shows"],
            lib["books"],
            lib["comics"],
        )
        return recs
    except Exception as e:
        log.error(f"Recommendation error: {e}")
        raise HTTPException(500, str(e))


@app.post("/refresh")
async def refresh_cache():
    _cache["ts"] = 0
    get_library()
    return {"status": "ok"}


@app.get("/img/plex/{rating_key}")
async def img_plex(rating_key: str):
    url = f"{PLEX_URL}/library/metadata/{rating_key}/thumb"
    r = _requests.get(url, params={"X-Plex-Token": PLEX_TOKEN}, timeout=10)
    if r.status_code != 200:
        raise HTTPException(404)
    return Response(content=r.content, media_type=r.headers.get("content-type", "image/jpeg"))


@app.get("/img/komga/{series_id}")
async def img_komga(series_id: str):
    url = f"{KOMGA_URL}/api/v1/series/{series_id}/thumbnail"
    r = _requests.get(url, auth=KOMGA_AUTH, timeout=10)
    if r.status_code != 200:
        raise HTTPException(404)
    return Response(content=r.content, media_type=r.headers.get("content-type", "image/jpeg"))


@app.get("/img/calibre/{book_id}")
async def img_calibre(book_id: int):
    import sqlite3
    from pathlib import Path
    db = sqlite3.connect(CALIBRE_DB)
    row = db.execute("SELECT path FROM books WHERE id = ?", (book_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404)
    cover = Path(CALIBRE_DB).parent / row[0] / "cover.jpg"
    if not cover.exists():
        raise HTTPException(404)
    return Response(content=cover.read_bytes(), media_type="image/jpeg")


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")
