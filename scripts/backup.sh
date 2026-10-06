#!/usr/bin/env bash
set -euo pipefail

DATE=$(date +%F)
mkdir -p backups

echo "▶ 导出 MySQL ..."
docker exec pkb-mysql sh -c \
  'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers pkb' \
  > "backups/pkb-${DATE}.sql"

echo "▶ 打包文件目录 ..."
tar -czf "backups/pkb-files-${DATE}.tar.gz" data/files

echo "✓ 备份完成："
echo "   backups/pkb-${DATE}.sql"
echo "   backups/pkb-files-${DATE}.tar.gz"
