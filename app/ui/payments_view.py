"""Tela de CRUD de pagamentos."""
from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QWidget,
)

from app.models.payment import Payment
from app.services import accounts_service, cards_service, payments_service
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.card import KpiCard
from app.ui.widgets.category_picker import CategoryPicker, emit_parent_view_data_changed
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.ui.ui_feedback import show_toast
from app.utils.formatting import format_currency, format_date_br


_KP_TITLE_MES = "Total do mês atual"
_KP_TITLE_GERAL = "Total geral"
_KP_TITLE_PERIODO = "Total no período"
_KP_TITLE_MEDIA = "Média por lançamento"
_KP_TITLE_QTD = "Quantidade"


FORMAS_PAGAMENTO = [
    "Pix",
    "Débito",
    "Crédito",
    "Dinheiro",
    "Boleto",
    "Transferência",
    "Débito Automático",
]


class PaymentDialog(FormDialog):
    def __init__(self, parent=None, payment: Optional[Payment] = None) -> None:
        super().__init__(
            "Editar despesa avulsa" if payment else "Nova despesa avulsa", parent
        )
        self._payment = payment

        self.add_section("Identificação")
        self.ed_descricao = QLineEdit()
        self.ed_descricao.setPlaceholderText("Ex.: Mercado, Farmácia...")

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 1_000_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(10.0)

        self.ed_data = QDateEdit()
        self.ed_data.setDisplayFormat("dd/MM/yyyy")
        self.ed_data.setCalendarPopup(True)
        self.ed_data.setDate(QDate.currentDate())

        self.lbl_data_hint = QLabel(
            "Em conta, débito no saldo a partir da data (ⓘ detalhes no campo Data)."
        )
        self.lbl_data_hint.setWordWrap(True)
        self.lbl_data_hint.setObjectName("FormHint")
        self.ed_data.setToolTip(
            "Em conta: data futura aparece no calendário e em compromissos próximos; "
            "o saldo só considera esse débito a partir dessa data."
        )

        self.cmb_origem = QComboBox()
        self.cmb_origem.setEditable(False)
        self._fill_origem()

        self.lbl_origem = QLabel("")
        self.lbl_origem.setWordWrap(True)
        self.lbl_origem.setObjectName("FormHint")

        self._picker_cat = CategoryPicker(self, allow_empty=False)
        self._picker_cat.connect_new_button(self._nova_categoria)

        self.ed_forma = QComboBox()
        self.ed_forma.addItems(FORMAS_PAGAMENTO)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(70)

        self.form.addRow("Descrição *", self.ed_descricao)
        self.form.addRow("Valor *", self.ed_valor)
        self.form.addRow("Data *", self.ed_data)
        self.form.addRow("", self.lbl_data_hint)
        self.add_section("Origem e categoria")
        self.form.addRow("Origem *", self.cmb_origem)
        self.form.addRow("", self.lbl_origem)
        self.form.addRow("Categoria *", self._picker_cat)
        self.form.addRow("Forma de pagamento *", self.ed_forma)
        self.add_section("Observação")
        self.form.addRow("Observação", self.ed_obs)

        self.cmb_origem.currentIndexChanged.connect(lambda _: self._sync_origem())

        if payment:
            self.ed_descricao.setText(payment.descricao)
            self.ed_valor.setValue(payment.valor)
            self.ed_data.setDate(QDate.fromString(payment.data, "yyyy-MM-dd"))
            if payment.conta_id is not None:
                for i in range(self.cmb_origem.count()):
                    d = self.cmb_origem.itemData(i)
                    if d == f"acc:{payment.conta_id}":
                        self.cmb_origem.setCurrentIndex(i)
                        break
            elif payment.cartao_id is not None:
                for i in range(self.cmb_origem.count()):
                    d = self.cmb_origem.itemData(i)
                    if d == f"card:{payment.cartao_id}":
                        self.cmb_origem.setCurrentIndex(i)
                        break
            idx = self.ed_forma.findText(payment.forma_pagamento)
            if idx >= 0:
                self.ed_forma.setCurrentIndex(idx)
            self.ed_obs.setPlainText(payment.observacao or "")
            if payment.category_id is not None:
                self._picker_cat.set_category_id(payment.category_id)

        self._sync_origem()

    def _sync_origem(self) -> None:
        raw = self.cmb_origem.currentData()
        if not raw or not isinstance(raw, str):
            self.lbl_origem.clear()
            self.ed_forma.setEnabled(True)
            return
        kind, _, mid = raw.partition(":")
        if kind == "card" and mid:
            self.ed_forma.setEnabled(False)
            idx = self.ed_forma.findText("Crédito")
            if idx >= 0:
                self.ed_forma.setCurrentIndex(idx)
            try:
                cid = int(mid)
            except ValueError:
                self.lbl_origem.clear()
                return
            c = cards_service.get(cid)
            if c:
                self.lbl_origem.setText(
                    "Lançamento na fatura do cartão (competência pelo mês da data)."
                )
            else:
                self.lbl_origem.clear()
        else:
            self.lbl_origem.clear()
            self.ed_forma.setEnabled(True)

    def _nova_categoria(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()
            emit_parent_view_data_changed(self)

    def _fill_origem(self) -> None:
        self.cmb_origem.clear()
        self.cmb_origem.addItem("(Selecione conta ou cartão)", None)
        for a in accounts_service.list_all():
            self.cmb_origem.addItem(f"Conta · {a.nome}", f"acc:{a.id}")
        for c in cards_service.list_all():
            self.cmb_origem.addItem(f"Cartão · {c.nome}", f"card:{c.id}")

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_descricao.text().strip():
            return False, "Descrição é obrigatória"
        if self.ed_valor.value() <= 0:
            return False, "Valor deve ser maior que zero"
        if self.cmb_origem.currentData() is None:
            return False, "Selecione conta bancária ou cartão em Contas ou Cartões"
        if self._picker_cat.current_category_id() is None:
            return False, "Selecione uma categoria"
        return True, None

    def payload(self) -> Payment:
        account_id: Optional[int] = None
        card_id: Optional[int] = None
        raw = self.cmb_origem.currentData()
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
        forma = "Crédito" if card_id is not None else self.ed_forma.currentText()
        return Payment(
            id=self._payment.id if self._payment else None,
            valor=float(self.ed_valor.value()),
            descricao=self.ed_descricao.text().strip(),
            data=self.ed_data.date().toString("yyyy-MM-dd"),
            conta_id=account_id,
            cartao_id=card_id,
            forma_pagamento=forma,
            observacao=self.ed_obs.toPlainText().strip() or None,
            category_id=self._picker_cat.current_category_id(),
        )


def _first_last_day_current_month() -> tuple[date, date]:
    today = date.today()
    _, last_d = monthrange(today.year, today.month)
    return today.replace(day=1), today.replace(day=last_d)


def _qdate_to_date(qd: QDate) -> date:
    return date(qd.year(), qd.month(), qd.day())


class PaymentsView(CrudPage):
    def __init__(self) -> None:
        super().__init__(
            "Despesas avulsas",
            "Gastos pontuais em conta ou cartão; o livro-caixa reflete débitos em conta quando aplicável.",
            ["Data", "Descrição", "Origem", "Categoria", "Forma", "Valor", "Observação"],
        )
        self._by_id: dict[int, Payment] = {}
        self.totals_wrap.setVisible(True)
        self._kp_mes = KpiCard(_KP_TITLE_MES, "-", compact=True)
        self._kp_geral = KpiCard(_KP_TITLE_GERAL, "-", compact=True)
        self._kp_qtd = KpiCard(_KP_TITLE_QTD, "-", compact=True)
        self.totals_bar.addWidget(self._kp_mes)
        self.totals_bar.addWidget(self._kp_geral)
        self.totals_bar.addWidget(self._kp_qtd)

        d_ini, d_fim = _first_last_day_current_month()
        self._chk_limit_date = QCheckBox("Limitar por data")
        self._ed_date_de = QDateEdit()
        self._ed_date_de.setDisplayFormat("dd/MM/yyyy")
        self._ed_date_de.setCalendarPopup(True)
        self._ed_date_de.setDate(QDate(d_ini.year, d_ini.month, d_ini.day))
        self._ed_date_ate = QDateEdit()
        self._ed_date_ate.setDisplayFormat("dd/MM/yyyy")
        self._ed_date_ate.setCalendarPopup(True)
        self._ed_date_ate.setDate(QDate(d_fim.year, d_fim.month, d_fim.day))
        self._ed_date_de.setEnabled(False)
        self._ed_date_ate.setEnabled(False)
        filter_row = QWidget()
        fl = QHBoxLayout(filter_row)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addWidget(self._chk_limit_date)
        fl.addWidget(QLabel("De"))
        fl.addWidget(self._ed_date_de)
        fl.addWidget(QLabel("Até"))
        fl.addWidget(self._ed_date_ate)
        fl.addStretch()
        self.toolbar_layout.insertWidget(4, filter_row)
        self.add_filter_chips([("all", "Todos"), ("month", "Mês atual")])
        self._chk_limit_date.stateChanged.connect(self._on_limit_date_toggled)
        self._ed_date_de.dateChanged.connect(self._on_date_filter_changed)
        self._ed_date_ate.dateChanged.connect(self._on_date_filter_changed)

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def on_filter_chip_selected(self, chip_id: str) -> None:
        if chip_id == "month":
            if not self._chk_limit_date.isChecked():
                self._chk_limit_date.setChecked(True)
            return
        if chip_id == "all":
            if self._chk_limit_date.isChecked():
                self._chk_limit_date.setChecked(False)

    def _on_limit_date_toggled(self, _state: int) -> None:
        on = self._chk_limit_date.isChecked()
        self._ed_date_de.setEnabled(on)
        self._ed_date_ate.setEnabled(on)
        self.reload()

    def _on_date_filter_changed(self, _d: QDate) -> None:
        if self._chk_limit_date.isChecked():
            self.reload()

    def _refresh_kpi_cards(self) -> None:
        if self._chk_limit_date.isChecked():
            total_periodo = sum(p.valor for p in self._by_id.values())
            n = len(self._by_id)
            media = total_periodo / n if n else 0.0
            self._kp_mes.set_title(_KP_TITLE_PERIODO)
            self._kp_mes.set_value(format_currency(total_periodo))
            self._kp_geral.set_title(_KP_TITLE_MEDIA)
            self._kp_geral.set_value(format_currency(media) if n else "—")
            self._kp_qtd.set_title(_KP_TITLE_QTD)
            self._kp_qtd.set_value(str(n))
        else:
            today = date.today()
            ym = f"{today.year:04d}-{today.month:02d}"
            total_mes = 0.0
            total_geral = 0.0
            for p in self._by_id.values():
                total_geral += p.valor
                if p.data.startswith(ym):
                    total_mes += p.valor
            self._kp_mes.set_title(_KP_TITLE_MES)
            self._kp_mes.set_value(format_currency(total_mes))
            self._kp_geral.set_title(_KP_TITLE_GERAL)
            self._kp_geral.set_value(format_currency(total_geral))
            self._kp_qtd.set_title(_KP_TITLE_QTD)
            self._kp_qtd.set_value(str(len(self._by_id)))

    def reload(self) -> None:
        if self._chk_limit_date.isChecked():
            d0 = _qdate_to_date(self._ed_date_de.date())
            d1 = _qdate_to_date(self._ed_date_ate.date())
            if d0 > d1:
                QMessageBox.warning(
                    self,
                    "Período",
                    "A data inicial não pode ser posterior à data final.",
                )
                return

        self._by_id.clear()
        rows: list[tuple[int, list[str]]] = []
        if self._chk_limit_date.isChecked():
            d0 = _qdate_to_date(self._ed_date_de.date())
            d1 = _qdate_to_date(self._ed_date_ate.date())
            payments_iter = payments_service.list_between(d0, d1)
        else:
            payments_iter = payments_service.list_all()
        for p in payments_iter:
            if p.id is not None:
                self._by_id[p.id] = p
            nome = p.conta_nome or p.cartao_nome or "—"
            cat = p.categoria_nome or "—"
            rows.append((p.id or 0, [
                format_date_br(p.data),
                p.descricao,
                nome,
                cat,
                p.forma_pagamento,
                format_currency(p.valor),
                p.observacao or "",
            ]))
        self.model.set_rows(rows)
        self._refresh_kpi_cards()
        self.refresh_totals()

    def compute_totals(self, visible_ids: list[int]) -> None:
        if not self._by_id:
            self.set_footer_text("", "")
            return
        vis = [self._by_id[i] for i in visible_ids if i in self._by_id]
        total = sum(p.valor for p in vis)
        self.set_footer_text(
            f"Total (visíveis): {format_currency(total)}",
            f"Itens: {len(vis)}",
        )

    def _add(self) -> None:
        if not accounts_service.list_all() and not cards_service.list_all():
            QMessageBox.information(
                self,
                "Cadastre uma origem",
                "Cadastre ao menos uma conta ou cartão em Contas ou Cartões.",
            )
            return
        dlg = PaymentDialog(self)
        if dlg.exec():
            pay = dlg.payload()
            payments_service.create(pay)
            origem = "—"
            if pay.conta_id is not None:
                a = accounts_service.get_or_unknown(pay.conta_id, "Conta")
                origem = a.nome
            elif pay.cartao_id is not None:
                c = cards_service.get_or_unknown(pay.cartao_id, "Cartão")
                origem = f"Cartão · {c.nome}"
            show_toast(
                f"Despesa avulsa registrada: {pay.descricao} · {format_currency(pay.valor)} · {origem}"
            )
            self.reload()

    def _edit(self) -> None:
        pid = self.selected_id()
        if pid is None:
            QMessageBox.information(self, "Editar", "Selecione um pagamento na tabela.")
            return
        payment = payments_service.get(pid)
        if payment is None:
            return
        dlg = PaymentDialog(self, payment)
        if dlg.exec():
            pay = dlg.payload()
            payments_service.update(pay)
            origem = "—"
            if pay.conta_id is not None:
                a = accounts_service.get_or_unknown(pay.conta_id, "Conta")
                origem = a.nome
            elif pay.cartao_id is not None:
                c = cards_service.get_or_unknown(pay.cartao_id, "Cartão")
                origem = f"Cartão · {c.nome}"
            show_toast(
                f"Despesa avulsa atualizada: {pay.descricao} · {format_currency(pay.valor)} · {origem}"
            )
            self.reload()

    def _delete(self) -> None:
        pid = self.selected_id()
        if pid is None:
            QMessageBox.information(self, "Excluir", "Selecione um pagamento na tabela.")
            return
        resp = QMessageBox.question(
            self,
            "Excluir pagamento",
            "Excluir este pagamento remove o registro; se houver débito em conta no "
            "livro-caixa associado a ele, esse lançamento também será removido.",
        )
        if resp == QMessageBox.Yes:
            payments_service.delete(pid)
            self.reload()
