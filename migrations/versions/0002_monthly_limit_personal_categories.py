"""Add monthly limits and personal categories.

Revision ID: 0002_limits_categories
Revises: 0001_legacy_schema
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_limits_categories"
down_revision = "0001_legacy_schema"
branch_labels = None
depends_on = None


def _names(items):
    return {item.get("name") for item in items if item.get("name")}


def upgrade():
    inspector = sa.inspect(op.get_bind())
    user_columns = {column["name"] for column in inspector.get_columns("usuarios")}
    if "monthly_limit" not in user_columns:
        op.add_column(
            "usuarios",
            sa.Column("monthly_limit", sa.Numeric(precision=12, scale=2), nullable=True),
        )

    inspector = sa.inspect(op.get_bind())
    category_columns = {column["name"] for column in inspector.get_columns("categorias")}
    inspector = sa.inspect(op.get_bind())
    foreign_keys = inspector.get_foreign_keys("categorias")
    has_owner_foreign_key = any(
        foreign_key.get("constrained_columns") == ["user_id"]
        and foreign_key.get("referred_table") == "usuarios"
        for foreign_key in foreign_keys
    )
    inspector = sa.inspect(op.get_bind())
    unique_names = _names(inspector.get_unique_constraints("categorias"))
    unique_indexes = _names(
        index for index in inspector.get_indexes("categorias") if index.get("unique")
    )
    with op.batch_alter_table("categorias") as batch_op:
        if "user_id" not in category_columns:
            batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        if not has_owner_foreign_key:
            batch_op.create_foreign_key(
                "fk_categorias_usuario",
                "usuarios",
                ["user_id"],
                ["id"],
                ondelete="CASCADE",
            )
        if "uq_categoria_user_nome_tipo" not in unique_names | unique_indexes:
            batch_op.create_unique_constraint(
                "uq_categoria_user_nome_tipo",
                ["user_id", "name", "kind"],
            )
        if "uq_categoria_nome_tipo" in unique_names:
            batch_op.drop_constraint("uq_categoria_nome_tipo", type_="unique")
        elif "uq_categoria_nome_tipo" in unique_indexes:
            batch_op.drop_index("uq_categoria_nome_tipo")


def downgrade():
    raise RuntimeError(
        "Esta migração não pode ser revertida sem descartar metas mensais e "
        "proprietários de categorias. Faça uma migração corretiva para avançar o schema."
    )