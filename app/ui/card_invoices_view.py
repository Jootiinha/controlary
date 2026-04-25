"""Faturas de cartão por competência."""
from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services import accounts_service, card_invoices_service, cards_service
from app.ui.widgets.card import KpiCard
from app.ui.widgets.crud_page import CrudPage
from app.utils.formatting import format_currency, format_month_br


class _MarkPaidDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Marcar fatura como paga")
        self.dt = QDateEdit()
        self.dt.setDisplayFormat("dd/MM/yyyy")
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())
        self.cmb = QComboBox()
        self.cmb.addItem("(Nenhuma)", None)
        for a in accounts_service.list_all():
            self.cmb.addItem(a.nome, a.id)
        form = QFormLayout()
        form.addRow("Data do pagamento *", self.dt)
        form.addRow("Conta utilizada", self.cmb)
        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(btns)

    def pago_em(self) -> str:
        return self.dt.date().toString("yyyy-MM-dd")

    def conta_id(self) -> int | None:
        d = self.cmb.currentData()
        return int(d) if d is not None else None


class _HistoricoDataDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar fatura (histórico)")
        self.dt = QDateEdit()
        self.dt.setDisplayFormat("dd/MM/yyyy")
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())
        form = QFormLayout()
        form.addRow("Data de referência *", self.dt)
        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(
            QLabel(
                "Apenas registro: não altera saldo em contas nem parcelas pagas."
            )
        )
        lay.addWidget(btns)

    def pago_em(self) -> str:
        return self.dt.date().toString("yyyy-MM-dd")


class CardInvoiceEditorDialog(QDialog):
    def __init__(self, parent, cartao_id: int, ano_mes: str) -> None:
        super().__init__(parent)
        self._cartao_id = cartao_id
        self._ano_mes = ano_mes
        c = cards_service.get(cartao_id)
        nome = c.nome if c else "Cartão"
        self.setWindowTitle(f"Fatura — {nome} · {format_month_br(ano_mes)}")

        self._contained = card_invoices_service.contained_items(cartao_id, ano_mes)
        sug = card_invoices_service.suggested_total(cartao_id, ano_mes)
        inv = card_invoices_service.get(cartao_id, ano_mes)

        tree = QTreeWidget()
        tree.setHeaderLabels(["Descrição", "Valor"])
        p_root = QTreeWidgetItem(["Parcelas no mês", ""])
        for t, val, _iid in self._contained.parcelas:
            QTreeWidgetItem(p_root, [t, format_currency(val)])
        tree.addTopLevelItem(p_root)
        p_root.setExpanded(True)

        s_root = QTreeWidgetItem(["Assinaturas no cartão", ""])
        for t, val in self._contained.assinaturas:
            QTreeWidgetItem(s_root, [t, format_currency(val)])
        tree.addTopLevelItem(s_root)
        s_root.setExpanded(True)

        pay_root = QTreeWidgetItem(["Pagamentos no cartão (mês)", ""])
        for t, val in self._contained.pagamentos_cartao:
            QTreeWidgetItem(pay_root, [t, format_currency(val)])
        tree.addTopLevelItem(pay_root)
        pay_root.setExpanded(True)

        self.sp_valor = QDoubleSpinBox()
        self.sp_valor.setRange(0.0, 9_999_999.0)
        self.sp_valor.setDecimals(2)
        self.sp_valor.setPrefix("R$ ")
        if inv is not None and inv.valor_total > 0:
            self.sp_valor.setValue(inv.valor_total)
        else:
            self.sp_valor.setValue(sug)

        self.lbl_sug = QLabel(f"Total sugerido: {format_currency(sug)}")
        self.lbl_sug.setObjectName("FormHint")

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(56)
        if inv and inv.observacao:
            self.ed_obs.setPlainText(inv.observacao)

        lay = QVBoxLayout(self)
        if inv is not None and inv.historico and inv.status == "paga":
            self._lbl_historico = QLabel(
                "Fatura histórica — sem impacto em saldo ou parcelas."
            )
            self._lbl_historico.setObjectName("FormHint")
            lay.addWidget(self._lbl_historico)
        lay.addWidget(QLabel("Itens que compõem a fatura (somente leitura):"))
        lay.addWidget(tree)
        lay.addWidget(self.lbl_sug)
        lay.addWidget(QLabel("Valor total da fatura *"))
        lay.addWidget(self.sp_valor)
        lay.addWidget(QLabel("Observação"))
        lay.addWidget(self.ed_obs)

        row = QHBoxLayout()
        self.btn_save = QPushButton("Salvar rascunho")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_paid = QPushButton("Marcar como paga")
        self.btn_historico = QPushButton("Registrar histórico")
        row.addWidget(self.btn_save)
        row.addWidget(self.btn_paid)
        row.addWidget(self.btn_historico)
        lay.addLayout(row)

        self.btn_save.clicked.connect(self._save_only)
        self.btn_paid.clicked.connect(self._mark_paid)
        self.btn_historico.clicked.connect(self._mark_historico)

        self._inv_id = inv.id if inv else None
        if inv is not None and inv.status == "paga":
            self.btn_save.setEnabled(False)
            self.btn_paid.setEnabled(False)
            self.btn_historico.setEnabled(False)
            self.btn_save.setToolTip(
                "Fatura paga: use Reabrir na lista para voltar a rascunho."
            )

    def _save_only(self) -> None:
        iid = card_invoices_service.upsert(
            self._cartao_id,
            self._ano_mes,
            float(self.sp_valor.value()),
            "aberta",
            self.ed_obs.toPlainText().strip() or None,
        )
        self._inv_id = iid
        QMessageBox.information(self, "Fatura", "Valores salvos.")
        self.accept()

    def _mark_paid(self) -> None:
        md = _MarkPaidDialog(self)
        if not md.exec():
            return
        iid = card_invoices_service.upsert(
            self._cartao_id,
            self._ano_mes,
            float(self.sp_valor.value()),
            "fechada",
            self.ed_obs.toPlainText().strip() or None,
        )
        self._inv_id = iid
        try:
            card_invoices_service.mark_paid(iid, md.conta_id(), md.pago_em())
        except ValueError as err:
            QMessageBox.warning(self, "Fatura", str(err))
            return
        QMessageBox.information(self, "Fatura", "Fatura marcada como paga.")
        self.accept()

    def _mark_historico(self) -> None:
        hd = _HistoricoDataDialog(self)
        if not hd.exec():
            return
        iid = card_invoices_service.upsert(
            self._cartao_id,
            self._ano_mes,
            float(self.sp_valor.value()),
            "fechada",
            self.ed_obs.toPlainText().strip() or None,
        )
        self._inv_id = iid
        try:
            card_invoices_service.mark_paid_historico(iid, hd.pago_em())
        except ValueError as err:
            QMessageBox.warning(self, "Fatura", str(err))
            return
        QMessageBox.information(
            self, "Fatura", "Fatura registrada no histórico (sem efeito em contas/parcelas)."
        )
        self.accept()


