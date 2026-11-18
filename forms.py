from datetime import date
from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class RegistrationForm(FlaskForm):
    full_name = StringField("Nome completo", validators=[DataRequired(), Length(max=120)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=255)])
    age_range = SelectField(
        "Faixa etária",
        choices=[
            ("18-24", "18 a 24 anos"),
            ("25-34", "25 a 34 anos"),
            ("35-44", "35 a 44 anos"),
            ("45-54", "45 a 54 anos"),
            ("55-64", "55 a 64 anos"),
            ("65+", "65 anos ou mais"),
        ],
        validators=[DataRequired()],
    )
    city = StringField("Cidade (opcional)", validators=[Optional(), Length(max=100)])
    password = PasswordField(
        "Senha", validators=[DataRequired(), Length(min=10, message="Use pelo menos 10 caracteres.")]
    )
    confirm_password = PasswordField(
        "Confirme a senha", validators=[DataRequired(), EqualTo("password", message="As senhas não conferem.")]
    )
    consent = BooleanField(
        "Concordo com o uso dos dados para controle financeiro pessoal.",
        validators=[DataRequired(message="É necessário aceitar o uso dos dados para criar a conta.")],
    )
    submit = SubmitField("Criar conta")


class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired()])
    remember = BooleanField("Manter conectado")
    submit = SubmitField("Entrar")


class PasswordResetRequestForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField("Enviar link de recuperação")


class PasswordResetForm(FlaskForm):
    password = PasswordField(
        "Nova senha", validators=[DataRequired(), Length(min=10, message="Use pelo menos 10 caracteres.")]
    )
    confirm_password = PasswordField(
        "Confirme a nova senha",
        validators=[DataRequired(), EqualTo("password", message="As senhas não conferem.")],
    )
    submit = SubmitField("Atualizar senha")


class LogoutForm(FlaskForm):
    submit = SubmitField("Sair")


class MovementForm(FlaskForm):
    kind = SelectField(
        "Tipo",
        choices=[("receita", "Receita"), ("despesa", "Despesa")],
        validators=[DataRequired()],
    )
    description = StringField("Descrição", validators=[DataRequired(), Length(max=160)])
    amount = DecimalField(
        "Valor",
        places=2,
        validators=[DataRequired(), NumberRange(min=Decimal("0.01"))],
        render_kw={"step": "0.01", "min": "0.01", "inputmode": "decimal"},
    )
    occurred_on = DateField(
        "Data",
        format="%Y-%m-%d",
        default=date.today,
        validators=[DataRequired()],
        render_kw={"type": "date"},
    )
    category_id = SelectField(
        "Categoria",
        coerce=int,
        choices=[(0, "Sem categoria")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Salvar movimentação")


class DeleteForm(FlaskForm):
    submit = SubmitField("Excluir")


class CategoryForm(FlaskForm):
    name = StringField("Nome da categoria", validators=[DataRequired(), Length(min=2, max=60)])
    kind = SelectField(
        "Tipo",
        choices=[("receita", "Receita"), ("despesa", "Despesa")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Criar categoria")


class MonthlyLimitForm(FlaskForm):
    monthly_limit = DecimalField(
        "Limite de gastos do mês",
        places=2,
        validators=[
            Optional(),
            NumberRange(
                min=Decimal("0.01"),
                max=Decimal("9999999999.99"),
                message="Informe um valor entre R$ 0,01 e R$ 9.999.999.999,99.",
            ),
        ],
        render_kw={"type": "number", "step": "0.01", "min": "0.01", "inputmode": "decimal"},
    )
    submit = SubmitField("Salvar meta")