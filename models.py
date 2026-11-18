from datetime import date, datetime, timezone
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    age_range = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100))
    monthly_limit = db.Column(db.Numeric(12, 2), nullable=True)
    consent_at = db.Column(db.DateTime(timezone=True), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    movements = db.relationship("Movement", back_populates="user", cascade="all, delete-orphan")
    categories = db.relationship("Category", back_populates="owner", cascade="all, delete-orphan")
    financial_profile = db.relationship(
        "FinancialProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = "categorias"
    __table_args__ = (
        db.UniqueConstraint("user_id", "name", "kind", name="uq_categoria_user_nome_tipo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True)
    name = db.Column(db.String(60), nullable=False)
    kind = db.Column(db.String(10), nullable=False)

    owner = db.relationship("User", back_populates="categories")


class Movement(db.Model):
    __tablename__ = "movimentacoes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)
    kind = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(160), nullable=False)
    occurred_on = db.Column(db.Date, nullable=False, default=date.today)

    user = db.relationship("User", back_populates="movements")
    category = db.relationship("Category")


class Tip(db.Model):
    __tablename__ = "dicas"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class FinancialProfile(db.Model):
    __tablename__ = "perfis_financeiros"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    profile_type = db.Column(db.String(30), nullable=False, default="Em formação")
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", back_populates="financial_profile")


def money_total(value: Decimal | None) -> Decimal:
    return value or Decimal("0.00")