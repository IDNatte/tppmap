"""empty message

Revision ID: e1cb82ca5fa1
Revises: 183603cd53be
Create Date: 2022-01-02 23:34:22.934017

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1cb82ca5fa1'
down_revision = '183603cd53be'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'map_data', ['latlang'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'map_data', type_='unique')
    # ### end Alembic commands ###
