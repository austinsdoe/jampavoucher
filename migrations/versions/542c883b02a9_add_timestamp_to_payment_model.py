"""Add timestamp to Payment model

Revision ID: 542c883b02a9
Revises: f7664cefc73a
Create Date: 2025-04-02 21:57:25.802590

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '542c883b02a9'
down_revision = 'f7664cefc73a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mikro_tik_router', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hotspot_enabled', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mikro_tik_router', schema=None) as batch_op:
        batch_op.drop_column('hotspot_enabled')

    # ### end Alembic commands ###
