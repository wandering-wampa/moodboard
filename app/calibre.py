import os
import sqlite3

CALIBRE_DB = os.environ.get("CALIBRE_DB", "/calibre-library/metadata.db")


def get_books():
    con = sqlite3.connect(CALIBRE_DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT
            b.id,
            b.title,
            group_concat(DISTINCT a.name) AS authors,
            group_concat(DISTINCT t.name) AS tags,
            d.text AS description
        FROM books b
        LEFT JOIN books_authors_link ba ON ba.book = b.id
        LEFT JOIN authors a             ON a.id = ba.author
        LEFT JOIN books_tags_link bt    ON bt.book = b.id
        LEFT JOIN tags t                ON t.id = bt.tag
        LEFT JOIN comments d            ON d.book = b.id
        GROUP BY b.id
    """).fetchall()
    con.close()

    out = []
    for r in rows:
        tags = [t.strip() for t in (r["tags"] or "").split(",") if t.strip()]
        skip_tags = {"knitting", "patterns", "crafts", "non-fiction", "tabletop-rpg", "gaming", "cooking"}
        if skip_tags.issuperset(set(tags[:3])):
            continue
        out.append({
            "id": r["id"],
            "title": r["title"],
            "author": (r["authors"] or "").split(",")[0].strip(),
            "tags": tags[:8],
            "description": (r["description"] or "")[:400],
            "thumb": f"/img/calibre/{r['id']}",
            "deep_link": f"/img/calibre/{r['id']}",  # overridden in main.py
        })
    return out