class CardInvoicesView(CrudPage):
    def __init__(self) -> None:
        super().__init__(
            "Faturas de cartão",
            "Por competência: visualize o total sugerido, ajuste o valor e marque como paga após o pagamento.",
            [
                "Cartão",
                "Itens",
                "Sugerido",
                "Valor registrado",
                "Vence em",
                "Status",
            ],
        )
        self.dt = QDateEdit()
        self.dt.setDisplayFormat("MM/yyyy")
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())
        self.dt.dateChanged.connect(lambda: self.reload())

        hb = QHBoxLayout()
        hb.addWidget(QLabel("Competência:"))
        hb.addWidget(self.dt)
        hb.addStretch()
        w = QWidget()
        w.setLayout(hb)
        outer_lay = self.layout()
        if outer_lay is not None:
            outer_lay.insertWidget(1, w)

        self.btn_add.setVisible(False)
        self.btn_edit.setText("Abrir fatura…")
        self.btn_edit.clicked.connect(self._open_selected)
        self.btn_delete.setVisible(False)
        self.table.doubleClicked.connect(lambda _: self._open_selected())
        self._by_card: dict[int, tuple[float, float, str]] = {}
        self.totals_wrap.setVisible(True)
        self._kp_sug = KpiCard("Total sugerido", "-", compact=True)
        self._kp_reg = KpiCard("Total registrado", "-", compact=True)
        self._kp_pagas = KpiCard("Pagas", "-", compact=True)
        self._kp_pend = KpiCard("Pendentes", "-", compact=True)
        self.totals_bar.addWidget(self._kp_sug)
        self.totals_bar.addWidget(self._kp_reg)
        self.totals_bar.addWidget(self._kp_pagas)
        self.totals_bar.addWidget(self._kp_pend)
        self.reload()

    def ano_mes(self) -> str:
        d = self.dt.date()
        return f"{d.year():04d}-{d.month():02d}"

    def _refresh_kpi_cards(self) -> None:
        total_sug = sum(t[0] for t in self._by_card.values())
        total_reg = sum(t[1] for t in self._by_card.values())
        n_pagas = sum(
            1 for t in self._by_card.values() if t[2] in ("paga", "histórico")
        )
        n_pend = len(self._by_card) - n_pagas
        self._kp_sug.set_value(format_currency(total_sug))
        self._kp_reg.set_value(format_currency(total_reg))
        self._kp_pagas.set_value(str(n_pagas))
        self._kp_pend.set_value(str(n_pend))

    def reload(self) -> None:
        ym = self.ano_mes()
        self._by_card.clear()
        rows = []
        for row in card_invoices_service.list_all_cards_with_invoice_hint(ym):
            card = row["card"]
            if card.id is None:
                continue
            cid = card.id
            sug = float(row["suggested"])
            inv = row["invoice"]
            cnt = row["contained_count"]
            valor_reg = float(inv.valor_total) if inv is not None else 0.0
            if inv is None or inv.valor_total <= 0:
                valor_reg = sug
            if inv is not None and inv.historico and inv.status == "paga":
                st = "histórico"
            else:
                st = inv.status if inv is not None else "—"
            self._by_card[cid] = (sug, valor_reg, st)
            d_v = card.dia_pagamento_fatura
            vence = f"Dia {d_v:02d}"
            rows.append((cid, [
                card.nome,
                str(cnt),
                format_currency(sug),
                format_currency(valor_reg),
                vence,
                st,
            ]))
        self.model.set_rows(rows)
        self._ym = ym
        self._refresh_kpi_cards()
        self.refresh_totals()

    def compute_totals(self, visible_ids: list[int]) -> None:
        if not self._by_card:
            self.set_footer_text("", "")
            return
        sug = 0.0
        reg = 0.0
        for cid in visible_ids:
            t = self._by_card.get(cid)
            if t is None:
                continue
            sug += t[0]
            reg += t[1]
        self.set_footer_text(
            f"Sugerido (visíveis): {format_currency(sug)}",
            f"Registrado (visíveis): {format_currency(reg)}",
        )

    def _open_selected(self) -> None:
        cid = self.selected_id()
        if cid is None:
            QMessageBox.information(self, "Fatura", "Selecione um cartão na tabela.")
            return
        dlg = CardInvoiceEditorDialog(self, cid, getattr(self, "_ym", self.ano_mes()))
        if dlg.exec():
            self.reload()
