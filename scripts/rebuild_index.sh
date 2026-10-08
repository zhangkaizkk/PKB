#!/usr/bin/env bash
set -e

TOKEN=${PKB_TOKEN:?请先设置 PKB_TOKEN 环境变量}
API=${PKB_API:-http://localhost:8000}

echo "重建全部 RAG 索引..."
curl -s -X POST "$API/api/rag/reindex" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
echo ""
echo "重建完成，可通过 $API/api/rag/stats 查看进度"
