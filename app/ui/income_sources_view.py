"""Cadastro de fontes de renda mensal."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.income_source import IncomeSource
from app.services import accounts_service, income_months_service, income_sources_service
from app.ui.widgets.card import KpiCard
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency


class IncomeSourceDialog(FormDialog):
    def __init__(self, parent=None, src: Optional[IncomeSource] = None) -> None:
        super().__init__("Editar fonte de renda" if src else "Nova fonte de renda", parent)
        self._src = src

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Salário, freelance, aluguel recebido...")

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 10_000_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(100.0)

        self.ed_dia = QSpinBox()
        self.ed_dia.setRange(1, 31)
        self.ed_dia.setValue(5)

        self.cmb_conta = QComboBox()
        self.cmb_conta.setEditable(False)
        self.cmb_conta.addItem("(Nenhuma — sem crédito automático)", None)
        for a in accounts_service.list_all():
            self.cmb_conta.addItem(a.nome, a.id)

        self.chk_ativo = QCheckBox("Ativa (entra na renda mensal do dashboard)")
        self.chk_ativo.setChecked(True)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Valor mensal *", self.ed_valor)
        self.form.addRow("Dia de recebimento *", self.ed_dia)
        self.form.addRow("Conta de crédito", self.cmb_conta)
        self.form.addRow("", self.chk_ativo)
        self.form.addRow("Observação", self.ed_obs)

        if src:
            self.ed_nome.setText(src.nome)
            self.ed_valor.setValue(src.valor_mensal)
            self.ed_dia.setValue(src.dia_recebimento)
            self.chk_ativo.setChecked(src.ativo)
            self.ed_obs.setPlainText(src.observacao or "")
            if src.account_id is not None:
                for i in range(self.cmb_conta.count()):
                    if self.cmb_conta.itemData(i) == src.account_id:
                        self.cmb_conta.setCurrentIndex(i)
                        break

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        if self.ed_valor.value() <= 0:
            return False, "Valor mensal deve ser maior que zero"
        return True, None

    def payload(self) -> IncomeSource:
        cid = self.cmb_conta.currentData()
        return IncomeSource(
            id=self._src.id if self._src else None,
            nome=self.ed_nome.text().strip(),
            valor_mensal=float(self.ed_valor.value()),
            ativo=self.chk_ativo.isChecked(),
            dia_recebimento=int(self.ed_dia.value()),
            account_id=int(cid) if cid is not None else None,
            observacao=self.ed_obs.toPlainText().strip() or None,
        )


class _IncomeCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Renda",
            "Cadastre uma ou mais fontes de renda mensal. A soma das ativas aparece no dashboard.",
            ["Nome", "Valor mensal", "Dia receb.", "Conta crédito", "Ativa", "Observação"],
        )
        self._by_id: dict[int, IncomeSource] = {}
        self.totals_wrap.setVisible(True)
        self._kp_mensal = KpiCard("Total mensal (ativas)", "-", compact=True)
        self._kp_ativas = KpiCard("Fontes ativas", "-", compact=True)
        self._kp_cad = KpiCard("Fontes cadastradas", "-", compact=True)
        self.totals_bar.addWidget(self._kp_mensal)
        self.totals_bar.addWidget(self._kp_ativas)
        self.totals_bar.addWidget(self._kp_cad)
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def _refresh_kpi_cards(self) -> None:
        total_ativas = sum(
            s.valor_mensal for s in self._by_id.values() if s.ativo
        )
        n_ativas = sum(1 for s in self._by_id.values() if s.ativo)
        self._kp_mensal.set_value(format_currency(total_ativas))
        self._kp_ativas.set_value(str(n_ativas))
        self._kp_cad.set_value(str(len(self._by_id)))

    def reload(self) -> None:
        self._by_id.clear()
        rows = []
        for s in income_sources_service.list_all():
            if s.id is not None:
                self._by_id[s.id] = s
            obs = (s.observacao or "").replace("\n", " ")
            if len(obs) > 80:
                obs = obs[:77] + "..."
            cn = s.conta_nome or "—"
            rows.append((s.id or 0, [
                s.nome,
                format_currency(s.valor_mensal),
                f"Dia {s.dia_recebimento:02d}",
                cn,
                "Sim" if s.ativo else "Não",
                obs or "—",
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
        dlg = IncomeSourceDialog(self)
        if dlg.exec():
            income_sources_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Editar", "Selecione uma fonte de renda.")
            return
        src = income_sources_service.get(sid)
        if src is None:
            return
        dlg = IncomeSourceDialog(self, src)
        if dlg.exec():
            income_sources_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Excluir", "Selecione uma fonte de renda.")
            return
        resp = QMessageBox.question(
            self, "Excluir", "Excluir esta fonte de renda?"
        )
        if resp == QMessageBox.Yes:
            income_sources_service.delete(sid)
            self.reload()
            self.data_changed.emit()


class _IncomeMonthlyControl(QWidget):
    """Marca renda como recebida na competência (crédito no livro-caixa)."""
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        hint = QLabel(
            "Fontes ativas com conta de crédito definida. "
            "Marque como Recebido quando o valor entrar na conta no mês selecionado."
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
        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(
            ["Nome", "Valor", "Conta", "Situação no mês"]
        )
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionMode(QAbstractItemView.NoSelection)
        self.tbl.verticalHeader().setVisible(False)
        lay = QVBoxLayout(self)
        lay.addWidget(hint)
        lay.addLayout(row)
        lay.addWidget(self.tbl, 1)
        self.reload_table()

    def ano_mes(self) -> str:
        d = self.dt.date()
        return f"{d.year():04d}-{d.month():02d}"

    def reload_table(self) -> None:
        ym = self.ano_mes()
        items = [
            s
            for s in income_sources_service.list_all()
            if s.ativo and s.account_id is not None and s.id is not None
        ]
        self.tbl.setRowCount(len(items))
        align_left = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        align_val = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        for i, s in enumerate(items):
            assert s.id is not None
            sid = s.id
            it_n = QTableWidgetItem(s.nome)
            it_n.setTextAlignment(align_left)
            self.tbl.setItem(i, 0, it_n)
            it_v = QTableWidgetItem(format_currency(s.valor_mensal))
            it_v.setTextAlignment(align_val)
            self.tbl.setItem(i, 1, it_v)
            acc = accounts_service.get(int(s.account_id))
            it_c = QTableWidgetItem(acc.nome if acc else "—")
            it_c.setTextAlignment(align_left)
            self.tbl.setItem(i, 2, it_c)
            cb = QComboBox()
            cb.addItems(["Pendente", "Recebido"])
            rec = income_months_service.is_received(sid, ym)
            cb.blockSignals(True)
            cb.setCurrentIndex(1 if rec else 0)
            cb.blockSignals(False)
            cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            def make_handler(src_id: int, combo: QComboBox, competencia: str):
                def on_change(_idx: int) -> None:
                    want = combo.currentIndex() == 1
                    income_months_service.set_month_status(
                        src_id, competencia, recebido=want
                    )
                    self.data_changed.emit()

                return on_change

            cb.currentIndexChanged.connect(make_handler(sid, cb, ym))
            self.tbl.setCellWidget(i, 3, cb)


class IncomeSourcesView(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._crud = _IncomeCrud()
        self._month = _IncomeMonthlyControl()
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
