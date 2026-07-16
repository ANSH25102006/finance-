"""rename_transaction_columns

Revision ID: 6abd611ade8e
Revises: abe4a2f18302
Create Date: 2026-07-16 16:46:32.709550+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers used by Alembic.
revision: str = '6abd611ade8e'
down_revision: Union[str, None] = 'abe4a2f18302'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename columns
    op.alter_column('transactions', 'title', new_column_name='description')
    op.alter_column('transactions', 'type', new_column_name='transaction_type')
    
    # Drop old index before renaming the date column
    op.drop_index('ix_transactions_date', table_name='transactions')
    op.alter_column('transactions', 'date', new_column_name='transaction_date')
    # Create new index on renamed column
    op.create_index(op.f('ix_transactions_transaction_date'), 'transactions', ['transaction_date'], unique=False)
    
    op.alter_column('transactions', 'amount',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('transactions', 'amount',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
    
    op.drop_index('ix_transactions_transaction_date', table_name='transactions')
    op.alter_column('transactions', 'transaction_date', new_column_name='date')
    op.create_index('ix_transactions_date', 'transactions', ['date'], unique=False)
    
    op.alter_column('transactions', 'transaction_type', new_column_name='type')
    op.alter_column('transactions', 'description', new_column_name='title')


