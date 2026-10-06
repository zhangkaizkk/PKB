"""初始迁移 — 手动手写，包含 MySQL ngram FULLTEXT 索引。

Alembic 自动生成无法识别 `WITH PARSER ngram`，因此本文件完全手写 DDL。
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TABLE users (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          username VARCHAR(64) NOT NULL UNIQUE,
          password_hash VARCHAR(255) NOT NULL,
          created_at TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """))

    conn.execute(sa.text("""
        CREATE TABLE documents (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          public_id CHAR(26) NOT NULL UNIQUE,
          owner_id BIGINT UNSIGNED NOT NULL,
          original_name VARCHAR(512) NOT NULL,
          title VARCHAR(512) NOT NULL,
          stored_path VARCHAR(1024) NOT NULL,
          mime_type VARCHAR(255) NOT NULL,
          size_bytes BIGINT UNSIGNED NOT NULL,
          sha256 CHAR(64) NOT NULL,
          extract_status ENUM('pending','done','failed','skipped') NOT NULL DEFAULT 'pending',
          extract_error VARCHAR(1024) NULL,
          created_at TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),
          updated_at TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
          deleted_at TIMESTAMP(6) NULL,
          FULLTEXT KEY ft_documents_title (title, original_name) WITH PARSER ngram,
          KEY idx_documents_sha256 (sha256),
          KEY idx_documents_owner (owner_id),
          KEY idx_documents_created_at (created_at),
          KEY idx_documents_deleted_at (deleted_at),
          CONSTRAINT fk_documents_owner FOREIGN KEY (owner_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """))

    conn.execute(sa.text("""
        CREATE TABLE document_texts (
          document_id BIGINT UNSIGNED PRIMARY KEY,
          content LONGTEXT NOT NULL,
          FULLTEXT KEY ft_document_texts_content (content) WITH PARSER ngram,
          CONSTRAINT fk_document_texts_doc FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """))

    conn.execute(sa.text("""
        CREATE TABLE tags (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(64) NOT NULL UNIQUE,
          color VARCHAR(16) DEFAULT NULL,
          created_at TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """))

    conn.execute(sa.text("""
        CREATE TABLE document_tags (
          document_id BIGINT UNSIGNED NOT NULL,
          tag_id BIGINT UNSIGNED NOT NULL,
          PRIMARY KEY (document_id, tag_id),
          CONSTRAINT fk_dt_doc FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
          CONSTRAINT fk_dt_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """))

    conn.execute(sa.text("""
        CREATE TABLE settings (
          `key` VARCHAR(128) PRIMARY KEY,
          `value` JSON NOT NULL,
          updated_at TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS document_tags"))
    conn.execute(sa.text("DROP TABLE IF EXISTS document_texts"))
    conn.execute(sa.text("DROP TABLE IF EXISTS documents"))
    conn.execute(sa.text("DROP TABLE IF EXISTS tags"))
    conn.execute(sa.text("DROP TABLE IF EXISTS users"))
    conn.execute(sa.text("DROP TABLE IF EXISTS settings"))
