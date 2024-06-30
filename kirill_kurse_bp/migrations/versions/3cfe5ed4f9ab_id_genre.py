"""id_genre

Revision ID: 3cfe5ed4f9ab
Revises: bbda0c98e598
Create Date: 2024-06-20 18:42:08.083470

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3cfe5ed4f9ab'
down_revision = 'bbda0c98e598'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(length=64),
               nullable=False)

    with op.batch_alter_table('genre_books', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_genre', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'genres', ['id_genre'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('genre_books', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('id_genre')

    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(length=64),
               nullable=True)

    # ### end Alembic commands ###