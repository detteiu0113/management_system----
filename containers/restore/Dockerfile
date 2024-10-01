# ベースイメージとしてPostgreSQLを使用
FROM postgres:15.2

# 必要なファイルをコピー
COPY ./containers/restore/restore.sh /usr/local/bin/restore.sh

# スクリプトに実行権限を付与
RUN chmod +x /usr/local/bin/restore.sh

# デフォルトのコマンドを設定
CMD ["sh", "-c", "/usr/local/bin/restore.sh"]
