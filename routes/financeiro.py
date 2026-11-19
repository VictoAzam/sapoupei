from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required
from sqlalchemy import func, or_, select, update

from extensions import db
from forms import CategoryForm, DeleteForm, MonthlyLimitForm, MovementFilterForm, MovementForm
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


def _get_personal_category(category_id: int) -> Category:
    category = db.session.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
        )
    )
    if category is None:
        abort(404)
    return category


def _set_filter_category_choices(form: MovementFilterForm) -> set[int]:
    categories = db.session.scalars(
        select(Category)
        .where(
            or_(Category.user_id.is_(None), Category.user_id == current_user.id)
        )
        .order_by(Category.user_id.is_not(None), Category.kind, Category.name)
    ).all()
    form.categoria.choices = [(0, "Todas as categorias"), (-1, "Sem categoria")] + [
        (category.id, f"{category.name} · {'Receita' if category.kind == 'receita' else 'Despesa'}")
        for category in categories
    ]
    return {category.id for category in categories}


@financeiro.get("/movimentacoes")
@login_required
def lista_movimentacoes():
    form = MovementFilterForm(formdata=request.args)
    allowed_category_ids = _set_filter_category_choices(form)
    form.validate()
    filter_errors = [
        error
        for field in (form.tipo, form.categoria, form.data_inicial, form.data_final, form.busca)
        for error in field.errors
    ]
    query = select(Movement).where(Movement.user_id == current_user.id)
    selected_kind = form.tipo.data if form.tipo.data in {kind for kind, _label in KINDS} else None
    if selected_kind:
        query = query.where(Movement.kind == selected_kind)

    selected_category = form.categoria.data
    if selected_category == -1:
        query = query.where(Movement.category_id.is_(None))
    elif selected_category in allowed_category_ids:
        query = query.where(Movement.category_id == selected_category)
    elif selected_category not in (None, 0):
        filter_errors.append("A categoria selecionada não está disponível.")
        form.categoria.data = 0

    start_date = form.data_inicial.data
    end_date = form.data_final.data
    invalid_period = bool(start_date and end_date and start_date > end_date)
    if invalid_period:
        filter_errors.append("A data inicial deve ser anterior ou igual à data final.")
        query = query.where(Movement.id.is_(None))
    else:
        if start_date:
            query = query.where(Movement.occurred_on >= start_date)
        if end_date:
            query = query.where(Movement.occurred_on <= end_date)

    search_text = (form.busca.data or "").strip()
    if search_text:
        query = query.where(Movement.description.ilike(f"%{search_text}%"))

    pagination_args = {}
    if selected_kind:
        pagination_args["tipo"] = selected_kind
    if selected_category not in (None, 0) and selected_category in {-1, *allowed_category_ids}:
        pagination_args["categoria"] = selected_category
    if start_date:
        pagination_args["data_inicial"] = start_date.isoformat()
    if end_date:
        pagination_args["data_final"] = end_date.isoformat()
    if search_text:
        pagination_args["busca"] = search_text

    movements = db.paginate(
        query.order_by(Movement.occurred_on.desc(), Movement.id.desc()),
        page=1 if invalid_period else request.args.get("page", 1, type=int),
        per_page=20,
        max_per_page=20,
        error_out=False,
    )
    previous_url = (
        url_for("financeiro.lista_movimentacoes", page=movements.prev_num, **pagination_args)
        if movements.has_prev
        else None
    )
    next_url = (
        url_for("financeiro.lista_movimentacoes", page=movements.next_num, **pagination_args)
        if movements.has_next
        else None
    )
    delete_form = DeleteForm()
    return render_template(
        "financeiro/movimentacoes.html",
        movements=movements,
        delete_form=delete_form,
        filter_form=form,
        filter_errors=filter_errors,
        pagination_args=pagination_args,
        previous_url=previous_url,
        next_url=next_url,
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


@financeiro.get("/categorias")
@login_required
def lista_categorias():
    personal_categories = db.session.scalars(
        select(Category)
        .where(Category.user_id == current_user.id)
        .order_by(Category.kind, Category.name)
    ).all()
    global_categories = db.session.scalars(
        select(Category)
        .where(Category.user_id.is_(None))
        .order_by(Category.kind, Category.name)
    ).all()
    return render_template(
        "financeiro/categorias.html",
        personal_categories=personal_categories,
        global_categories=global_categories,
        delete_form=DeleteForm(),
    )


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
            return redirect(url_for("financeiro.lista_categorias"))

    return render_template(
        "financeiro/categoria_form.html",
        form=form,
        page_title="Nova categoria",
        submit_label="Criar categoria",
    )


@financeiro.route("/categorias/<int:category_id>/editar", methods=["GET", "POST"])
@login_required
def editar_categoria(category_id: int):
    category = _get_personal_category(category_id)
    form = CategoryForm(obj=category)
    movement_count = db.session.scalar(
        select(func.count(Movement.id)).where(
            Movement.category_id == category.id,
            Movement.user_id == current_user.id,
        )
    )

    if form.validate_on_submit():
        name = form.name.data.strip()
        duplicate = db.session.scalar(
            select(Category).where(
                Category.id != category.id,
                func.lower(Category.name) == name.lower(),
                Category.kind == form.kind.data,
                or_(Category.user_id.is_(None), Category.user_id == current_user.id),
            )
        )
        if duplicate:
            form.name.errors.append(
                "Já existe uma categoria global ou sua categoria com esse nome e tipo."
            )
        elif movement_count and form.kind.data != category.kind:
            form.kind.errors.append(
                "O tipo não pode ser alterado enquanto houver movimentações vinculadas."
            )
        else:
            category.name = name
            category.kind = form.kind.data
            db.session.commit()
            flash("Categoria atualizada.", "success")
            return redirect(url_for("financeiro.lista_categorias"))

    return render_template(
        "financeiro/categoria_form.html",
        form=form,
        page_title="Editar categoria",
        submit_label="Salvar alterações",
    )


@financeiro.post("/categorias/<int:category_id>/excluir")
@login_required
def excluir_categoria(category_id: int):
    category = _get_personal_category(category_id)
    form = DeleteForm()
    if form.validate_on_submit():
        db.session.execute(
            update(Movement)
            .where(
                Movement.category_id == category.id,
                Movement.user_id == current_user.id,
            )
            .values(category_id=None)
        )
        db.session.delete(category)
        db.session.commit()
        flash("Categoria excluída. As movimentações foram preservadas sem categoria.", "success")
    else:
        flash("Não foi possível confirmar a exclusão.", "error")
    return redirect(url_for("financeiro.lista_categorias"))


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