"""add IsExpedition to card

Revision ID: ef4a0e644933
Revises: 48f4320cfbbb
Create Date: 2021-01-14 12:57:35.745534

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ef4a0e644933"
down_revision = "48f4320cfbbb"
branch_labels = None
depends_on = None

COLUMN_NAME = "IsInExpedition"


def upgrade():
    op.add_column("cards", sa.Column(COLUMN_NAME, sa.Boolean()))


def downgrade():
    op.drop_column("cards", COLUMN_NAME)
