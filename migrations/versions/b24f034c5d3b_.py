"""empty message

Revision ID: b24f034c5d3b
Revises: 98bcbd052dec
Create Date: 2018-05-14 14:58:38.206348

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b24f034c5d3b'
down_revision = '98bcbd052dec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('i_pinfo', sa.Column('countrycode', sa.String(length=3), nullable=True))
    op.add_column('i_pinfo', sa.Column('countryname', sa.String(length=128), nullable=True))
    op.create_index(op.f('ix_i_pinfo_countrycode'), 'i_pinfo', ['countrycode'], unique=False)
    op.create_index(op.f('ix_i_pinfo_countryname'), 'i_pinfo', ['countryname'], unique=False)
    op.drop_index('ix_i_pinfo_origincountry', table_name='i_pinfo')
    op.drop_column('i_pinfo', 'origincountry')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('i_pinfo', sa.Column('origincountry', sa.VARCHAR(length=128), nullable=True))
    op.create_index('ix_i_pinfo_origincountry', 'i_pinfo', ['origincountry'], unique=False)
    op.drop_index(op.f('ix_i_pinfo_countryname'), table_name='i_pinfo')
    op.drop_index(op.f('ix_i_pinfo_countrycode'), table_name='i_pinfo')
    op.drop_column('i_pinfo', 'countryname')
    op.drop_column('i_pinfo', 'countrycode')
    # ### end Alembic commands ###