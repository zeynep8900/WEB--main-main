"""Add rating column to comment table

Revision ID: 7f9ea0efd0e3
Revises: afa5f85f8366
Create Date: 2024-05-25 22:45:18.242773

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f9ea0efd0e3'
down_revision = 'afa5f85f8366'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rating', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.drop_column('rating')

    # ### end Alembic commands ###