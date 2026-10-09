"""按用户隔离 — tags 表加 owner_id，去重查询按 owner 过滤。

Revision ID: 0003_owner_scope
Revises: 0002_ocr_rag
Create Date: 2026-10-09 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_owner_scope"
down_revision = "0002_ocr_rag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # --- tags 表：加 owner_id + 删旧唯一约束 + 加新复合唯一约束 ---
    conn.execute(sa.text("""
        ALTER TABLE tags
          ADD COLUMN owner_id BIGINT UNSIGNED NOT NULL DEFAULT 1 AFTER id,
          DROP INDEX name,
          ADD CONSTRAINT uq_tags_owner_name UNIQUE (owner_id, name),
          ADD CONSTRAINT fk_tags_owner FOREIGN KEY (owner_id) REFERENCES users(id)
    """))

    # --- documents 去重索引：加 owner_id（保留原 sha256 索引，新增复合索引）---
    conn.execute(sa.text("""
        ALTER TABLE documents
          ADD KEY idx_documents_owner_sha256 (owner_id, sha256)
    """))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        ALTER TABLE documents
          DROP INDEX idx_documents_owner_sha256
    """))

    conn.execute(sa.text("""
        ALTER TABLE tags
          DROP FOREIGN KEY fk_tags_owner,
          DROP INDEX uq_tags_owner_name,
          ADD UNIQUE KEY name (name),
          DROP COLUMN owner_id
    """))
