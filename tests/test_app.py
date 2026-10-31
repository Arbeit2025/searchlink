import os
import sys
import tempfile
import unittest
from urllib.parse import quote_plus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["SEARCHLINK_DB"] = _tmp.name

import app as app_module  # noqa: E402


class SearchLinkTest(unittest.TestCase):
    def setUp(self):
        app_module.init_db()
        self.client = app_module.app.test_client()
        with app_module.app.app_context():
            conn = app_module.get_db()
            conn.execute("DELETE FROM history")
            conn.commit()

    def test_healthz(self):
        res = self.client.get("/healthz")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "ok")

    def test_build_links_shops(self):
        links = dict(app_module.build_links("イヤホン"))
        self.assertEqual(len(links), 5)
        for name in ["Amazon.co.jp", "楽天市場", "Yahoo!ショッピング", "ヨドバシ.com", "メルカリ"]:
            self.assertIn(name, links)

    def test_links_encoded(self):
        kw = "ワイヤレス イヤホン"
        links = dict(app_module.build_links(kw))
        self.assertIn(quote_plus(kw), links["Amazon.co.jp"])
        self.assertIn(quote_plus(kw), links["メルカリ"])
        self.assertNotIn("ワイヤレス イヤホン", links["Amazon.co.jp"])

    def test_search_saves_history(self):
        self.client.post("/search", data={"keyword": "掃除機"})
        with app_module.app.app_context():
            conn = app_module.get_db()
            rows = conn.execute("SELECT keyword FROM history").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["keyword"], "掃除機")

    def test_history_redisplay(self):
        self.client.post("/search", data={"keyword": "掃除機"})
        body = self.client.get("/?q=掃除機").get_data(as_text=True)
        self.assertIn("amazon.co.jp", body)
        self.assertIn("rakuten.co.jp", body)

    def test_delete_history(self):
        self.client.post("/search", data={"keyword": "削除対象"})
        with app_module.app.app_context():
            conn = app_module.get_db()
            hid = conn.execute("SELECT id FROM history").fetchone()["id"]
        self.client.post(f"/history/{hid}/delete")
        with app_module.app.app_context():
            conn = app_module.get_db()
            self.assertEqual(conn.execute("SELECT COUNT(*) AS c FROM history").fetchone()["c"], 0)

    def test_index_ok(self):
        self.assertEqual(self.client.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
