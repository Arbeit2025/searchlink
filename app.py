"""検索リンク集 searchlink

キーワードを入れると、主要ショッピングサイトの検索結果へのリンクを
一括生成する小さなツール。検索履歴を SQLite に残せる。
単一ファイル Flask + SQLite。
"""
import os
import sqlite3
from datetime import datetime
from urllib.parse import quote, quote_plus
from zoneinfo import ZoneInfo

from flask import Flask, g, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
JST = ZoneInfo("Asia/Tokyo")
DB_PATH = os.environ.get("SEARCHLINK_DB", os.path.join(os.path.dirname(__file__), "searchlink.db"))


def build_links(keyword):
    q = quote_plus(keyword)
    return [
        ("Amazon.co.jp", f"https://www.amazon.co.jp/s?k={q}"),
        ("楽天市場", f"https://search.rakuten.co.jp/search/mall/{quote(keyword, safe='')}/"),
        ("Yahoo!ショッピング", f"https://shopping.yahoo.co.jp/search?p={q}"),
        ("ヨドバシ.com", f"https://www.yodobashi.com/?word={q}"),
        ("メルカリ", f"https://jp.mercari.com/search?keyword={q}"),
    ]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    db.commit()
    db.close()


PAGE = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>検索リンク集</title>
<style>body{font-family:sans-serif;max-width:640px;margin:2em auto;padding:0 1em}
li{margin:.4em 0}</style>
</head><body>
<h1>検索リンク集</h1>
<p>キーワードから各ショッピングサイトの検索結果リンクを一括で作ります。価格や在庫はリンク先で確認してください。</p>
<form method="post" action="{{ url_for('search') }}">
  <input type="text" name="keyword" value="{{ keyword or '' }}" placeholder="例：ワイヤレスイヤホン" size="30">
  <button type="submit">リンクを作る</button>
</form>
{% if links %}
<h2>「{{ keyword }}」の検索リンク</h2>
<ul>
{% for name, url in links %}
<li><a href="{{ url }}" target="_blank" rel="noopener">{{ name }} で探す</a></li>
{% endfor %}
</ul>
{% endif %}
<h2>検索履歴</h2>
<ul>
{% for h in history %}
<li>{{ h.created_at }} <a href="{{ url_for('index', q=h.keyword) }}">{{ h.keyword }}</a>
  <form method="post" action="{{ url_for('delete_history', hid=h.id) }}" style="display:inline"><button>削除</button></form></li>
{% else %}<li>履歴はありません</li>{% endfor %}
</ul>
</body></html>"""


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    db = get_db()
    history = db.execute("SELECT * FROM history ORDER BY id DESC LIMIT 50").fetchall()
    keyword = request.args.get("q", "")
    links = build_links(keyword) if keyword else None
    return render_template_string(PAGE, keyword=keyword, links=links, history=history)


@app.route("/search", methods=["POST"])
def search():
    keyword = (request.form.get("keyword") or "").strip()
    if keyword:
        db = get_db()
        db.execute(
            "INSERT INTO history(keyword, created_at) VALUES(?, ?)",
            (keyword, datetime.now(JST).strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
    return redirect(url_for("index", q=keyword))


@app.route("/history/<int:hid>/delete", methods=["POST"])
def delete_history(hid):
    db = get_db()
    db.execute("DELETE FROM history WHERE id = ?", (hid,))
    db.commit()
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
