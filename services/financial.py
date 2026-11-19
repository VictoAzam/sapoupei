from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext

from sqlalchemy import case, func, or_, select

from extensions import db
from models import Category, FinancialProfile, Movement, money_total


PROFILE_WINDOW_DAYS = 30
MAX_SIMULATION_MONTHS = 600
MAX_SIMULATION_RATE_PERCENT = Decimal("100")
MAX_SIMULATION_AMOUNT = Decimal("9999999999.99")
MONEY_CENT = Decimal("0.01")


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


def _get_period_totals(
    user_id: int, start_date: date, end_date: date
) -> tuple[Decimal, Decimal]:
    income, expenses = db.session.execute(
        select(
            func.sum(
                case(
                    (Movement.kind == "receita", Movement.amount),
                    else_=Decimal("0.00"),
                )
            ),
            func.sum(
                case(
                    (Movement.kind == "despesa", Movement.amount),
                    else_=Decimal("0.00"),
                )
            ),
        ).where(
            Movement.user_id == user_id,
            Movement.occurred_on >= start_date,
            Movement.occurred_on <= end_date,
        )
    ).one()
    return money_total(income), money_total(expenses)


def get_month_comparison(user_id: int, today: date | None = None) -> dict:
    current = today or date.today()
    current_start = current.replace(day=1)
    previous_month = current_start - timedelta(days=1)
    previous_start = previous_month.replace(day=1)
    previous_end = previous_start.replace(
        day=min(current.day, monthrange(previous_start.year, previous_start.month)[1])
    )

    current_income, current_expenses = _get_period_totals(
        user_id, current_start, current
    )
    previous_income, previous_expenses = _get_period_totals(
        user_id, previous_start, previous_end
    )
    return {
        "current": {"income": current_income, "expenses": current_expenses},
        "previous": {"income": previous_income, "expenses": previous_expenses},
        "current_start": current_start,
        "current_end": current,
        "previous_start": previous_start,
        "previous_end": previous_end,
    }


def get_month_expenses_by_category(
    user_id: int, today: date | None = None
) -> list[tuple[str, Decimal]]:
    current = today or date.today()
    month_start = current.replace(day=1)
    category_label = case(
        (Category.name.is_(None), "Sem categoria"),
        (or_(Category.user_id.is_(None), Category.user_id == user_id), Category.name),
        else_="Sem categoria",
    )
    rows = db.session.execute(
        select(category_label, func.sum(Movement.amount))
        .select_from(Movement)
        .outerjoin(Category, Movement.category_id == Category.id)
        .where(
            Movement.user_id == user_id,
            Movement.kind == "despesa",
            Movement.occurred_on >= month_start,
            Movement.occurred_on <= current,
        )
        .group_by(category_label)
        .order_by(func.sum(Movement.amount).desc(), category_label)
    ).all()
    return [(str(label), money_total(amount)) for label, amount in rows]


def simulate_investment(
    initial_amount: Decimal,
    monthly_contribution: Decimal,
    interest_rate_percent: Decimal,
    rate_period: str,
    months: int,
) -> dict[str, Decimal | list[int] | list[Decimal]]:
    if not Decimal("0") <= initial_amount <= MAX_SIMULATION_AMOUNT:
        raise ValueError("Valor inicial fora do intervalo permitido.")
    if not Decimal("0") <= monthly_contribution <= MAX_SIMULATION_AMOUNT:
        raise ValueError("Aporte mensal fora do intervalo permitido.")
    if not Decimal("0") <= interest_rate_percent <= MAX_SIMULATION_RATE_PERCENT:
        raise ValueError("A taxa deve estar entre 0% e 100%.")
    if rate_period not in {"mensal", "anual"}:
        raise ValueError("Período de taxa inválido.")
    if not 1 <= months <= MAX_SIMULATION_MONTHS:
        raise ValueError("O prazo deve ser de 1 a 600 meses.")

    with localcontext() as context:
        context.prec = 40
        monthly_rate = interest_rate_percent / Decimal("100")
        if rate_period == "anual":
            monthly_rate = (
                (Decimal("1") + monthly_rate) ** (Decimal("1") / Decimal("12"))
                - Decimal("1")
            )

        balance = initial_amount
        total_invested = initial_amount
        months_elapsed = [0]
        invested_series = [total_invested.quantize(MONEY_CENT)]
        balance_series = [balance.quantize(MONEY_CENT)]

        for month in range(1, months + 1):
            balance = balance * (Decimal("1") + monthly_rate)
            balance += monthly_contribution
            total_invested += monthly_contribution
            months_elapsed.append(month)
            invested_series.append(total_invested.quantize(MONEY_CENT))
            balance_series.append(
                balance.quantize(MONEY_CENT, rounding=ROUND_HALF_UP)
            )

        final_value = balance.quantize(MONEY_CENT, rounding=ROUND_HALF_UP)
        total_invested = total_invested.quantize(MONEY_CENT)

        return {
            "months": months_elapsed,
            "invested_series": invested_series,
            "balance_series": balance_series,
            "total_invested": total_invested,
            "interest_earned": final_value - total_invested,
            "final_value": final_value,
            "monthly_rate": monthly_rate,
        }


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
            Movement.user_id == user_id,
            Movement.occurred_on >= months[0],
            Movement.occurred_on <= current,
        )
    ).all()
    for occurred_on, kind, amount in rows:
        month_total = totals.get((occurred_on.year, occurred_on.month))
        if month_total is not None and kind in month_total:
            month_total[kind] = money_total(month_total[kind] + money_total(amount))
    return {
        "labels": [item.strftime("%m/%Y") for item in months],
        "income": [money_total(totals[(item.year, item.month)]["receita"]) for item in months],
        "expenses": [money_total(totals[(item.year, item.month)]["despesa"]) for item in months],
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