from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user
from flask_mail import Message
from sqlalchemy import select

from extensions import db, mail
from forms import LoginForm, PasswordResetForm, PasswordResetRequestForm, RegistrationForm
from models import FinancialProfile, User
from services.auth import gerar_token_recuperacao, verificar_token_recuperacao

auth = Blueprint("auth", __name__)


@auth.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("painel"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = db.session.scalar(select(User).where(User.email == email))
        if existing_user:
            form.email.errors.append("Este e-mail já possui uma conta.")
        else:
            user = User(
                full_name=form.full_name.data.strip(),
                email=email,
                age_range=form.age_range.data,
                city=(form.city.data or "").strip() or None,
                consent_at=datetime.now(timezone.utc),
            )
            user.set_password(form.password.data)
            user.financial_profile = FinancialProfile()
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Conta criada. Seu controle financeiro começa por aqui.", "success")
            return redirect(url_for("painel"))

    return render_template("auth/cadastro.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("painel"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.scalar(select(User).where(User.email == email))
        if user is None or not user.check_password(form.password.data):
            flash("E-mail ou senha inválidos.", "error")
        else:
            login_user(user, remember=form.remember.data)
            destination = "admin.dashboard" if user.role == "admin" else "painel"
            return redirect(url_for(destination))

    return render_template("auth/login.html", form=form)


@auth.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():
    if current_user.is_authenticated:
        return redirect(url_for("painel"))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.scalar(select(User).where(User.email == email))
        if user:
            token = gerar_token_recuperacao(user.email)
            reset_url = url_for("auth.resetar_senha", token=token, _external=True)
            message = Message(
                subject="Recuperação de senha | sapoupei",
                recipients=[user.email],
                body=(
                    f"Olá, {user.full_name}.\n\n"
                    f"Acesse o link para criar uma nova senha: {reset_url}\n\n"
                    "Este link expira em 1 hora. Se você não solicitou a recuperação, ignore este e-mail."
                ),
            )
            try:
                mail.send(message)
            except Exception:
                current_app.logger.exception("Falha ao enviar e-mail de recuperação de senha")

        flash(
            "Se o e-mail estiver cadastrado, você receberá um link de recuperação.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/esqueci_senha.html", form=form)


@auth.route("/resetar-senha/<token>", methods=["GET", "POST"])
def resetar_senha(token: str):
    email = verificar_token_recuperacao(token)
    if not email:
        flash("O link de recuperação é inválido ou expirou.", "error")
        return redirect(url_for("auth.esqueci_senha"))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.email == email))
        if user is None:
            flash("O link de recuperação é inválido ou expirou.", "error")
            return redirect(url_for("auth.esqueci_senha"))

        user.set_password(form.password.data)
        db.session.commit()
        flash("Sua senha foi atualizada com sucesso.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/resetar_senha.html", form=form)


@auth.post("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Você saiu da sua conta.", "success")
    return redirect(url_for("auth.login"))