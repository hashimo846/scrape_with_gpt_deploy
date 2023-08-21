# このリポジトリについて
リサーチ作業のサポートAIをCloud Functionsにデプロイするためのリポジトリ

# GCFへのデプロイ方法
1. GCPのサービスアカウント認証情報を`google_service_account.json`としてルートに保存
2. `.env.templete`の内容をGCP上の環境変数として設定
3. `zip deploy *.py google_service_account.json requirements.txt`を実行して`deploy.zip`を生成
4. `deploy.zip`をCloud Functionsにアップロードしてデプロイ

# ローカルでの実行方法
### 環境変数とAPIキーの設定
1. GCPのサービスアカウント認証情報を`google_service_account.json`としてルートに保存
2. `.env.templete`をコピーした`.env`に認証情報等を入力

### 仮想環境立ち上げ
```shell
docker-compose up -d
```
### スクリプトの実行方法
```shell
docker-compose exec scrape_with_gpt_deploy python3 main.py
```

### コンテナ再構築
`requirements.txt`、`.env`、`Dockerfile`、`docker-compose.yml`を変更したときは、次のコマンドにより
```shell
docker-compose down
docker-compose build --no-cache #少し時間がかかる
docker-compose up -d
```