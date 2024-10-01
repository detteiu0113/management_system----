# PostgreSQLのイメージを指定
# 今回は15.2を使用
FROM postgres:15.2

# 初期化用のSQLスクリプトをコンテナにコピー
COPY containers/postgres/init.sql /docker-entrypoint-initdb.d/