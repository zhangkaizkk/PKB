"""Alembic 生成的脚本模板（alembic revision --autogenerate 会用它）。"""
${message = ""}
${up_revision = None}
${down_revision = None}
${branch_labels = None}
${depends_on = None}

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
