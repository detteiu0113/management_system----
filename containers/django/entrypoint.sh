#!/bin/sh
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py createusers

# 環境変数設定スクリプト作成
printenv | awk '{print "export " $1}' > /root/env.sh

# cron 起動
service cron start

# 環境変数のDEBUGの値がTrueの時はrunserverを、Falseの時はgunicornを実行します
# シェルスクリプトでは`[`と`$DEBUG`、`1`と`]`の間にスペースを一つ空けておかないと[]内の式を認識できないので注意
if [ $DEBUG = 1 ]; then
    python manage.py runserver 0.0.0.0:8000
else
    daphne -b 0.0.0.0 -p 8000 management_system.asgi:application
fi
