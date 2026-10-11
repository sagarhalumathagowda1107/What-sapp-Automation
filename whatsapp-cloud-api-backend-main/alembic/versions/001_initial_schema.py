"""Initial schema creation for WhatsApp Weekly PDF Report Automation System

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-11 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. recipients table
    op.create_table(
        'recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone_number', sa.String(length=30), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('opted_in', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('opted_in_at', sa.DateTime(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='Asia/Kolkata'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipients_id'), 'recipients', ['id'], unique=False)
    op.create_index(op.f('ix_recipients_phone_number'), 'recipients', ['phone_number'], unique=True)

    # 2. schedules table
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cron_expression', sa.String(length=100), nullable=True),
        sa.Column('day_of_week', sa.String(length=20), nullable=False, server_default='mon'),
        sa.Column('hour', sa.Integer(), nullable=False, server_default='9'),
        sa.Column('minute', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='Asia/Kolkata'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedules_id'), 'schedules', ['id'], unique=False)

    # 3. reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('reporting_period_start', sa.DateTime(), nullable=False),
        sa.Column('reporting_period_end', sa.DateTime(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('media_id', sa.String(length=100), nullable=True),
        sa.Column('metrics_data', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='generated'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)
    op.create_index(op.f('ix_reports_media_id'), 'reports', ['media_id'], unique=False)
    op.create_index(op.f('ix_reports_status'), 'reports', ['status'], unique=False)

    # 4. message_delivery_logs table
    op.create_table(
        'message_delivery_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=True),
        sa.Column('recipient_id', sa.Integer(), nullable=True),
        sa.Column('phone_number', sa.String(length=30), nullable=False),
        sa.Column('message_id', sa.String(length=150), nullable=True),
        sa.Column('delivery_channel', sa.String(length=50), nullable=False, server_default='whatsapp_cloud_api'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('meta_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['recipient_id'], ['recipients.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_delivery_logs_id'), 'message_delivery_logs', ['id'], unique=False)
    op.create_index(op.f('ix_message_delivery_logs_message_id'), 'message_delivery_logs', ['message_id'], unique=False)
    op.create_index(op.f('ix_message_delivery_logs_phone_number'), 'message_delivery_logs', ['phone_number'], unique=False)
    op.create_index(op.f('ix_message_delivery_logs_recipient_id'), 'message_delivery_logs', ['recipient_id'], unique=False)
    op.create_index(op.f('ix_message_delivery_logs_report_id'), 'message_delivery_logs', ['report_id'], unique=False)
    op.create_index(op.f('ix_message_delivery_logs_status'), 'message_delivery_logs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('message_delivery_logs')
    op.drop_table('reports')
    op.drop_table('schedules')
    op.drop_table('recipients')
