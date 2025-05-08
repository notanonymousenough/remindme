"""Neuro Image Rate

Revision ID: 3ba879bcab3c
Revises: e69e2f39be18
Create Date: 2025-04-25 20:00:58.907959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ba879bcab3c'
down_revision: Union[str, None] = 'e69e2f39be18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type first
    image_rate_enum = sa.Enum('GOOD', 'NEUTRAL', 'BAD', name='imagerate')
    image_rate_enum.create(op.get_bind())

    # Then add the column using the enum type
    op.add_column('neuro_images', sa.Column('rate', image_rate_enum, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the column first
    op.drop_column('neuro_images', 'rate')

    # Then drop the enum type
    sa.Enum(name='imagerate').drop(op.get_bind())
