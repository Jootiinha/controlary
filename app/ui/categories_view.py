"""CRUD de categorias globais."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QLineEdit, QMessageBox

from app.models.category import Category
from app.services import categories_service
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog


class CategoryDialog(FormDialog):
    def __init__(self, parent=None, cat: Optional[Category] = None) -> None:
        super().__init__("Editar categoria" if cat else "Nova categoria", parent)
        self._cat = cat

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Mercado, Streaming…")

        self.ed_tipo = QLineEdit()
        self.ed_tipo.setPlaceholderText("Opcional: assinatura, pagamento, fixo…")

        self.chk_ativo = QCheckBox("Ativa")
        self.chk_ativo.setChecked(True)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Tipo sugerido", self.ed_tipo)
        self.form.addRow("", self.chk_ativo)

        if cat:
            self.ed_nome.setText(cat.nome)
            self.ed_tipo.setText(cat.tipo_sugerido or "")
            self.chk_ativo.setChecked(cat.ativo)

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        return True, None

    def payload(self) -> Category:
        return Category(
            id=self._cat.id if self._cat else None,
            nome=self.ed_nome.text().strip(),
            tipo_sugerido=self.ed_tipo.text().strip() or None,
            cor=None,
            ativo=self.chk_ativo.isChecked(),
        )


class CategoriesView(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Categorias",
            "Cadastre categorias para classificar despesas. Não use texto livre nos lançamentos.",
            ["Nome", "Tipo sugerido", "Ativa"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def reload(self) -> None:
        rows = []
        for c in categories_service.list_all(include_inactive=True):
            rows.append((c.id or 0, [
                c.nome,
                c.tipo_sugerido or "",
                "Sim" if c.ativo else "Não",
            ]))
        self.model.set_rows(rows)

    def _add(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            categories_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        cid = self.selected_id()
        if cid is None:
            QMessageBox.information(self, "Editar", "Selecione uma categoria.")
            return
        cat = categories_service.get(cid)
        if cat is None:
            return
        dlg = CategoryDialog(self, cat)
        if dlg.exec():
            categories_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        cid = self.selected_id()
        if cid is None:
            QMessageBox.information(self, "Excluir", "Selecione uma categoria.")
            return
        if QMessageBox.question(
            self, "Excluir", "Excluir esta categoria? Referências ficarão sem categoria."
        ) != QMessageBox.Yes:
            return
        categories_service.delete(cid)
        self.reload()
        self.data_changed.emit()
