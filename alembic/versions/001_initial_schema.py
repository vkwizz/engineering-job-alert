"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-12 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Companies
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('canonical_name', sa.String(), nullable=False),
        sa.Column('normalized_name', sa.String(), nullable=False),
        sa.Column('tier', sa.Integer(), nullable=True),
        sa.Column('company_score', sa.Integer(), server_default='0'),
        sa.Column('preferred', sa.Boolean(), server_default='false'),
        sa.Column('blocked', sa.Boolean(), server_default='false'),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('career_url', sa.String(), nullable=True),
        sa.Column('aliases_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_companies_canonical_name', 'companies', ['canonical_name'], unique=True)
    op.create_index('ix_companies_normalized_name', 'companies', ['normalized_name'])

    # 2. Jobs
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('canonical_key', sa.String(), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('normalized_title', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('remote_type', sa.String(), nullable=True),
        sa.Column('employment_type', sa.String(), nullable=True),
        sa.Column('role_family', sa.String(), nullable=True),
        sa.Column('technical_domain', sa.String(), nullable=True),
        sa.Column('experience_min', sa.Integer(), nullable=True),
        sa.Column('experience_max', sa.Integer(), nullable=True),
        sa.Column('graduation_years_json', sa.JSON(), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_description', sa.String(), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('apply_url', sa.String(), nullable=True),
        sa.Column('company_career_url', sa.String(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), server_default='new'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_jobs_canonical_key', 'jobs', ['canonical_key'], unique=True)
    op.create_index('ix_jobs_normalized_title', 'jobs', ['normalized_title'])

    # 3. Job Sources
    op.create_table(
        'job_sources',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_job_id', sa.String(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('source_company_name', sa.String(), nullable=True),
        sa.Column('source_raw_json', sa.JSON(), nullable=True),
        sa.Column('source_first_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_confidence', sa.Integer(), server_default='50'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 4. Job Analysis
    op.create_table(
        'job_analysis',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('student_eligible', sa.Boolean(), nullable=True),
        sa.Column('is_internship', sa.Boolean(), nullable=True),
        sa.Column('is_graduate_role', sa.Boolean(), nullable=True),
        sa.Column('is_target_technical_role', sa.Boolean(), nullable=True),
        sa.Column('is_excluded_role', sa.Boolean(), nullable=True),
        sa.Column('technical_domain', sa.String(), nullable=True),
        sa.Column('role_family', sa.String(), nullable=True),
        sa.Column('company_fit_score', sa.Float(), server_default='0.0'),
        sa.Column('technical_fit_score', sa.Float(), server_default='0.0'),
        sa.Column('student_fit_score', sa.Float(), server_default='0.0'),
        sa.Column('location_fit_score', sa.Float(), server_default='0.0'),
        sa.Column('freshness_score', sa.Float(), server_default='0.0'),
        sa.Column('source_score', sa.Float(), server_default='0.0'),
        sa.Column('final_score', sa.Float(), server_default='0.0'),
        sa.Column('ai_reasoning_summary', sa.String(), nullable=True),
        sa.Column('ai_model', sa.String(), nullable=True),
        sa.Column('ai_classified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('classifier_version', sa.String(), nullable=True),
    )

    # 5. Alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_key', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='sent'),
        sa.Column('error_message', sa.String(), nullable=True),
    )
    op.create_index('ix_alerts_notification_key', 'alerts', ['notification_key'], unique=True)

    # 6. Runs
    op.create_table(
        'runs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), server_default='running'),
        sa.Column('jobs_fetched', sa.Integer(), server_default='0'),
        sa.Column('jobs_normalized', sa.Integer(), server_default='0'),
        sa.Column('jobs_deduplicated', sa.Integer(), server_default='0'),
        sa.Column('jobs_rejected', sa.Integer(), server_default='0'),
        sa.Column('jobs_ai_classified', sa.Integer(), server_default='0'),
        sa.Column('jobs_alerted', sa.Integer(), server_default='0'),
        sa.Column('error_summary', sa.String(), nullable=True),
        sa.Column('run_metadata_json', sa.JSON(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('runs')
    op.drop_table('alerts')
    op.drop_table('job_analysis')
    op.drop_table('job_sources')
    op.drop_table('jobs')
    op.drop_table('companies')
