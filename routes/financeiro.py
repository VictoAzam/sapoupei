from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required
from sqlalchemy import func, or_, select

from extensions import db
from forms import CategoryForm, DeleteForm, MonthlyLimitForm, MovementForm
from models import Category, Movement, Tip
from services.financial import get_totals, profile_description, refresh_financial_profile

financeiro = Blueprint("financeiro", __name__)
KINDS = (("receita", "Receita"), ("despesa", "Despesa"))


def _set_form_choices(form: MovementForm, default_kind: str = "despesa") -> None:
    form.kind.choices = list(KINDS)
    selected_kind = form.kind.data or default_kind
    if selected_kind not in {kind for kind, _label in KINDS}:
        selected_kind = default_kind
    categories = db.session.scalars(
        select(Category)
        .where(
            Category.kind == selected_kind,
            or_(Category.user_id.is_(None), Category.user_id == current_user.id),
        )
        .order_by(Category.user_id.is_not(None), Category.name)
    ).all()
    form.category_id.choices = [(0, "Sem categoria")] + [
        (category.id, category.name) for category in categories
    ]


def _get_movement(movement_id: int) -> Movement:
    movement = db.session.scalar(
        select(Movement).where(
            Movement.id == movement_id, Movement.user_id == current_user.id
        )
    )
    if movement is None:
        abort(404)
    return movement


@financeiro.get("/movimentacoes")
@login_required
def lista_movimentacoes():
    kind = request.args.get("tipo")
    selected_kind = kind if kind in {value for value, _label in KINDS} else None
    query = select(Movement).where(Movement.user_id == current_user.id)
    if selected_kind:
        query = query.where(Movement.kind == selected_kind)
    movements = db.paginate(
        query.order_by(Movement.occurred_on.desc(), Movement.id.desc()),
        page=request.args.get("page", 1, type=int),
        per_page=20,
        max_per_page=20,
        error_out=False,
    )
    delete_form = DeleteForm()
    return render_template(
        "financeiro/movimentacoes.html",
        movements=movements,
        delete_form=delete_form,
        selected_kind=selected_kind,
    )


@financeiro.route("/movimentacoes/nova", methods=["GET", "POST"])
@login_required
def nova_movimentacao():
    form = MovementForm()
    if request.method == "GET":
        requested_kind = request.args.get("tipo", "despesa")
        form.kind.data = requested_kind if requested_kind in {kind for kind, _ in KINDS} else "despesa"
    _set_form_choices(form)

    if form.validate_on_submit():
        movement = Movement(user_id=current_user.id)
        _apply_form(movement, form)
        db.session.add(movement)
        db.session.flush()
        refresh_financial_profile(current_user.id, force=True)
        db.session.commit()
        flash("Movimentação registrada.", "success")
        return redirect(url_for("financeiro.lista_movimentacoes"))

    return render_template("financeiro/form.html", form=form, page_title="Nova movimentação")


@financeiro.route("/movimentacoes/<int:movement_id>/editar", methods=["GET", "POST"])
@login_required
def editar_movimentacao(movement_id: int):
    movement = _get_movement(movement_id)
    form = MovementForm(obj=movement)
    _set_form_choices(form, movement.kind)

    if form.validate_on_submit():
        _apply_form(movement, form)
        refresh_financial_profile(current_user.id, force=True)
        db.session.commit()
        flash("Movimentação atualizada.", "success")
        return redirect(url_for("financeiro.lista_movimentacoes"))

    return render_template("financeiro/form.html", form=form, page_title="Editar movimentação")


@financeiro.route("/categorias/nova", methods=["GET", "POST"])
@login_required
def nova_categoria():
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        duplicate = db.session.scalar(
            select(Category).where(
                func.lower(Category.name) == name.lower(),
                Category.kind == form.kind.data,
                or_(Category.user_id.is_(None), Category.user_id == current_user.id),
            )
        )
        if duplicate:
            form.name.errors.append(
                "Já existe uma categoria global ou sua categoria com esse nome e tipo."
            )
        else:
            category = Category(
                user_id=current_user.id,
                name=name,
                kind=form.kind.data,
            )
            db.session.add(category)
            db.session.commit()
            flash("Categoria criada para sua conta.", "success")
            return redirect(url_for("financeiro.nova_movimentacao", tipo=category.kind))

    return render_template("financeiro/categoria_form.html", form=form)


@financeiro.post("/movimentacoes/<int:movement_id>/excluir")
@login_required
def excluir_movimentacao(movement_id: int):
    movement = _get_movement(movement_id)
    form = DeleteForm()
    if form.validate_on_submit():
        db.session.delete(movement)
        db.session.flush()
        refresh_financial_profile(current_user.id, force=True)
        db.session.commit()
        flash("Movimentação excluída.", "success")
    else:
        flash("Não foi possível confirmar a exclusão.", "error")
    return redirect(url_for("financeiro.lista_movimentacoes"))


@financeiro.get("/dicas")
@login_required
def dicas():
    tips = db.session.scalars(
        select(Tip).where(Tip.is_active.is_(True)).order_by(Tip.id)
    ).all()
    income, expenses = get_totals(current_user.id)
    profile = refresh_financial_profile(current_user.id)
    if db.session.new or db.session.dirty:
        db.session.commit()
    if income <= 0:
        recommendation = "Comece registrando suas receitas para montar um orçamento realista."
    elif expenses > income:
        recommendation = "Compare despesas essenciais e variáveis; escolha um ajuste pequeno para acompanhar neste mês."
    elif expenses / income >= 0.8:
        recommendation = "Suas despesas se aproximam das receitas. Revise os gastos recorrentes antes de assumir novos compromissos."
    else:
        recommendation = "Considere reservar uma parte do saldo para uma meta ou uma reserva de emergência."
    profile_type = profile.profile_type if profile else "Em formação"
    return render_template(
        "financeiro/dicas.html",
        tips=tips,
        recommendation=recommendation,
        profile_type=profile_type,
        profile_text=profile_description(profile_type),
    )


@financeiro.route("/meta-mensal", methods=["GET", "POST"])
@login_required
def meta_mensal():
    form = MonthlyLimitForm()
    if request.method == "GET":
        form.monthly_limit.data = current_user.monthly_limit

    if form.validate_on_submit():
        current_user.monthly_limit = form.monthly_limit.data
        db.session.commit()
        if current_user.monthly_limit is None:
            flash("Meta mensal removida.", "success")
        else:
            flash("Meta mensal atualizada.", "success")
        return redirect(url_for("painel"))

    return render_template("financeiro/meta_mensal.html", form=form)


def _apply_form(movement: Movement, form: MovementForm) -> None:
    movement.kind = form.kind.data
    movement.description = form.description.data.strip()
    movement.amount = form.amount.data
    movement.occurred_on = form.occurred_on.data or date.today()
    movement.category_id = form.category_id.data or None