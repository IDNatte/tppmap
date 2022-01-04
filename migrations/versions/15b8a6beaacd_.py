"""empty message

Revision ID: 15b8a6beaacd
Revises: aa78175bdf1c
Create Date: 2022-01-04 22:17:38.711998

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15b8a6beaacd'
down_revision = 'aa78175bdf1c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('map_data_history', sa.Column('created_on', sa.DateTime(), nullable=True))
    op.add_column('map_data_history', sa.Column('updated_on', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('map_data_history', 'updated_on')
    op.drop_column('map_data_history', 'created_on')
    # ### end Alembic commands ###
