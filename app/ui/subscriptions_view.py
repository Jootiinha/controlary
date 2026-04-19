"""Tela de CRUD de assinaturas recorrentes."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.subscription import Subscription
from app.services import (
    accounts_service,
    cards_service,
    subscription_months_service,
    subscriptions_service,
)
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.card import KpiCard
from app.ui.widgets.category_picker import CategoryPicker
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency


STATUS_ASSINATURA = ["ativa", "pausada", "cancelada"]
FORMAS = ["Pix", "Débito", "Crédito", "Boleto", "Transferência", "Débito Automático"]


class SubscriptionDialog(FormDialog):
    def __init__(self, parent=None, sub: Optional[Subscription] = None) -> None:
        super().__init__("Editar assinatura" if sub else "Nova assinatura", parent)
        self._sub = sub

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Netflix, Spotify, ChatGPT...")

        self._picker_cat = CategoryPicker(self, allow_empty=False)
        self._picker_cat.connect_new_button(self._nova_categoria)

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 100_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(5.0)

        self.ed_dia = QSpinBox()
        self.ed_dia.setRange(1, 31)
        self.ed_dia.setValue(1)

        self.ed_forma = QComboBox()
        self.ed_forma.addItems(FORMAS)

        self.cmb_meio = QComboBox()
        self.cmb_meio.setEditable(False)
        self._fill_meio()
        self.cmb_meio.currentIndexChanged.connect(lambda _: self._sync_meio())

        self.lbl_meio = QLabel()
        self.lbl_meio.setWordWrap(True)
        self.lbl_meio.setStyleSheet("color: #6B7280;")

        self.ed_status = QComboBox()
        self.ed_status.addItems(STATUS_ASSINATURA)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(70)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Categoria *", self._picker_cat)
        self.form.addRow("Valor mensal *", self.ed_valor)
        self.form.addRow("Dia da cobrança *", self.ed_dia)
        self.form.addRow("Forma de pagamento *", self.ed_forma)
        self.form.addRow("Conta ou cartão", self.cmb_meio)
        self.form.addRow("", self.lbl_meio)
        self.form.addRow("Status *", self.ed_status)
        self.form.addRow("Observação", self.ed_obs)

        if sub:
            self.ed_nome.setText(sub.nome)
            if sub.category_id is not None:
                self._picker_cat.set_category_id(sub.category_id)
            self.ed_valor.setValue(sub.valor_mensal)
            self.ed_dia.setValue(sub.dia_cobranca)
            idx = self.ed_forma.findText(sub.forma_pagamento)
            if idx >= 0:
                self.ed_forma.setCurrentIndex(idx)
            idx = self.ed_status.findText(sub.status)
            if idx >= 0:
                self.ed_status.setCurrentIndex(idx)
            self.ed_obs.setPlainText(sub.observacao or "")
            self._select_meio(sub)

        self._sync_meio()

    def _sync_meio(self) -> None:
        raw = self.cmb_meio.currentData()
        if not raw or not isinstance(raw, str):
            self.ed_dia.setEnabled(True)
            self.ed_forma.setEnabled(True)
            self.lbl_meio.clear()
            return
        kind, _, mid = raw.partition(":")
        if kind != "card" or not mid:
            self.ed_dia.setEnabled(True)
            self.ed_forma.setEnabled(True)
            self.lbl_meio.clear()
            return
        try:
            cid = int(mid)
        except ValueError:
            return
        c = cards_service.get(cid)
        if c is None:
            return
        self.ed_dia.setEnabled(False)
        self.ed_dia.setValue(c.dia_pagamento_fatura)
        self.ed_forma.setEnabled(False)
        idx = self.ed_forma.findText("Crédito")
        if idx >= 0:
            self.ed_forma.setCurrentIndex(idx)
        self.lbl_meio.setText(
            f"Cobra na fatura do cartão (vencimento dia {c.dia_pagamento_fatura:02d}). "
            "O calendário usa o evento da fatura mensal."
        )

    def _nova_categoria(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()

    def _fill_meio(self) -> None:
        self.cmb_meio.clear()
        self.cmb_meio.addItem("(Nenhum)", None)
        for a in accounts_service.list_all():
            self.cmb_meio.addItem(f"Conta · {a.nome}", f"acc:{a.id}")
        for c in cards_service.list_all():
            self.cmb_meio.addItem(f"Cartão · {c.nome}", f"card:{c.id}")

    def _select_meio(self, sub: Subscription) -> None:
        for i in range(self.cmb_meio.count()):
            data = self.cmb_meio.itemData(i)
            if not data or not isinstance(data, str):
                continue
            kind, _, mid = data.partition(":")
            if not mid:
                continue
            try:
                iid = int(mid)
            except ValueError:
                continue
            if sub.account_id and kind == "acc" and iid == sub.account_id:
                self.cmb_meio.setCurrentIndex(i)
                return
            if sub.card_id and kind == "card" and iid == sub.card_id:
                self.cmb_meio.setCurrentIndex(i)
                return

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        if self.ed_valor.value() <= 0:
            return False, "Valor mensal deve ser maior que zero"
        if self._picker_cat.current_category_id() is None:
            return False, "Selecione uma categoria"
        return True, None

    def payload(self) -> Subscription:
        account_id: Optional[int] = None
        card_id: Optional[int] = None
        raw = self.cmb_meio.currentData()
        if raw and isinstance(raw, str):
            kind, _, mid = raw.partition(":")
            if mid:
                try:
                    iid = int(mid)
                except ValueError:
                    iid = None
                if iid is not None:
                    if kind == "acc":
                        account_id = iid
                    elif kind == "card":
                        card_id = iid
        dia = int(self.ed_dia.value())
        forma = self.ed_forma.currentText()
        if card_id is not None:
            c = cards_service.get(card_id)
            if c is not None:
                dia = c.dia_pagamento_fatura
            forma = "Crédito"
        return Subscription(
            id=self._sub.id if self._sub else None,
            nome=self.ed_nome.text().strip(),
            categoria=None,
            valor_mensal=float(self.ed_valor.value()),
            dia_cobranca=dia,
            forma_pagamento=forma,
            status=self.ed_status.currentText(),
            observacao=self.ed_obs.toPlainText().strip() or None,
            account_id=account_id,
            card_id=card_id,
            category_id=self._picker_cat.current_category_id(),
        )


class _SubscriptionsCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Assinaturas",
            "Gerencie assinaturas recorrentes e o custo mensal total.",
            ["Nome", "Categoria", "Valor", "Dia", "Forma", "Conta/Cartão", "Status"],
        )
        self._by_id: dict[int, Subscription] = {}
        self.totals_wrap.setVisible(True)
        self._kp_mensal = KpiCard("Total mensal (ativas)", "-", compact=True)
        self._kp_ativas = KpiCard("Ativas", "-", compact=True)
        self._kp_outras = KpiCard("Pausadas / canceladas", "-", compact=True)
        self.totals_bar.addWidget(self._kp_mensal)
        self.totals_bar.addWidget(self._kp_ativas)
        self.totals_bar.addWidget(self._kp_outras)
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def _refresh_kpi_cards(self) -> None:
        total_ativas = sum(
            s.valor_mensal for s in self._by_id.values() if s.status == "ativa"
        )
        n_ativas = sum(1 for s in self._by_id.values() if s.status == "ativa")
        n_out = len(self._by_id) - n_ativas
        self._kp_mensal.set_value(format_currency(total_ativas))
        self._kp_ativas.set_value(str(n_ativas))
        self._kp_outras.set_value(str(n_out))

    def reload(self) -> None:
        self._by_id.clear()
        rows = []
        for s in subscriptions_service.list_all():
            if s.id is not None:
                self._by_id[s.id] = s
            meio = s.meio_label or "—"
            cat = s.categoria_nome or s.categoria or ""
            rows.append((s.id or 0, [
                s.nome,
                cat,
                format_currency(s.valor_mensal),
                f"Dia {s.dia_cobranca:02d}",
                s.forma_pagamento,
                meio,
                s.status.capitalize(),
            ]))
        self.model.set_rows(rows)
        self._refresh_kpi_cards()
        self.refresh_totals()

    def compute_totals(self, visible_ids: list[int]) -> None:
        if not self._by_id:
            self.set_footer_text("", "")
            return
        vis = [self._by_id[i] for i in visible_ids if i in self._by_id]
        total = sum(s.valor_mensal for s in vis)
        self.set_footer_text(
            f"Total mensal (visíveis): {format_currency(total)}",
            f"Itens: {len(vis)}",
        )

    def _add(self) -> None:
        dlg = SubscriptionDialog(self)
        if dlg.exec():
            subscriptions_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Editar", "Selecione uma assinatura.")
            return
        sub = subscriptions_service.get(sid)
        if sub is None:
            return
        dlg = SubscriptionDialog(self, sub)
        if dlg.exec():
            subscriptions_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Excluir", "Selecione uma assinatura.")
            return
        resp = QMessageBox.question(
            self, "Excluir", "Excluir esta assinatura?"
        )
        if resp == QMessageBox.Yes:
            subscriptions_service.delete(sid)
            self.reload()
            self.data_changed.emit()


class _SubscriptionMonthlyControl(QWidget):
    """Marca assinaturas em conta como pagas na competência (livro-caixa)."""
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._hdr_sort_col: int | None = None
        self._hdr_sort_order = Qt.SortOrder.AscendingOrder
        hint = QLabel(
            "Assinaturas ativas debitadas em conta corrente. "
            "Marque como Pago quando o débito ocorrer no mês selecionado."
        )
        hint.setWordWrap(True)
        hint.setObjectName("PageSubtitle")
        row = QHBoxLayout()
        row.addWidget(QLabel("Competência:"))
        self.dt = QDateEdit()
        self.dt.setDisplayFormat("MM/yyyy")
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())
        self.dt.dateChanged.connect(self.reload_table)
        row.addWidget(self.dt)
        row.addStretch()
        self.tbl = ReadOnlyTable(
            ["Nome", "Valor", "Conta", "Situação no mês"],
            sorting_enabled=False,
        )
        self.tbl.horizontalHeader().sectionClicked.connect(
            self._on_monthly_header_clicked
        )
        lay = QVBoxLayout(self)
        lay.addWidget(hint)
        lay.addLayout(row)
        lay.addWidget(self.tbl, 1)
        self.reload_table()

    def _on_monthly_header_clicked(self, logical_index: int) -> None:
        if self._hdr_sort_col == logical_index:
            self._hdr_sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._hdr_sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._hdr_sort_col = logical_index
            self._hdr_sort_order = Qt.SortOrder.AscendingOrder
        self.reload_table()

    def ano_mes(self) -> str:
        d = self.dt.date()
        return f"{d.year():04d}-{d.month():02d}"

    def reload_table(self) -> None:
        ym = self.ano_mes()
        items = [
            s
            for s in subscriptions_service.list_all()
            if s.status == "ativa" and s.account_id is not None and s.id is not None
        ]
        if self._hdr_sort_col is not None:
            col = self._hdr_sort_col
            rev = self._hdr_sort_order == Qt.SortOrder.DescendingOrder

            def hdr_key(s: Subscription):
                assert s.id is not None
                acc = accounts_service.get(int(s.account_id))
                cn = (acc.nome if acc else "—").lower()
                pg = subscription_months_service.is_paid(s.id, ym)
                if col == 0:
                    return (s.nome.lower(),)
                if col == 1:
                    return (float(s.valor_mensal),)
                if col == 2:
                    return (cn,)
                if col == 3:
                    return (pg,)
                return (0,)

            items = sorted(items, key=hdr_key, reverse=rev)

        self.tbl.setRowCount(len(items))
        for i, s in enumerate(items):
            assert s.id is not None
            sid = s.id
            it_n = QTableWidgetItem(s.nome)
            it_n.setTextAlignment(ReadOnlyTable.ALIGN_LEFT)
            self.tbl.setItem(i, 0, it_n)
            it_v = QTableWidgetItem(format_currency(s.valor_mensal))
            it_v.setTextAlignment(ReadOnlyTable.ALIGN_RIGHT)
            self.tbl.setItem(i, 1, it_v)
            acc = accounts_service.get(int(s.account_id))
            it_c = QTableWidgetItem(acc.nome if acc else "—")
            it_c.setTextAlignment(ReadOnlyTable.ALIGN_LEFT)
            self.tbl.setItem(i, 2, it_c)
            cb = QComboBox()
            cb.addItems(["Pendente", "Pago"])
            pago = subscription_months_service.is_paid(sid, ym)
            cb.blockSignals(True)
            cb.setCurrentIndex(1 if pago else 0)
            cb.blockSignals(False)
            cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            def make_handler(sub_id: int, combo: QComboBox, competencia: str):
                def on_change(_idx: int) -> None:
                    want = combo.currentIndex() == 1
                    subscription_months_service.set_month_status(
                        sub_id, competencia, pago=want
                    )
                    self.data_changed.emit()

                return on_change

            cb.currentIndexChanged.connect(make_handler(sid, cb, ym))
            self.tbl.setCellWidget(i, 3, cb)

        hdr = self.tbl.horizontalHeader()
        if self._hdr_sort_col is not None:
            hdr.setSortIndicatorShown(True)
            hdr.setSortIndicator(self._hdr_sort_col, self._hdr_sort_order)
        else:
            hdr.setSortIndicatorShown(False)


class SubscriptionsView(QWidget):
    """Cadastro + situação mensal (conta)."""

    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._crud = _SubscriptionsCrud()
        self._month = _SubscriptionMonthlyControl()
        self._crud.data_changed.connect(self.data_changed.emit)
        self._month.data_changed.connect(self.data_changed.emit)
        tabs = QTabWidget()
        tabs.addTab(self._crud, "Cadastro")
        tabs.addTab(self._month, "Situação mensal")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs)

    def reload(self) -> None:
        self._crud.reload()
        self._month.reload_table()
