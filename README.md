# みはる（LLM Monitor Apps）

**みはる** は、FastAPI と HTMX で作られた、ローカル LLM サーバーの簡易監視 Web アプリです。
登録したマシン（IP:ポート）に問い合わせ、**今オンラインか／どのモデルが立っているか**を一覧表示します。

> 研究室での運用（ネットワーク構成・デプロイ手順）は [docs/運用ガイド.md](docs/運用ガイド.md) を参照してください。

## できること

- 監視したいマシン（IP:ポート）を Web UI から登録する
- 各マシンの `/v1/models` に問い合わせ、**オンライン判定とモデル名取得を同時に行う**
- **20秒ごとに自動更新**（画面を開いておけば常に最新）＋手動更新ボタン
- ネットワーク（AI2 / AI3）ごとにグループ分けして表示
- データを `endpoints.json` に保存する

## 稼働判定の仕組み

モデル名の取得を、そのままオンライン判定に使います。

1. `http://<ip>:<port>/v1/models` に問い合わせる（取れなければ `http://<ip>:<port>/props`）
2. **モデル名が取れた** → `online` ＋ そのモデル名を表示
3. **応答がない/エラー** → `offline`（モデル欄は「—」）

「モデルが立っている ⟹ サーバーは起動している」ため、`/v1/models` 一本で
「生きているか」と「何が立っているか」を同時に判定できます（`/health` は使いません）。

- 全マシンのチェックは**並行実行**（オフライン機で待たされない。タイムアウト3秒）
- vLLM を認証あり（`--api-key`）で立てる運用は現状未対応（将来課題）

## 使用技術

- Python / UV / FastAPI / HTMX / Uvicorn

補足：画面はテンプレート内のインライン CSS で構成されています（Tailwind は未導入）。

## ディレクトリ構成

```text
.
├── app
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── routers
│   │   └── endpoints.py
│   ├── services
│   │   └── llm_detector.py
│   └── templates
│       └── index.html
├── docs
│   └── 運用ガイド.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── endpoints.json
├── pyproject.toml
└── uv.lock
```

## ローカル起動

### 前提条件

- `uv` がインストールされていること
- Python 3.10 以上が使えること

### セットアップ・起動

```bash
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`uv` のキャッシュ権限でエラーになる場合は、書き込み可能なディレクトリを指定してください。

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync
UV_CACHE_DIR=/tmp/uv-cache uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

ブラウザで `http://127.0.0.1:8000/` を開きます。

## Docker で起動する

```bash
docker compose up --build        # フォアグラウンド
docker compose up --build -d     # バックグラウンド
docker compose down              # 停止
```

`docker-compose.yml` はホストの `endpoints.json` をコンテナにバインドマウントしているため、
コンテナを作り直しても登録内容は保持されます。`restart: unless-stopped` により再起動後も自動で立ち上がります。

> 閉域ネットワーク（インターネット非接続）へのデプロイは `git clone` や `--build` が使えません。
> イメージを別環境でビルドして持ち込む手順は [docs/運用ガイド.md](docs/運用ガイド.md) を参照してください。

## 使い方

1. トップページを開く
2. `マシン名` `ネットワーク(AI2/AI3)` `IPアドレス` `ポート` を入力して登録する
   - 登録するのは「マシンの住所」です。モデル名は登録不要（自動で検出されます）
3. 一覧は AI2 / AI3 ごとにグループ表示され、各マシンの状態とモデル名が出ます
4. 更新操作
   - **自動**：20秒ごとに全台の状態を自動で取り直します
   - **今すぐ更新**：全台をすぐに取り直す
   - 各行の **更新**：そのマシンだけ取り直す
   - **削除**：登録を削除する

## データ保存

- 登録データはリポジトリ直下の `endpoints.json`（JSON ファイル）に保存されます
- データベースは使っていません。削除・更新は即時反映されます

## API エンドポイント

- `GET /` : 画面表示
- `GET /api/endpoints` : 一覧取得（JSON。HTMXリクエスト時はHTML断片）
- `GET /api/endpoints/refresh` : 全台を再チェックしてHTML描画（自動更新／今すぐ更新が使用）
- `POST /api/endpoints` : マシン追加
- `GET /api/endpoints/{id}` : 詳細取得
- `PUT /api/endpoints/{id}` : 更新
- `DELETE /api/endpoints/{id}` : 削除
- `POST /api/endpoints/{id}/ping` : 1台を再チェック（状態＋モデル名を更新）
- `POST /api/endpoints/ping-all` : 全台を再チェック

## 実装メモ

- `api_key` はデータ項目としては残していますが、現状の稼働確認には使っていません（UIの入力欄は廃止）
- `HEAD /` には対応していないため、`curl -I` では `405 Method Not Allowed` が返ります

## 今後の改善候補

- 認証あり（`--api-key`）vLLM への対応（APIキーを Bearer で付与）
- ネットワークの自動スキャン（登録不要で稼働機を自動発見）
- GPU種別・VRAM の表示
- Tailwind の導入 / テスト追加 / Docker イメージの軽量化
