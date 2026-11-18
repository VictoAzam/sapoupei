import os
from datetime import date
from decimal import Decimal

import click
from flask import Flask, redirect, render_template, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from extensions import csrf, db, login_manager, mail, migrate
from models import Category, Movement, Tip, User
from routes.admin import admin as admin_blueprint
from routes.auth import auth
from routes.financeiro import financeiro
from services.financial import (
    get_month_history,
    get_totals,
    profile_description,
    refresh_financial_profile,
)

login_manager.login_view = "auth.login"
login_manager.login_message = "Entre na sua conta para continuar."
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
  try:
    return db.session.get(User, int(user_id))
  except (TypeError, ValueError):
    return None


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    app.register_blueprint(auth)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(financeiro)

    @app.get("/service-worker.js")
    def service_worker():
        response = send_from_directory(app.static_folder, "service-worker.js")
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    @app.context_processor
    def inject_logout_form():
      from forms import LogoutForm

      return {"logout_form": LogoutForm()}

    @app.get("/")
    def inicio():
      if current_user.is_authenticated:
        return redirect(url_for("painel"))
      return redirect(url_for("auth.login"))

    @app.get("/painel")
    @login_required
    def painel():
                total_income, total_expenses = get_totals(current_user.id)
                today = date.today()
                month_start = today.replace(day=1)
                monthly_expenses = db.session.scalar(
                        select(func.sum(Movement.amount)).where(
                                Movement.user_id == current_user.id,
                                Movement.kind == "despesa",
                                Movement.occurred_on >= month_start,
                                Movement.occurred_on <= today,
                        )
                )
                monthly_spent = monthly_expenses or Decimal("0.00")
                monthly_limit = current_user.monthly_limit
                monthly_percent = (
                        float(monthly_spent / monthly_limit * 100) if monthly_limit else 0.0
                )
                monthly_progress = min(monthly_percent, 100.0)
                monthly_progress_class = (
                        "bg-danger"
                        if monthly_percent >= 100
                        else "bg-warning"
                        if monthly_percent >= 80
                        else "bg-success"
                )
                monthly_remaining = (
                        monthly_limit - monthly_spent if monthly_limit is not None else None
                )
                profile = refresh_financial_profile(current_user.id)
                if db.session.new or db.session.dirty:
                    db.session.commit()
                movements = db.session.scalars(
                        select(Movement)
                        .where(Movement.user_id == current_user.id)
                        .order_by(Movement.occurred_on.desc(), Movement.id.desc())
                        .limit(10)
                ).all()
                return render_template(
                        "painel.html",
                        total_income=total_income,
                        total_expenses=total_expenses,
                        balance=total_income - total_expenses,
                        movements=movements,
                        profile_type=profile.profile_type,
                        profile_text=profile_description(profile.profile_type),
                        month_history=get_month_history(current_user.id),
                        monthly_spent=monthly_spent,
                        monthly_limit=monthly_limit,
                        monthly_percent=monthly_percent,
                        monthly_progress=monthly_progress,
                        monthly_progress_class=monthly_progress_class,
                        monthly_remaining=monthly_remaining,
                )

    @app.get("/teste-banco")
    def teste_banco() -> tuple[str, int] | str:
        try:
            with db.engine.connect() as conexao:
                conexao.execute(text("SELECT 1"))
            return "Conexão com MySQL realizada com sucesso!"
        except SQLAlchemyError:
            app.logger.exception("Não foi possível testar a conexão com MySQL")
            return "Não foi possível conectar ao banco. Confira o serviço e o arquivo .env.", 503

    @app.cli.command("init-db")
    def init_db():
        """Insere categorias e dicas iniciais que ainda não existam."""
        default_categories = [
            ("Salário", "receita"),
            ("Renda extra", "receita"),
            ("Alimentação", "despesa"),
            ("Moradia", "despesa"),
            ("Transporte", "despesa"),
            ("Saúde", "despesa"),
            ("Educação", "despesa"),
            ("Lazer", "despesa"),
            ("Outros", "despesa"),
        ]
        for name, kind in default_categories:
            exists = db.session.scalar(
                select(Category).where(Category.name == name, Category.kind == kind)
            )
            if exists is None:
                db.session.add(Category(name=name, kind=kind))
        default_tips = [
            ("Pague-se primeiro", "Defina um valor possível para guardar assim que receber, mesmo que comece pequeno."),
            ("Revise os gastos recorrentes", "Confira assinaturas, tarifas e serviços pouco usados antes da próxima cobrança."),
            ("Planeje compras maiores", "Compare preços e espere um período antes de decidir por uma compra não essencial."),
            ("Monte sua reserva aos poucos", "Uma reserva pode começar com depósitos regulares e crescer conforme sua realidade."),
            ("Organize as contas por prioridade", "Separe despesas essenciais, compromissos e gastos flexíveis para enxergar escolhas."),
        ]
        for title, content in default_tips:
            exists = db.session.scalar(select(Tip).where(Tip.title == title))
            if exists is None:
                db.session.add(Tip(title=title, content=content))
        db.session.commit()
        click.echo("Categorias e dicas iniciais verificadas.")

    @app.cli.command("promote-admin")
    @click.argument("email")
    def promote_admin(email: str):
        """Promove uma conta já cadastrada para administradora."""
        normalized_email = email.strip().lower()
        user = db.session.scalar(select(User).where(User.email == normalized_email))
        if user is None:
            raise click.ClickException(
                "Conta não encontrada. Cadastre essa conta no site antes de promovê-la."
            )
        if user.role == "admin":
            click.echo("Essa conta já é administradora.")
            return
        user.role = "admin"
        db.session.commit()
        click.echo("Conta promovida. Entre novamente para abrir a área administrativa.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")