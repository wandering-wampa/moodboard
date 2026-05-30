import json
import logging
import os
import anthropic

CLIENT = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM = """You are MoodBoard — a warm, perceptive media recommender for a family's personal home library.

Your job: given a mood described in plain language, pick ONE item from each of four categories (movie, show, book, comic) that best matches that mood. Then write a short, personal pitch for each.

Rules:
- Match the FEELING, not just the genre. "Dark and broody" is different from "scary". "Cozy" means comfort, not just light.
- Pick confidently. Don't hedge. One recommendation per category.
- Pitches should be 2-3 sentences, warm and specific — explain WHY this fits the mood right now.
- Never recommend something that clearly contradicts the mood (e.g. a comedy for "I want to cry").
- If the library is thin on a category, pick the closest match available.

Respond ONLY with valid JSON, no other text:
{
  "movie":  { "id": "...", "title": "...", "pitch": "..." },
  "show":   { "id": "...", "title": "...", "pitch": "..." },
  "book":   { "id": "...", "title": "...", "pitch": "..." },
  "comic":  { "id": "...", "title": "...", "pitch": "..." }
}"""


def build_library_text(movies, shows, books, comics):
    lines = ["## MOVIES"]
    for m in movies:
        genres = ", ".join(m["genres"]) if m["genres"] else "unknown"
        lines.append(f"[{m['id']}] {m['title']} ({m['year']}) | {genres} | {m['summary'][:150]}")

    lines.append("\n## TV SHOWS")
    for s in shows:
        genres = ", ".join(s["genres"]) if s["genres"] else "unknown"
        lines.append(f"[{s['id']}] {s['title']} ({s['year']}) | {genres} | {s['summary'][:150]}")

    lines.append("\n## BOOKS")
    for b in books:
        tags = ", ".join(b["tags"][:6]) if b["tags"] else "unknown"
        lines.append(f"[{b['id']}] {b['title']} by {b['author']} | {tags} | {b['description'][:400]}")

    lines.append("\n## COMICS")
    for c in comics:
        genres = ", ".join(c["genres"]) if c["genres"] else "unknown"
        lines.append(f"[{c['id']}] {c['title']} | {genres} | {c['summary'][:120]}")

    return "\n".join(lines)


def get_recommendations(mood: str, movies, shows, books, comics):
    library_text = build_library_text(movies, shows, books, comics)

    response = CLIENT.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=[
            {"type": "text", "text": SYSTEM},
            {"type": "text", "text": f"## AVAILABLE LIBRARY\n\n{library_text}", "cache_control": {"type": "ephemeral"}},
        ],
        messages=[
            {"role": "user", "content": f"My mood: {mood}"}
        ],
    )

    u = response.usage
    logging.getLogger(__name__).info(
        f"Tokens — input: {u.input_tokens}, output: {u.output_tokens}, "
        f"cache_write: {getattr(u, 'cache_creation_input_tokens', 0)}, "
        f"cache_read: {getattr(u, 'cache_read_input_tokens', 0)}"
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    recs = json.loads(raw)

    lookup = {}
    for item in movies:  lookup[str(item["id"])] = item
    for item in shows:   lookup[str(item["id"])] = item
    for item in books:   lookup[str(item["id"])] = item
    for item in comics:  lookup[str(item["id"])] = item

    for category in ("movie", "show", "book", "comic"):
        rec = recs.get(category, {})
        item = lookup.get(str(rec.get("id", "")), {})
        rec["thumb"] = item.get("thumb")
        rec["deep_link"] = item.get("deep_link")
        recs[category] = rec

    return recs
