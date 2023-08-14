# このリポジトリについて
リサーチ作業のサポートAIをCloud Functionsにデプロイするためのリポジトリ

# 使い方
1. GCPのサービスアカウント認証情報を`google_service_account.json`としてルートに保存
2. `.env.templete`の内容をGCP上の環境変数として設定
3. `zip deploy *.py google_service_account.json requirements.txt`を実行して`deploy.zip`を生成
4. `deploy.zip`をCloud Functionsにアップロードしてデプロイ