"""dev

Revision ID: 3e26d044e226
Revises: f81b37895dec
Create Date: 2024-10-27 08:45:26.473996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e26d044e226'
down_revision: Union[str, None] = 'f81b37895dec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('challenge', sa.Column('finalized_at', sa.DateTime(), nullable=True))
    op.add_column('challenge_member', sa.Column('is_winner', sa.Boolean(), nullable=False))
    op.alter_column('user', 'phone_number',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'phone_number',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.drop_column('challenge_member', 'is_winner')
    op.drop_column('challenge', 'finalized_at')
    # ### end Alembic commands ###
