#!/usr/bin/env bash
set -euo pipefail

SQL_FILE=${1:-}
FILES_TAR=${2:-}

if [ -z "$SQL_FILE" ] || [ -z "$FILES_TAR" ]; then
  echo "用法：./scripts/restore.sh backups/pkb-2026-10-06.sql backups/pkb-files-2026-10-06.tar.gz"
  exit 1
fi

if [ ! -f "$SQL_FILE" ]; then
  echo "✗ SQL 文件不存在：$SQL_FILE"; exit 1
fi
if [ ! -f "$FILES_TAR" ]; then
  echo "✗ 文件包不存在：$FILES_TAR"; exit 1
fi

echo "▶ 恢复 MySQL ..."
docker exec -i pkb-mysql sh -c \
  'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" pkb' < "$SQL_FILE"

echo "▶ 恢复文件目录 ..."
tar -xzf "$FILES_TAR"

echo "✓ 恢复完成"
