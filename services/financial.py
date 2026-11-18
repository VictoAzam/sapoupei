from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import case, func, select

from extensions import db
from models import FinancialProfile, Movement, money_total


PROFILE_WINDOW_DAYS = 30


def profile_start_date(today: date | None = None) -> date:
    return (today or date.today()) - timedelta(days=PROFILE_WINDOW_DAYS)


def get_totals(
    user_id: int, since: date | None = None
) -> tuple[Decimal, Decimal]:
    date_filter = Movement.occurred_on >= since if since else True
    income, expenses = db.session.execute(
        select(
            func.sum(case((Movement.kind == "receita", Movement.amount), else_=0)),
            func.sum(case((Movement.kind == "despesa", Movement.amount), else_=0)),
        ).where(Movement.user_id == user_id, date_filter)
    ).one()
    return money_total(income), money_total(expenses)


def classify_finances(income: Decimal, expenses: Decimal) -> str:
    if income <= 0:
        return "Em formação"
    if expenses > income:
        return "Gastador"
    savings_ratio = (income - expenses) / income
    if savings_ratio >= Decimal("0.20"):
        return "Poupador"
    if expenses / income >= Decimal("0.90"):
        return "Equilibrado"
    return "Organizado"


def refresh_financial_profile(user_id: int, force: bool = False) -> FinancialProfile:
    profile = db.session.scalar(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    now = datetime.now(timezone.utc)
    if profile is not None and not force and profile.updated_at.date() >= now.date():
        return profile

    income, expenses = get_totals(user_id, since=profile_start_date())
    new_profile_type = classify_finances(income, expenses)
    if profile is None:
        profile = FinancialProfile(
            user_id=user_id,
            profile_type=new_profile_type,
            updated_at=now,
        )
        db.session.add(profile)
    else:
        profile.profile_type = new_profile_type
        profile.updated_at = now
    return profile


def get_month_history(user_id: int, today: date | None = None) -> dict:
    current = today or date.today()
    year, month = current.year, current.month
    months = []
    for _ in range(6):
        months.append(date(year, month, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    totals = {
        (item.year, item.month): {"receita": Decimal("0"), "despesa": Decimal("0")}
        for item in months
    }
    rows = db.session.execute(
        select(Movement.occurred_on, Movement.kind, Movement.amount).where(
            Movement.user_id == user_id, Movement.occurred_on >= months[0]
        )
    ).all()
    for occurred_on, kind, amount in rows:
        month_total = totals.get((occurred_on.year, occurred_on.month))
        if month_total is not None and kind in month_total:
            month_total[kind] += amount
    return {
        "labels": [item.strftime("%m/%Y") for item in months],
        "income": [float(totals[(item.year, item.month)]["receita"]) for item in months],
        "expenses": [float(totals[(item.year, item.month)]["despesa"]) for item in months],
    }


def profile_description(profile_type: str) -> str:
    descriptions = {
        "Em formação": "Registre receitas e despesas para começar a entender seu orçamento.",
        "Organizado": "Até aqui, suas despesas estão abaixo das receitas, com espaço para planejar objetivos.",
        "Equilibrado": "Suas despesas estão próximas das receitas. Pequenos ajustes podem abrir espaço para poupar.",
        "Gastador": "No período registrado, as despesas superam as receitas. Revise prioridades sem julgamento.",
        "Poupador": "Os registros mostram uma parte da renda preservada. Considere direcioná-la a objetivos.",
    }
    return descriptions.get(profile_type, descriptions["Em formação"])