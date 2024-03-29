# このリポジトリについて

リサーチ作業のサポート AI を Cloud Functions にデプロイするためのリポジトリ

# GCF へのデプロイ方法

1. GCP のサービスアカウント認証情報を`google_service_account.json`としてルートに保存
2. `.env.templete`の内容を GCP 上の環境変数として設定
3. GCP の設定にて、ランタイムを`Python3.9`、エントリポイントを`on_http_trigger`に設定
4. 次を実行して`deploy.zip`を生成（-j オプションは src 配下のファイルを同一ディレクトリに展開するため）
   ```shell
   zip -j deploy src/*.py google_service_account.json requirements.txt sheet_info.yml
   ```
5. `deploy.zip`を Cloud Functions にアップロードしてデプロイ

# ローカルでのテスト実行

### 認証情報やパラメータの設定

1. GCP のサービスアカウント認証情報を`google_service_account.json`としてルートに保存
2. `.env.templete`をコピーした`.env`に認証情報等を入力
3. `test_sheet.template.yml`をコピーした`test_sheet.yml`に処理対象のスプシの情報を入力

### 仮想環境立ち上げ

```shell
docker-compose up -d
```

### スクリプトの実行方法

```shell
docker-compose exec python3 python3 src/main.py
```

### コンテナ再構築

`requirements.txt`、`.env`、`Dockerfile`、`docker-compose.yml`を変更したときは、次のコマンドによりコンテナを再構築する。

```shell
docker-compose down
docker-compose build --no-cache #少し時間がかかる
docker-compose up -d
```
