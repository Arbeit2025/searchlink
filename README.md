# 検索リンク集（searchlink）

キーワードを1回入れるだけで、Amazon.co.jp・楽天市場・Yahoo!ショッピング・ヨドバシ.com・メルカリの検索結果へのリンクを一括生成する小さなツールです。各サイトを行き来して同じ語を打ち直す手間を省きます。

## 使い方

1. キーワードを入力して「リンクを作る」を押します。
2. 5サイト分の検索リンクが一覧表示されます。価格・在庫・送料はリンク先で確認してください。
3. 検索したキーワードは履歴に残ります（SQLite、環境変数 `SEARCHLINK_DB` でパス変更可）。履歴のキーワードを押すとリンクを再表示でき、不要な履歴は削除できます。

## ローカル実行

```bash
pip install -r requirements.txt
python app.py
# http://localhost:5000
```

## テスト

```bash
python -m unittest discover -s tests
```

## Render へのデプロイ

`render.yaml` 同梱。無料プラン（free）の Web Service としてデプロイできます（healthCheckPath: `/healthz`）。

## 制限事項（正直なところ）

- このツールはリンクを生成するだけです。価格比較や在庫チェックは行いません（各サイトの検索仕様に依存します）。
- 各サイトの URL 仕様が変わるとリンクが正しく動かなくなる可能性があります。その場合は `app.py` の `build_links` の修正が必要です。
- ログイン機能はありません。Render 無料プランでは SQLite の履歴が再デプロイ等で消える場合があります。

## ライセンス

MIT License
