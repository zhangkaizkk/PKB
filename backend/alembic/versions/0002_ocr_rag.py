"""OCR + RAG 扩展迁移 — 新增 qa_history 表 + documents 表增加 ocr/indexed 字段。

Revision ID: 0002_ocr_rag
Revises: 0001_init
Create Date: 2026-10-07 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_ocr_rag"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # --- 1. documents 表增加 OCR / 索引字段 ---
    conn.execute(sa.text("""
        ALTER TABLE documents
          ADD COLUMN ocr_status ENUM('pending','processing','done','failed','skipped')
            NOT NULL DEFAULT 'skipped' AFTER extract_status,
          ADD COLUMN ocr_error VARCHAR(1024) NULL AFTER ocr_status,
          ADD COLUMN indexed_at TIMESTAMP(6) NULL AFTER ocr_error,
          ADD KEY idx_documents_ocr_status (ocr_status),
          ADD KEY idx_documents_indexed_at (indexed_at)
    """))

    # --- 2. 新建 qa_history 表 ---
    conn.execute(sa.text("""
        CREATE TABLE qa_history (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          owner_id BIGINT UNSIGNED NOT NULL,
          question TEXT NOT NULL,
          answer LONGTEXT NOT NULL,
          citations JSON DEFAULT NULL,
          chat_model VARCHAR(128) DEFAULT NULL,
          embed_model VARCHAR(128) DEFAULT NULL,
          prompt_tokens INT UNSIGNED DEFAULT NULL,
          completion_tokens INT UNSIGNED DEFAULT NULL,
          latency_ms INT UNSIGNED DEFAULT NULL,
          created_at TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),
          KEY idx_qa_owner_created (owner_id, created_at),
          CONSTRAINT fk_qa_owner FOREIGN KEY (owner_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("DROP TABLE IF EXISTS qa_history"))

    conn.execute(sa.text("""
        ALTER TABLE documents
          DROP INDEX idx_documents_ocr_status,
          DROP INDEX idx_documents_indexed_at,
          DROP COLUMN indexed_at,
          DROP COLUMN ocr_error,
          DROP COLUMN ocr_status
    """))
