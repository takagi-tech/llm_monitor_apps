# LLM Monitor Apps

FastAPI と HTMX で作られた、ローカル LLM サーバーの簡易監視 Web アプリです。
登録したエンドポイントに対して疎通確認を行い、モデル名を取得して一覧表示できます。

## できること

- LLM エンドポイントを Web UI から登録する
- `/health` へのリクエストでオンライン状態を確認する
- `/v1/models` または `/props` からモデル名を取得する
- 登録済みエンドポイントを一覧表示・削除する
- データを `endpoints.json` に保存する

## 想定している LLM サーバー

このアプリは、次のような HTTP エンドポイントを持つサーバーを想定しています。

- `GET /health`
- `GET /v1/models`
- `GET /props`

実装上は、モデル名の取得時に以下の順で問い合わせます。

1. `http://<ip>:<port>/v1/models`
2. `http://<ip>:<port>/props`

## 使用技術

- Python
- UV
- FastAPI
- HTMX
- Uvicorn

補足:
画面は Tailwind ではなく、現状はテンプレート内のインライン CSS で構成されています。

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

### セットアップ

```bash
uv sync
```

環境によって `uv` の標準キャッシュディレクトリに書き込めない場合があります。
その場合は、書き込み可能なディレクトリを `UV_CACHE_DIR` に指定してください。

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync
```

### 起動

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`uv` のキャッシュ権限でエラーになる場合はこちらを使ってください。

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

ブラウザで以下を開きます。

- `http://127.0.0.1:8000/`
- `http://localhost:8000/`

## Docker で起動する

### 前提条件

- Docker がインストールされていること
- Docker Compose が使えること

### 起動

```bash
docker compose up --build
```

バックグラウンドで起動する場合はこちらです。

```bash
docker compose up --build -d
```

ブラウザで以下を開きます。

- `http://127.0.0.1:8000/`
- `http://localhost:8000/`

### 停止

```bash
docker compose down
```

### データ永続化

`docker-compose.yml` では、ホスト側の `endpoints.json` をコンテナ内の `/app/endpoints.json` にバインドマウントしています。
そのため、コンテナを作り直しても登録済みエンドポイントは保持されます。

## 使い方

1. トップページを開く
2. `名前` `IPアドレス` `ポート` を入力して追加する
3. 必要に応じて以下の操作を行う

- `Ping`: `/health` にアクセスして状態を更新
- `モデル取得`: `/v1/models` または `/props` からモデル名を取得
- `削除`: 登録済みエンドポイントを削除

エンドポイント登録直後にも、モデル名の自動取得を試みます。

## データ保存

登録したエンドポイントは、リポジトリ直下の [endpoints.json](/mnt/c/users/takagi/documents/mac用ディレクトリ/study/llm_monitor_apps/endpoints.json) に保存されます。

- データベースは使っていません
- 永続化は JSON ファイルベースです
- 削除や更新はこのファイルに即時反映されます

## API エンドポイント

主な API は以下です。

- `GET /` : 画面表示
- `GET /api/endpoints` : エンドポイント一覧取得
- `POST /api/endpoints` : エンドポイント追加
- `GET /api/endpoints/{id}` : エンドポイント詳細取得
- `PUT /api/endpoints/{id}` : エンドポイント更新
- `DELETE /api/endpoints/{id}` : エンドポイント削除
- `POST /api/endpoints/{id}/ping` : ヘルスチェック実行
- `GET /api/endpoints/{id}/model` : モデル名取得

## 実装メモ

- `api_key` フィールドはありますが、現状の疎通確認やモデル取得には使っていません
- `/health` を持たないサーバーは `Ping` で `offline` になります
- `HEAD /` には対応していないため、`curl -I` では `405 Method Not Allowed` が返ります

## トラブルシュート

### ページを開けない

次を確認してください。

- サーバーが起動中か
- `8000` 番ポートが他プロセスと競合していないか
- WSL やコンテナ内で起動している場合、ブラウザから到達できる環境で起動しているか

### `uv` がキャッシュ書き込みで失敗する

一時ディレクトリを明示してください。

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker ビルドが失敗する

次を確認してください。

- Docker デーモンが起動しているか
- `docker compose` が使えるか
- 社内ネットワークやプロキシの制限で Python パッケージ取得に失敗していないか

## 今後の改善候補

- Tailwind の導入
- API キー付きエンドポイントへの対応
- 定期ポーリングによる自動監視
- テスト追加
- Docker イメージの軽量化
