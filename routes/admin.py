import csv
import io
from datetime import date
from decimal import Decimal
from functools import wraps

from flask import Blueprint, Response, abort, render_template
from flask_login import current_user, login_required
from sqlalchemy import and_, case, func, select

from extensions import db
from models import Category, Movement, User, money_total
from services.financial import classify_finances, profile_start_date

admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_function):
    @wraps(view_function)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view_function(*args, **kwargs)

    return wrapped


def _month_starts(today: date) -> list[date]:
    year, month = today.year, today.month
    starts = []
    for _ in range(6):
        starts.append(date(year, month, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(starts))


def _build_report() -> dict:
    total_users = db.session.scalar(
        select(func.count(User.id)).where(User.role == "user")
    ) or 0
    income_total = money_total(
        db.session.scalar(
            select(func.sum(Movement.amount))
            .join(User, Movement.user_id == User.id)
            .where(Movement.kind == "receita", User.role == "user")
        )
    )
    expense_total = money_total(
        db.session.scalar(
            select(func.sum(Movement.amount))
            .join(User, Movement.user_id == User.id)
            .where(Movement.kind == "despesa", User.role == "user")
        )
    )
    divisor = Decimal(total_users or 1)

    age_rows = db.session.execute(
        select(User.age_range, func.count(User.id))
        .where(User.role == "user")
        .group_by(User.age_range)
        .order_by(User.age_range)
    ).all()
    expense_expression = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        Movement.kind == "despesa",
                        Movement.occurred_on >= profile_start_date(),
                    ),
                    Movement.amount,
                ),
                else_=Decimal("0.00"),
            )
        ),
        Decimal("0.00"),
    )
    income_expression = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        Movement.kind == "receita",
                        Movement.occurred_on >= profile_start_date(),
                    ),
                    Movement.amount,
                ),
                else_=Decimal("0.00"),
            )
        ),
        Decimal("0.00"),
    )
    user_finances = db.session.execute(
        select(User.id, User.age_range, income_expression, expense_expression)
        .outerjoin(Movement, Movement.user_id == User.id)
        .where(User.role == "user")
        .group_by(User.id, User.age_range)
    ).all()
    age_expenses: dict[str, dict[str, Decimal | int]] = {}
    profile_counts: dict[str, int] = {}
    users_with_savings = 0
    for _user_id, age_range, income, expenses in user_finances:
        income = money_total(income)
        expenses = money_total(expenses)
        age_data = age_expenses.setdefault(age_range, {"total": Decimal("0.00"), "users": 0})
        age_data["total"] += expenses
        age_data["users"] += 1
        profile_type = classify_finances(income, expenses)
        profile_counts[profile_type] = profile_counts.get(profile_type, 0) + 1
        if income > 0 and income > expenses:
            users_with_savings += 1
    profile_rows = sorted(profile_counts.items())
    age_expense_rows = [
        (age, data["total"] / data["users"] if data["users"] else Decimal("0.00"))
        for age, data in sorted(age_expenses.items())
    ]
    category_name = func.coalesce(Category.name, "Sem categoria")
    category_rows = db.session.execute(
        select(category_name, func.sum(Movement.amount), func.count(Movement.id))
        .select_from(Movement)
        .outerjoin(Category, Movement.category_id == Category.id)
        .join(User, Movement.user_id == User.id)
        .where(Movement.kind == "despesa", User.role == "user")
        .group_by(category_name)
        .order_by(func.sum(Movement.amount).desc())
        .limit(8)
    ).all()
    category_frequency_rows = sorted(
        ((str(row[0]), int(row[2])) for row in category_rows),
        key=lambda row: row[1],
        reverse=True,
    )
    month_starts = _month_starts(date.today())
    monthly_totals = {
        (month.year, month.month): {"receita": Decimal("0"), "despesa": Decimal("0")}
        for month in month_starts
    }
    monthly_rows = db.session.execute(
        select(Movement.occurred_on, Movement.kind, Movement.amount)
        .join(User, Movement.user_id == User.id)
        .where(Movement.occurred_on >= month_starts[0], User.role == "user")
    ).all()
    for occurred_on, kind, amount in monthly_rows:
        totals = monthly_totals.get((occurred_on.year, occurred_on.month))
        if totals is not None and kind in totals:
            totals[kind] += amount

    return {
        "total_users": total_users,
        "avg_income": float(income_total / divisor),
        "avg_expense": float(expense_total / divisor),
        "income_total": float(income_total),
        "expense_total": float(expense_total),
        "saving_percent": round(users_with_savings * 100 / total_users, 1) if total_users else 0,
        "avg_monthly_expense": float(
            sum((totals["despesa"] for totals in monthly_totals.values()), Decimal("0.00"))
            / len(monthly_totals)
        ),
        "age_labels": [str(row[0]) for row in age_rows],
        "age_values": [int(row[1]) for row in age_rows],
        "age_expense_labels": [row[0] for row in age_expense_rows],
        "age_expense_values": [float(row[1]) for row in age_expense_rows],
        "category_labels": [str(row[0]) for row in category_rows],
        "category_values": [float(row[1] or 0) for row in category_rows],
        "category_frequency_rows": category_frequency_rows,
        "profile_labels": [str(row[0]) for row in profile_rows],
        "profile_values": [int(row[1]) for row in profile_rows],
        "month_labels": [month.strftime("%m/%Y") for month in month_starts],
        "month_income": [float(monthly_totals[(month.year, month.month)]["receita"]) for month in month_starts],
        "month_expense": [float(monthly_totals[(month.year, month.month)]["despesa"]) for month in month_starts],
        "age_rows": age_rows,
        "age_expense_rows": age_expense_rows,
        "category_rows": category_rows,
        "profile_rows": profile_rows,
        "monthly_rows": [
            (month.strftime("%m/%Y"), monthly_totals[(month.year, month.month)])
            for month in month_starts
        ],
    }


@admin.get("/")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html", report=_build_report())


@admin.get("/relatorio.csv")
@admin_required
def export_report():
    report = _build_report()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Relatório agregado", "Grupo", "Valor"])
    writer.writerow(["Usuários cadastrados", "Total", report["total_users"]])
    writer.writerow(["Receita média por usuário", "Todos", f'{report["avg_income"]:.2f}'])
    writer.writerow(["Despesa média por usuário", "Todos", f'{report["avg_expense"]:.2f}'])
    writer.writerow(["Média mensal de despesas", "Últimos seis meses", f'{report["avg_monthly_expense"]:.2f}'])
    writer.writerow(["Usuários com saldo positivo", "Percentual", f'{report["saving_percent"]:.1f}%'])
    for age_range, count in report["age_rows"]:
        writer.writerow(["Usuários por faixa etária", age_range, count])
    for age_range, average_expense in report["age_expense_rows"]:
        writer.writerow(["Despesa média por faixa etária", age_range, f"{average_expense:.2f}"])
    for category, amount, _count in report["category_rows"]:
        writer.writerow(["Despesas por categoria", category, f"{amount:.2f}"])
    for category, count in report["category_frequency_rows"]:
        writer.writerow(["Lançamentos por categoria", category, count])
    for profile_type, count in report["profile_rows"]:
        writer.writerow(["Perfis financeiros", profile_type, count])
    for month, totals in report["monthly_rows"]:
        writer.writerow(["Receitas mensais", month, f'{totals["receita"]:.2f}'])
        writer.writerow(["Despesas mensais", month, f'{totals["despesa"]:.2f}'])

    response = Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = "attachment; filename=relatorio-financeiro.csv"
    return response