"""ingredient embeddings

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ingredients", sa.Column("embedding", Vector(384), nullable=True))


def downgrade() -> None:
    op.drop_column("ingredients", "embedding")
