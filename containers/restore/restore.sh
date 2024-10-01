#!/bin/bash

# 最新のバックアップファイルを見つける
latest_backup=$(ls -1 /backup/*.dump | tail -n 1)

# バックアップファイルが存在するか確認
if [ -z "$latest_backup" ]; then
  echo "No backup file found!"
  exit 1
fi

# データベースを復元
echo "Restoring database from $latest_backup"
PGPASSWORD=$POSTGRES_PASSWORD pg_restore -h postgres -U $POSTGRES_USER -d $POSTGRES_NAME -c $latest_backup

echo "Restore completed"
