#!/bin/sh

# 環境変数を設定
. /root/env.sh

# 定期実行したい処理
python ../code/manage.py update_grade 1>/proc/1/fd/1 2>/proc/1/fd/2