"""empty message

Revision ID: aa78175bdf1c
Revises: 5a3aec4fce59
Create Date: 2022-01-04 20:30:03.376936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa78175bdf1c'
down_revision = '5a3aec4fce59'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('map_data_history', sa.Column('tower_id', sa.String(length=255), nullable=True))
    op.create_foreign_key(None, 'map_data_history', 'map_data', ['tower_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'map_data_history', type_='foreignkey')
    op.drop_column('map_data_history', 'tower_id')
    # ### end Alembic commands ###
