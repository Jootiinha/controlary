"""Cadastro de investimentos e evolução por snapshots."""
from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QInputDialog,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.charts import investment_evolution_overview
from app.models.investment import Investment
from app.services import accounts_service, investments_service
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.category_picker import CategoryPicker, emit_parent_view_data_changed
from app.ui.widgets.card import KpiCard
from app.ui.widgets.chart_canvas import ChartCanvas
from app.ui.ui_wait import wait_cursor
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency, format_date_br

TIPOS = [
    "CDB", "Tesouro direto", "LCI", "LCA", "Poupança", "Ações", "Fundos", "Outros",
]


def _fmt_pct_carteira(pct: float | None) -> str:
    if pct is None:
        return "—"
    s = f"{pct:.2f}".replace(".", ",")
    return f"{s} %"


def _kpi_carteira_style(card: KpiCard, signed: float | None) -> None:
    if signed is None or signed == 0:
        trend = "neutral"
    elif signed > 0:
        trend = "positive"
    else:
        trend = "negative"
    card.setProperty("kpiTrend", trend)
    card.style().unpolish(card)
    card.style().polish(card)


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
        self.sp_rend.setReadOnly(True)
        self.sp_rend.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.sp_rend.setToolTip(
            "Calculado automaticamente a partir dos registros de evolução (snapshots)."
        )

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
            self._lbl_gain.setObjectName("")
            self._lbl_gain.style().unpolish(self._lbl_gain)
            self._lbl_gain.style().polish(self._lbl_gain)
            return
        series = investments_service.evolution_series(self._inv.id)
        if not series:
            self._lbl_gain.setText("—")
            self._lbl_gain.setObjectName("")
            self._lbl_gain.style().unpolish(self._lbl_gain)
            self._lbl_gain.style().polish(self._lbl_gain)
            return
        last_v = series[-1][1]
        gain = last_v - float(self.sp_valor.value())
        self._lbl_gain.setText(format_currency(gain))
        if gain > 0:
            self._lbl_gain.setObjectName("PositiveDelta")
        elif gain < 0:
            self._lbl_gain.setObjectName("NegativeDelta")
        else:
            self._lbl_gain.setObjectName("")
        self._lbl_gain.style().unpolish(self._lbl_gain)
        self._lbl_gain.style().polish(self._lbl_gain)

    def _nova_cat(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()
            emit_parent_view_data_changed(self)

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
        self.btn_registrar_hoje = QPushButton("Registrar valor hoje")
        self.btn_registrar_hoje.setObjectName("PrimaryButton")
        self.btn_registrar_hoje.setToolTip(
            "Gravar o valor atual do investimento selecionado para a data de hoje"
        )
        self.btn_registrar_hoje.clicked.connect(self._registrar_valor_hoje)
        idx = self.toolbar_layout.indexOf(self.btn_delete)
        self.toolbar_layout.insertWidget(idx + 1, self.btn_registrar_hoje)

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

    def _registrar_valor_hoje(self) -> None:
        iid = self.selected_id()
        if iid is None:
            QMessageBox.information(
                self, "Investimentos", "Selecione um investimento na tabela."
            )
            return
        inv = investments_service.get(iid)
        if inv is None:
            return
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
        investments_service.add_snapshot(iid, d, float(val))
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
    def __init__(self) -> None:
        super().__init__()
        lbl = QLabel(
            "Visão consolidada de todos os investimentos ativos. "
            "O patrimônio soma o valor de cada aplicação nas datas registradas."
        )
        lbl.setObjectName("PageSubtitle")
        lbl.setWordWrap(True)

        self._kp_ganho = KpiCard(
            "Ganho total da carteira (R$)", "—", compact=True, compact_style="tall_narrow"
        )
        self._kp_var = KpiCard(
            "Variação total da carteira (%)", "—", compact=True, compact_style="tall_narrow"
        )
        row_kpi = QHBoxLayout()
        row_kpi.setSpacing(10)
        row_kpi.addWidget(self._kp_ganho, 1)
        row_kpi.addWidget(self._kp_var, 1)

        self._canvas_pat = ChartCanvas(
            investment_evolution_overview.plot_patrimonio_total(),
            width=7.0,
            height=3.2,
            dpi=100,
        )
        self._canvas_inv = ChartCanvas(
            investment_evolution_overview.plot_todos_investimentos(),
            width=7.0,
            height=3.2,
            dpi=100,
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(lbl)
        lay.addLayout(row_kpi)
        lay.addWidget(self._canvas_pat, 1)
        lay.addWidget(self._canvas_inv, 1)
        self._refresh_kpis()

    def _refresh_kpis(self) -> None:
        invs = investments_service.list_all()
        if not invs:
            self._kp_ganho.set_value("—")
            self._kp_var.set_value("—")
            _kpi_carteira_style(self._kp_ganho, None)
            _kpi_carteira_style(self._kp_var, None)
            return
        ganho, pct = investments_service.portfolio_carteira_gain_metrics()
        self._kp_ganho.set_value(format_currency(ganho))
        _kpi_carteira_style(self._kp_ganho, ganho)
        if pct is None:
            self._kp_var.set_value("—")
            _kpi_carteira_style(self._kp_var, None)
        else:
            self._kp_var.set_value(_fmt_pct_carteira(pct))
            _kpi_carteira_style(self._kp_var, pct)

    def reload_all(self) -> None:
        self._refresh_kpis()
        self._canvas_pat.set_renderer(investment_evolution_overview.plot_patrimonio_total())
        self._canvas_pat.refresh()
        self._canvas_inv.set_renderer(
            investment_evolution_overview.plot_todos_investimentos()
        )
        self._canvas_inv.refresh()


class InvestmentsView(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._crud = _InvestCrud()
        self._evo = _InvestEvo()
        self._crud.data_changed.connect(self.data_changed.emit)
        self._crud.data_changed.connect(self._evo.reload_all)

        tabs = QTabWidget()
        tabs.addTab(self._crud, "Cadastro")
        tabs.addTab(self._evo, "Evolução")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs, 1)

    def reload(self) -> None:
        with wait_cursor():
            self._crud.reload()
            self._evo.reload_all()
