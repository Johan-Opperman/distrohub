#!/usr/bin/env python3
"""
DistroHub — Flask + SQLite backend.  by Opperman Cybernetix.

Run:
    pip install -r requirements.txt
    python3 app.py
Then open http://localhost:5000  (or http://<pi-ip>:5000 on your network).

The database (distrohub.db) is created and seeded from distros.json on first run.
Contact-form messages are always saved to the DB; they're also emailed if you set
the SMTP_* environment variables (see README).
"""
import json, os, sqlite3, smtplib, ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from flask import Flask, g, jsonify, request, render_template, abort, Response

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "distrohub.db"
SEED = BASE / "distros.json"

app = Flask(__name__)

# ---------- database ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exc):
    d = g.pop("db", None)
    if d is not None:
        d.close()

SCHEMA = """
CREATE TABLE IF NOT EXISTS distros(
  id TEXT PRIMARY KEY, name TEXT, cat TEXT, g TEXT, tags TEXT, pm TEXT,
  based TEXT, diff TEXT, url TEXT, blurb TEXT, usb TEXT, install TEXT,
  after TEXT, upd TEXT, note TEXT, sort INTEGER
);
CREATE TABLE IF NOT EXISTS reviews(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  distro_id TEXT NOT NULL, who TEXT, r INTEGER, c TEXT, created TEXT,
  FOREIGN KEY(distro_id) REFERENCES distros(id)
);
CREATE TABLE IF NOT EXISTS contacts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT, email TEXT, topic TEXT, message TEXT, created TEXT, emailed INTEGER DEFAULT 0
);
"""

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    # seed distros once
    have = con.execute("SELECT COUNT(*) FROM distros").fetchone()[0]
    if have == 0 and SEED.exists():
        data = json.loads(SEED.read_text())
        for i, d in enumerate(data):
            con.execute(
                """INSERT INTO distros(id,name,cat,g,tags,pm,based,diff,url,blurb,usb,install,after,upd,note,sort)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (d["id"], d["name"], d["cat"], d.get("g","#35d0ba"),
                 json.dumps(d.get("tags",[])), d.get("pm",""), d.get("based",""),
                 d.get("diff",""), d.get("url",""), d.get("blurb",""), d.get("usb",""),
                 json.dumps(d.get("install",[])), d.get("after",""), d.get("update",""),
                 d.get("note",""), i))
            # optional demo reviews from the seed
            for s in d.get("seed", []):
                con.execute("INSERT INTO reviews(distro_id,who,r,c,created) VALUES(?,?,?,?,?)",
                            (d["id"], s["who"], s["r"], s["c"], now()))
        con.commit()
        print(f"Seeded {len(data)} distros into {DB_PATH.name}")
    con.close()

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def distro_row_to_dict(row, avg=None, count=None):
    d = dict(row)
    d["tags"] = json.loads(d.get("tags") or "[]")
    d["install"] = json.loads(d.get("install") or "[]")
    d["update"] = d.pop("upd", "")
    d.pop("sort", None)
    if avg is not None:
        d["avg"] = round(avg, 2)
        d["count"] = count
    return d

# ---------- pages ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/tools")
def api_tools():
    path = BASE / "tools.json"
    if not path.exists():
        return jsonify([])
    return jsonify(json.loads(path.read_text()))

@app.route("/distros/<did>.pdf")
def distro_pdf(did):
    row = db().execute("SELECT * FROM distros WHERE id=?", (did,)).fetchone()
    if not row:
        abort(404)
    from pdfgen import build_distro_pdf
    d = distro_row_to_dict(row)
    buf = build_distro_pdf(d)
    from flask import send_file
    fname = did + "-distrohub-guide.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=fname)


@app.route("/robots.txt")
def robots():
    return Response(
        "User-agent: *\nAllow: /\nSitemap: https://distrohub.opperman.dev/sitemap.xml\n",
        mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    rows = db().execute("SELECT id FROM distros ORDER BY sort").fetchall()
    locs = ["https://distrohub.opperman.dev/"]
    locs += [f"https://distrohub.opperman.dev/distros/{r['id']}.pdf" for r in rows]
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    body += [f"  <url><loc>{u}</loc></url>" for u in locs]
    body.append("</urlset>")
    return Response("\n".join(body), mimetype="application/xml")
# ---------- api ----------
@app.route("/api/distros")
def api_distros():
    rows = db().execute("""
        SELECT d.*,
               COALESCE(AVG(r.r),0) AS avg,
               COUNT(r.id) AS cnt
        FROM distros d LEFT JOIN reviews r ON r.distro_id = d.id
        GROUP BY d.id ORDER BY d.sort
    """).fetchall()
    return jsonify([distro_row_to_dict(row, row["avg"], row["cnt"]) for row in rows])

@app.route("/api/distros/<did>/reviews")
def api_reviews(did):
    rows = db().execute(
        "SELECT who, r, c, created AS 'when' FROM reviews WHERE distro_id=? ORDER BY id DESC",
        (did,)).fetchall()
    return jsonify([dict(x) for x in rows])

@app.route("/api/distros/<did>/reviews", methods=["POST"])
def api_add_review(did):
    d = db()
    if not d.execute("SELECT 1 FROM distros WHERE id=?", (did,)).fetchone():
        abort(404)
    body = request.get_json(force=True, silent=True) or {}
    try:
        rating = int(body.get("r", 0))
    except (TypeError, ValueError):
        rating = 0
    comment = (body.get("c") or "").strip()[:2000]
    who = (body.get("who") or "anonymous").strip()[:60] or "anonymous"
    if rating < 1 or rating > 5:
        return jsonify(error="Rating must be 1–5."), 400
    if not comment:
        return jsonify(error="A comment is required."), 400
    d.execute("INSERT INTO reviews(distro_id,who,r,c,created) VALUES(?,?,?,?,?)",
              (did, who, rating, comment, now()))
    d.commit()
    rows = d.execute("SELECT who,r,c,created AS 'when' FROM reviews WHERE distro_id=? ORDER BY id DESC",
                     (did,)).fetchall()
    agg = d.execute("SELECT COALESCE(AVG(r),0) avg, COUNT(*) cnt FROM reviews WHERE distro_id=?",
                    (did,)).fetchone()
    return jsonify(reviews=[dict(x) for x in rows], avg=round(agg["avg"],2), count=agg["cnt"])

@app.route("/api/contact", methods=["POST"])
def api_contact():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "anonymous").strip()[:80]
    email = (body.get("email") or "").strip()[:120]
    topic = (body.get("topic") or "Other").strip()[:80]
    message = (body.get("message") or "").strip()[:4000]
    if not message:
        return jsonify(error="A message is required."), 400
    d = db()
    cur = d.execute("INSERT INTO contacts(name,email,topic,message,created) VALUES(?,?,?,?,?)",
                    (name, email, topic, message, now()))
    d.commit()
    sent = send_contact_email(name, email, topic, message)
    if sent:
        d.execute("UPDATE contacts SET emailed=1 WHERE id=?", (cur.lastrowid,))
        d.commit()
    # Always report success to the visitor — the message is safely stored either way.
    return jsonify(ok=True, emailed=sent)

# ---------- email (best-effort) ----------
def send_contact_email(name, email, topic, message):
    host = os.environ.get("SMTP_HOST")
    if not host:
        return False  # not configured — message is still saved in the DB
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    pw = os.environ.get("SMTP_PASS", "")
    to = os.environ.get("CONTACT_TO", "cybernetix88@proton.me")
    frm = os.environ.get("CONTACT_FROM", user or to)
    msg = EmailMessage()
    msg["Subject"] = f"[DistroHub · {topic}] from {name}"
    msg["From"] = frm
    msg["To"] = to
    if email:
        msg["Reply-To"] = email
    msg.set_content(f"{message}\n\n— {name}" + (f" ({email})" if email else "") + "\nSent from DistroHub")
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.starttls(context=ctx)
            if user:
                s.login(user, pw)
            s.send_message(msg)
        return True
    except Exception as e:
        print("Email send failed (message still saved):", e)
        return False

if __name__ == "__main__":
    init_db()
    # host=0.0.0.0 so other devices on your network (and you, via the pi's IP) can reach it
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
