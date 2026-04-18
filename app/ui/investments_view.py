"""Cadastro de investimentos e evolução por snapshots."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QInputDialog,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)

from app.models.investment import Investment
from app.services import accounts_service, investments_service
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.category_picker import CategoryPicker
from app.ui.widgets.chart_canvas import ChartCanvas
from app.ui.widgets.card import KpiCard
from app.charts import investment_evolution
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency, format_date_br

TIPOS = [
    "CDB", "Tesouro direto", "LCI", "LCA", "Poupança", "Ações", "Fundos", "Outros",
]


def _format_pct_br(value: float, suffix: str) -> str:
    s = f"{value:.2f}".replace(".", ",")
    return f"{s}{suffix}"


def _kpi_value_style(card: KpiCard, gain: float | None) -> None:
    if gain is None:
        card.setStyleSheet("")
        return
    if gain > 0:
        card.setStyleSheet(
            "QFrame#KpiCardCompact QLabel#KpiValue { color: #15803d; }"
        )
    elif gain < 0:
        card.setStyleSheet(
            "QFrame#KpiCardCompact QLabel#KpiValue { color: #B91C1C; }"
        )
    else:
        card.setStyleSheet("")


class InvestmentDialog(FormDialog):
    def __init__(self, parent=None, inv: Optional[Investment] = None) -> None:
        super().__init__("Editar investimento" if inv else "Novo investimento", parent)
        self._inv = inv

        self.cmb_banco = QComboBox()
        for a in accounts_service.list_all():
            self.cmb_banco.addItem(a.nome, a.id)

        self.ed_nome = QLineEdit()

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(TIPOS)

        self.sp_valor = QDoubleSpinBox()
        self.sp_valor.setRange(0.0, 99_999_999.0)
        self.sp_valor.setDecimals(2)
        self.sp_valor.setPrefix("R$ ")

        self.sp_rend = QDoubleSpinBox()
        self.sp_rend.setRange(0.0, 100.0)
        self.sp_rend.setDecimals(2)
        self.sp_rend.setSuffix(" % a.a.")
        self.sp_rend.setSpecialValueText("—")
        self.sp_rend.setValue(0.0)

        self.dt_ini = QDateEdit()
        self.dt_ini.setDisplayFormat("dd/MM/yyyy")
        self.dt_ini.setCalendarPopup(True)
        self.dt_ini.setDate(QDate.currentDate())

        self.dt_fim = QDateEdit()
        self.dt_fim.setDisplayFormat("dd/MM/yyyy")
        self.dt_fim.setCalendarPopup(True)
        self.dt_fim.setSpecialValueText("—")
        self.dt_fim.setMinimumDate(QDate(1900, 1, 1))

        self._picker_cat = CategoryPicker(self, allow_empty=False)
        self._picker_cat.connect_new_button(self._nova_cat)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Banco / conta *", self.cmb_banco)
        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Tipo *", self.cmb_tipo)
        self.form.addRow("Valor aplicado *", self.sp_valor)

        self._lbl_gain = QLabel("—")
        self.form.addRow("Ganho", self._lbl_gain)

        self.form.addRow("Rendimento", self.sp_rend)
        self.form.addRow("Data aplicação *", self.dt_ini)
        self.form.addRow("Vencimento", self.dt_fim)
        self.form.addRow("Categoria *", self._picker_cat)
        self.form.addRow("Observação", self.ed_obs)

        if inv:
            if inv.banco_id is not None:
                for i in range(self.cmb_banco.count()):
                    if self.cmb_banco.itemData(i) == inv.banco_id:
                        self.cmb_banco.setCurrentIndex(i)
                        break
            self.ed_nome.setText(inv.nome)
            idx = self.cmb_tipo.findText(inv.tipo)
            if idx >= 0:
                self.cmb_tipo.setCurrentIndex(idx)
            self.sp_valor.setValue(inv.valor_aplicado)
            if inv.rendimento_percentual_aa is not None:
                self.sp_rend.setValue(inv.rendimento_percentual_aa)
            else:
                self.sp_rend.setValue(0.0)
            self.dt_ini.setDate(QDate.fromString(inv.data_aplicacao, "yyyy-MM-dd"))
            if inv.data_vencimento:
                self.dt_fim.setDate(QDate.fromString(inv.data_vencimento, "yyyy-MM-dd"))
            else:
                self.dt_fim.setDate(QDate(1900, 1, 1))
            if inv.category_id is not None:
                self._picker_cat.set_category_id(inv.category_id)
            self.ed_obs.setPlainText(inv.observacao or "")
            if inv.id is not None:
                self.sp_valor.valueChanged.connect(self._refresh_gain_label)
                self._refresh_gain_label()
        else:
            self.dt_fim.setDate(QDate(1900, 1, 1))

    def _refresh_gain_label(self) -> None:
        if self._inv is None or self._inv.id is None:
            self._lbl_gain.setText("—")
            self._lbl_gain.setStyleSheet("")
            return
        series = investments_service.evolution_series(self._inv.id)
        if not series:
            self._lbl_gain.setText("—")
            self._lbl_gain.setStyleSheet("")
            return
        last_v = series[-1][1]
        gain = last_v - float(self.sp_valor.value())
        self._lbl_gain.setText(format_currency(gain))
        if gain > 0:
            self._lbl_gain.setStyleSheet("color: #15803d;")
        elif gain < 0:
            self._lbl_gain.setStyleSheet("color: #B91C1C;")
        else:
            self._lbl_gain.setStyleSheet("")

    def _nova_cat(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()

    def validate(self) -> tuple[bool, str | None]:
        if self.cmb_banco.currentData() is None:
            return False, "Selecione o banco/conta"
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        if self.sp_valor.value() <= 0:
            return False, "Valor aplicado deve ser maior que zero"
        if self._picker_cat.current_category_id() is None:
            return False, "Selecione uma categoria"
        return True, None

    def payload(self) -> Investment:
        bid = int(self.cmb_banco.currentData())
        rend = self.sp_rend.value() if self.sp_rend.value() > 0 else None
        venc = self.dt_fim.date()
        venc_s = None if venc.year() == 1900 else venc.toString("yyyy-MM-dd")
        return Investment(
            id=self._inv.id if self._inv else None,
            banco_id=bid,
            nome=self.ed_nome.text().strip(),
            tipo=self.cmb_tipo.currentText(),
            valor_aplicado=float(self.sp_valor.value()),
            data_aplicacao=self.dt_ini.date().toString("yyyy-MM-dd"),
            rendimento_percentual_aa=rend,
            data_vencimento=venc_s,
            category_id=self._picker_cat.current_category_id(),
            observacao=self.ed_obs.toPlainText().strip() or None,
            ativo=True,
        )


class _InvestCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Investimentos",
            "Aplicações vinculadas a contas cadastradas.",
            ["Banco", "Nome", "Tipo", "Aplicado", "Categoria", "Início"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def reload(self) -> None:
        rows = []
        for x in investments_service.list_all():
            rows.append((x.id or 0, [
                x.banco_nome or "—",
                x.nome,
                x.tipo,
                format_currency(x.valor_aplicado),
                x.categoria_nome or "—",
                format_date_br(x.data_aplicacao),
            ]))
        self.model.set_rows(rows)

    def _add(self) -> None:
        if not accounts_service.list_all():
            QMessageBox.information(
                self, "Contas", "Cadastre ao menos uma conta em “Contas e cartões”."
            )
            return
        dlg = InvestmentDialog(self)
        if dlg.exec():
            investments_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        iid = self.selected_id()
        if iid is None:
            QMessageBox.information(self, "Editar", "Selecione um investimento.")
            return
        inv = investments_service.get(iid)
        if inv is None:
            return
        dlg = InvestmentDialog(self, inv)
        if dlg.exec():
            investments_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        iid = self.selected_id()
        if iid is None:
            return
        if QMessageBox.question(self, "Excluir", "Excluir este investimento?") != QMessageBox.Yes:
            return
        investments_service.delete(iid)
        self.reload()
        self.data_changed.emit()


class _InvestEvo(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._inv_id: int | None = None

        row = QHBoxLayout()
        row.addWidget(QLabel("Investimento:"))
        self.cmb = QComboBox()
        self.cmb.currentIndexChanged.connect(self._on_inv_change)
        row.addWidget(self.cmb, 1)
        self.btn_atual = QPushButton("Registrar valor hoje")
        self.btn_atual.setObjectName("PrimaryButton")
        self.btn_atual.clicked.connect(self._snapshot_hoje)
        row.addWidget(self.btn_atual)

        self._kp_gain_pct = KpiCard("Ganho médio (%)", "—", compact=True)
        self._kp_gain_rs = KpiCard("Ganho (R$)", "—", compact=True)
        _evo_kpi_w = 152
        for kp in (self._kp_gain_pct, self._kp_gain_rs):
            kp.setFixedWidth(_evo_kpi_w)
            kp.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        row_kpi = QHBoxLayout()
        row_kpi.setSpacing(10)
        row_kpi.addWidget(self._kp_gain_pct, 0)
        row_kpi.addWidget(self._kp_gain_rs, 0)
        row_kpi.addStretch(1)

        self.tbl = QTableWidget(0, 2)
        self.tbl.setHorizontalHeaderLabels(["Data", "Valor"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self._canvas = ChartCanvas(width=7.0, height=3.0, dpi=100)

        lay = QVBoxLayout(self)
        lay.addLayout(row)
        lay.addLayout(row_kpi)
        lay.addWidget(self.tbl)
        lay.addWidget(self._canvas, 1)
        self._reload_combo()

    def _reload_combo(self) -> None:
        self.cmb.blockSignals(True)
        self.cmb.clear()
        for x in investments_service.list_all():
            if x.id is not None:
                self.cmb.addItem(f"{x.nome} ({x.banco_nome})", x.id)
        self.cmb.blockSignals(False)
        if self.cmb.count() > 0:
            self.cmb.setCurrentIndex(0)
            self._on_inv_change()
        else:
            self._inv_id = None
            self._clear_gain_kpis()
            self.tbl.setRowCount(0)
            self._canvas.set_renderer(None)
            self._canvas.refresh()

    def _clear_gain_kpis(self) -> None:
        self._kp_gain_pct.set_value("—")
        self._kp_gain_rs.set_value("—")
        self._kp_gain_pct.set_subtitle("")
        _kpi_value_style(self._kp_gain_pct, None)
        _kpi_value_style(self._kp_gain_rs, None)

    def _on_inv_change(self) -> None:
        iid = self.cmb.currentData()
        if iid is None:
            self._inv_id = None
            self._clear_gain_kpis()
            self.tbl.setRowCount(0)
            self._canvas.set_renderer(None)
            self._canvas.refresh()
            return
        self._inv_id = int(iid)
        self._refresh_table()
        self._canvas.set_renderer(
            investment_evolution.plot_for_investment(self._inv_id)
        )
        self._canvas.refresh()

    def _refresh_table(self) -> None:
        if self._inv_id is None:
            self.tbl.setRowCount(0)
            self._clear_gain_kpis()
            return
        inv = investments_service.get(self._inv_id)
        if inv is None:
            self.tbl.setRowCount(0)
            self._clear_gain_kpis()
            return
        series = investments_service.evolution_series(self._inv_id)
        self.tbl.setRowCount(len(series))
        for i, (d, val) in enumerate(series):
            self.tbl.setItem(i, 0, QTableWidgetItem(format_date_br(d)))
            self.tbl.setItem(i, 1, QTableWidgetItem(format_currency(val)))
        last_v, gain = investments_service.last_value_and_gain(self._inv_id)
        has_snapshots = len(investments_service.list_snapshots(self._inv_id)) > 0
        self._kp_gain_rs.set_value(format_currency(gain))
        _kpi_value_style(self._kp_gain_rs, gain)

        if not has_snapshots:
            self._kp_gain_pct.set_value("—")
            self._kp_gain_pct.set_subtitle("")
            _kpi_value_style(self._kp_gain_pct, None)
            return

        if inv.rendimento_percentual_aa is not None:
            self._kp_gain_pct.set_value(
                _format_pct_br(inv.rendimento_percentual_aa, " % a.a.")
            )
            self._kp_gain_pct.set_subtitle("")
            _kpi_value_style(self._kp_gain_pct, inv.rendimento_percentual_aa)
        elif inv.valor_aplicado > 0:
            total_pct = (last_v / float(inv.valor_aplicado) - 1.0) * 100.0
            self._kp_gain_pct.set_value(_format_pct_br(total_pct, " %"))
            self._kp_gain_pct.set_subtitle("Variação no período")
            _kpi_value_style(self._kp_gain_pct, total_pct)
        else:
            self._kp_gain_pct.set_value("—")
            self._kp_gain_pct.set_subtitle("")
            _kpi_value_style(self._kp_gain_pct, None)

    def _snapshot_hoje(self) -> None:
        if self._inv_id is None:
            return
        inv = investments_service.get(self._inv_id)
        if inv is None:
            return
        from datetime import date

        d = date.today().isoformat()
        val, ok = QInputDialog.getDouble(
            self,
            "Valor na data de hoje",
            "Valor atual (R$):",
            float(inv.valor_aplicado),
            0.0,
            1e12,
            2,
        )
        if not ok:
            return
        investments_service.add_snapshot(self._inv_id, d, float(val))
        self._refresh_table()
        self._canvas.refresh()
        self.data_changed.emit()

    def reload_all(self) -> None:
        self._reload_combo()


class InvestmentsView(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._crud = _InvestCrud()
        self._evo = _InvestEvo()
        self._crud.data_changed.connect(self.data_changed.emit)
        self._crud.data_changed.connect(self._evo.reload_all)
        self._evo.data_changed.connect(self.data_changed.emit)

        tabs = QTabWidget()
        tabs.addTab(self._crud, "Cadastro")
        tabs.addTab(self._evo, "Evolução")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs, 1)

    def reload(self) -> None:
        self._crud.reload()
        self._evo.reload_all()
