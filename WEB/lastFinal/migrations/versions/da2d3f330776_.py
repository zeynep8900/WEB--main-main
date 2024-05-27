"""empty message

Revision ID: da2d3f330776
Revises: 70a0d841dd0f
Create Date: 2024-05-26 22:57:03.756728

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da2d3f330776'
down_revision = '70a0d841dd0f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('city', schema=None) as batch_op:
        batch_op.drop_column('transportation')
        batch_op.drop_column('bars')
        batch_op.drop_column('tourist_attractions')
        batch_op.drop_column('restaurants')
        batch_op.drop_column('accommodation')
        batch_op.drop_column('places_of_interest')
        batch_op.drop_column('cultural_places')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('city', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cultural_places', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('places_of_interest', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('accommodation', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('restaurants', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('tourist_attractions', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('bars', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('transportation', sa.TEXT(), nullable=True))

    # ### end Alembic commands ###