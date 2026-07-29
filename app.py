from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, redirect, render_template, request, send_file, url_for

app = Flask(__name__)
DATA = Path(app.root_path) / "data" / "prompts.json"


def prompts() -> list[dict]:
    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save(items: list[dict]) -> None:
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(items[:500], ensure_ascii=False, indent=2), encoding="utf-8")


def tags(value: str) -> list[str]:
    return list(dict.fromkeys(x.strip().lower()[:32] for x in value.split(",") if x.strip()))[:8]


@app.get("/")
def home():
    items = prompts()
    return render_template("index.html", count=len(items), recent=items[:3])


@app.route("/generator", methods=["GET", "POST"])
def generator():
    result = ""
    if request.method == "POST":
        topic = request.form.get("topic", "").strip()[:180]
        audience = request.form.get("audience", "genel kullanıcı").strip()[:100]
        tone = request.form.get("tone", "net ve faydalı").strip()[:100]
        if topic:
            result = f"{topic} konusunda {audience} için {tone} tonda yardımcı ol. Önce hedefi ve varsayımları kısa doğrula. Ardından uygulanabilir, adım adım yanıt ver. Eksik bilgi varsa en fazla 3 net soru sor; bilmediğin bilgiyi uydurma."
    return render_template("generator.html", result=result)


@app.post("/prompts")
def create_prompt():
    title = request.form.get("title", "").strip()[:120]
    body = request.form.get("body", "").strip()[:8000]
    if title and body:
        items = prompts()
        items.insert(0, {"id": uuid4().hex, "title": title, "body": body, "tags": tags(request.form.get("tags", "")), "favorite": False, "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")})
        save(items)
    return redirect(url_for("library"))


@app.get("/prompts")
def library():
    query = request.args.get("q", "").casefold().strip()
    tag = request.args.get("tag", "").casefold().strip()
    items = prompts()
    if query:
        items = [x for x in items if query in x["title"].casefold() or query in x["body"].casefold()]
    if tag:
        items = [x for x in items if tag in x.get("tags", [])]
    all_tags = sorted({tag for item in prompts() for tag in item.get("tags", [])})
    return render_template("prompts.html", prompts=items, tags=all_tags, query=query)


@app.post("/prompts/<prompt_id>/favorite")
def favorite(prompt_id: str):
    items = prompts()
    for item in items:
        if item["id"] == prompt_id:
            item["favorite"] = not item.get("favorite", False)
            save(items)
            return redirect(url_for("library"))
    abort(404)


@app.post("/prompts/<prompt_id>/delete")
def delete(prompt_id: str):
    items = prompts()
    updated = [item for item in items if item["id"] != prompt_id]
    if len(updated) == len(items):
        abort(404)
    save(updated)
    return redirect(url_for("library"))


@app.get("/export")
def export():
    if not DATA.exists(): save([])
    return send_file(DATA, as_attachment=True, download_name="promptforge-backup.json")


@app.get("/health")
def health(): return {"status": "online", "app": "PromptForge"}


if __name__ == "__main__": app.run(host="127.0.0.1", port=5000)
