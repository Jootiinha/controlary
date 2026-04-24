"""Testes de CRUD de categorias e mapeamentos."""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.category import Category
from app.models.fixed_expense import FixedExpense
from app.services import categories_service, fixed_expenses_service


def _uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _account() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES (?, 0)", (_uniq("Acc"),)
        )
        return int(cur.lastrowid)


def test_create_get_by_name_list_all_includes_new(test_db_path: Path) -> None:
    nome = _uniq("Moradia")
    cid = categories_service.create(
        Category(
            id=None,
            nome=f"  {nome}  ",
            tipo_sugerido="fixo",
            cor="#112233",
        )
    )
    c = categories_service.get(cid)
    assert c is not None
    assert c.nome == nome
    by_name = categories_service.get_by_name(nome.upper())
    assert by_name is not None
    assert by_name.id == cid
    all_active = categories_service.list_all()
    ids = {x.id for x in all_active}
    assert cid in ids


def test_list_all_excludes_inactive(test_db_path: Path) -> None:
    n1, n2 = _uniq("Ativa"), _uniq("Inativa")
    categories_service.create(Category(id=None, nome=n1, ativo=True))
    categories_service.create(Category(id=None, nome=n2, ativo=False))
    active = categories_service.list_all(include_inactive=False)
    active_names = {c.nome for c in active}
    assert n1 in active_names
    assert n2 not in active_names
    all_c = categories_service.list_all(include_inactive=True)
    all_names = {c.nome for c in all_c}
    assert n1 in all_names and n2 in all_names


def test_update_inactive_hidden_from_default_list(test_db_path: Path) -> None:
    nome = _uniq("Desativar")
    cid = categories_service.create(
        Category(id=None, nome=nome, ativo=True)
    )
    categories_service.update(
        Category(
            id=cid,
            nome=nome,
            tipo_sugerido=None,
            cor=None,
            ativo=False,
        )
    )
    updated = categories_service.get(cid)
    assert updated is not None
    assert updated.ativo is False
    active_names = {c.nome for c in categories_service.list_all()}
    assert nome not in active_names


def test_update_sem_id_raises(test_db_path: Path) -> None:
    with pytest.raises(ValueError, match="sem id"):
        categories_service.update(
            Category(id=None, nome="x", ativo=True)
        )


def test_list_expense_category_mappings_includes_fixed(test_db_path: Path) -> None:
    cat_nome = _uniq("Utilidades")
    cat_id = categories_service.create(
        Category(id=None, nome=cat_nome, ativo=True)
    )
    aid = _account()
    fixed_nome = _uniq("Condominio")
    fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome=fixed_nome,
            valor_mensal=300.0,
            dia_referencia=5,
            forma_pagamento="Pix",
            conta_id=aid,
            category_id=cat_id,
        )
    )
    rows = categories_service.list_expense_category_mappings()
    fixed_rows = [r for r in rows if r[0] == "Gasto fixo" and r[1] == fixed_nome]
    assert len(fixed_rows) == 1
    assert fixed_rows[0][2] == cat_nome
