"""empty message

Revision ID: c28223b2b28a
Revises: 85cd83eed5e9
Create Date: 2022-01-19 11:43:24.934304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c28223b2b28a'
down_revision = '85cd83eed5e9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('map_data', sa.Column('tower_name', sa.String(length=200), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('map_data', 'tower_name')
    # ### end Alembic commands ###
