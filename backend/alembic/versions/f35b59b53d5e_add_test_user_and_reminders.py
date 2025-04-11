"""Add test user and reminders

Revision ID: f35b59b53d5e
Revises: 36db7907d5a7
Create Date: 2025-04-19 18:11:34.722518

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers, used by Alembic.
revision: str = 'f35b59b53d5e'
down_revision: Union[str, None] = '36db7907d5a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add test user and reminders."""

    # Define tables for bulk insert operations
    users_table = table('users',
                        column('id', UUID),
                        column('telegram_id', sa.String),
                        column('username', sa.String),
                        column('email', sa.String),
                        column('first_name', sa.String),
                        column('timezone', sa.String),
                        column('level', sa.Integer),
                        column('experience', sa.Integer),
                        column('streak', sa.Integer),
                        column('created_at', sa.DateTime(timezone=True)),
                        column('updated_at', sa.DateTime(timezone=True))
                        )

    reminders_table = table('reminders',
                            column('id', UUID),
                            column('user_id', UUID),
                            column('text', sa.Text),
                            column('time', sa.DateTime(timezone=True)),
                            column('status', sa.String),  # Using String instead of ENUM to avoid creation issues
                            column('removed', sa.Boolean),
                            column('notification_sent', sa.Boolean),
                            column('created_at', sa.DateTime(timezone=True)),
                            column('updated_at', sa.DateTime(timezone=True))
                            )

    # Generate a UUID for the test user
    user_id = uuid.uuid4()

    # Insert test user
    op.bulk_insert(users_table, [
        {
            'id': user_id,
            'telegram_id': '313049106',
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test User',
            'timezone': 'UTC',
            'level': 1,
            'experience': 0,
            'streak': 0,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
    ])

    # Current time for reminders
    now = datetime.now(timezone.utc)

    # Insert test reminders
    op.bulk_insert(reminders_table, [
        {
            'id': uuid.uuid4(),
            'user_id': user_id,
            'text': 'Call mom about birthday plans',
            'time': now + timedelta(hours=2),
            'status': 'ACTIVE',
            'removed': False,
            'notification_sent': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': uuid.uuid4(),
            'user_id': user_id,
            'text': 'Submit weekly report',
            'time': now - timedelta(hours=24),
            'status': 'ACTIVE',
            'removed': False,
            'notification_sent': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': uuid.uuid4(),
            'user_id': user_id,
            'text': 'Buy groceries: milk, eggs, bread',
            'time': now - timedelta(hours=6),
            'status': 'ACTIVE',
            'removed': False,
            'notification_sent': False,
            'created_at': now,
            'updated_at': now
        }
    ])


def downgrade() -> None:
    """Remove test user and associated reminders."""
    # The reminders will be automatically deleted due to the CASCADE constraint
    op.execute("DELETE FROM users WHERE telegram_id = '313049106'")
