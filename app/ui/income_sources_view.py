"""Cadastro de fontes de renda (recorrente, avulsa e parcelada)."""
from __future__ import annotations

from typing import Optional, Sequence

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
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

from app.models.income_source import IncomeSource
from app.services import accounts_service, income_months_service, income_sources_service
from app.ui.widgets.card import KpiCard
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import current_month, format_currency

FORMAS_RECEBIMENTO = [
    "Pix",
    "Transferência",
    "Dinheiro",
    "Boleto",
    "Cheque",
    "VR/VA",
]


def _format_ano_mes(ym: str | None) -> str:
    if not ym or len(ym) < 7:
        return "—"
    return f"{ym[5:7]}/{ym[0:4]}"


class IncomeSourceDialog(FormDialog):
    def __init__(
        self,
        parent=None,
        src: Optional[IncomeSource] = None,
        allowed_tipos: Sequence[str] = ("recorrente", "avulsa", "parcelada"),
    ) -> None:
        tit = "Editar fonte de renda" if src else "Nova fonte de renda"
        super().__init__(tit, parent)
        self._src = src
        self._allowed = tuple(allowed_tipos)

        self.cmb_tipo = QComboBox()
        tipo_labels = {
            "recorrente": "Recorrente (salário, aluguel…)",
            "avulsa": "Avulsa (um mês)",
            "parcelada": "Avulsa parcelada",
        }
        for k in self._allowed:
            self.cmb_tipo.addItem(tipo_labels[k], k)
        self.cmb_tipo.currentIndexChanged.connect(self._on_tipo_changed)

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Salário, serviço, aluguel recebido…")

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 10_000_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(100.0)

        self.dt_mes_ref = QDateEdit()
        self.dt_mes_ref.setDisplayFormat("MM/yyyy")
        self.dt_mes_ref.setCalendarPopup(True)
        self.dt_mes_ref.setDate(QDate.currentDate())

        self.ed_dia = QSpinBox()
        self.ed_dia.setRange(1, 31)
        self.ed_dia.setValue(5)

        self.sp_total_parcelas = QSpinBox()
        self.sp_total_parcelas.setRange(1, 999)
        self.sp_total_parcelas.setValue(12)

        self.sp_parcelas_recebidas = QSpinBox()
        self.sp_parcelas_recebidas.setRange(0, 999)
        self.sp_parcelas_recebidas.setValue(0)
        self.sp_total_parcelas.valueChanged.connect(self._ajusta_max_parcelas_recebidas)

        self.cmb_forma = QComboBox()
        self.cmb_forma.addItem("(Não informado)", None)
        for f in FORMAS_RECEBIMENTO:
            self.cmb_forma.addItem(f, f)

        self.cmb_conta = QComboBox()
        self.cmb_conta.setEditable(False)
        self.cmb_conta.addItem("(Nenhuma — sem crédito automático)", None)
        for a in accounts_service.list_all():
            self.cmb_conta.addItem(a.nome, a.id)

        self.chk_ativo = QCheckBox("Ativa (entra na renda do mês quando aplicável)")
        self.chk_ativo.setChecked(True)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Tipo *", self.cmb_tipo)
        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Valor *", self.ed_valor)
        self._row_mes = self.form.rowCount()
        self.form.addRow("Mês referência *", self.dt_mes_ref)
        self.form.addRow("Total de parcelas *", self.sp_total_parcelas)
        self.form.addRow("Parcelas já recebidas *", self.sp_parcelas_recebidas)
        self.form.addRow("Dia de recebimento *", self.ed_dia)
        self.form.addRow("Forma de recebimento", self.cmb_forma)
        self.form.addRow("Conta de crédito", self.cmb_conta)
        self.form.addRow("", self.chk_ativo)
        self.form.addRow("Observação", self.ed_obs)

        if src:
            self._load_src(src)
        self._on_tipo_changed()

    def _ajusta_max_parcelas_recebidas(self, _v: int) -> None:
        self.sp_parcelas_recebidas.setMaximum(self.sp_total_parcelas.value())

    def _load_src(self, src: IncomeSource) -> None:
        self.cmb_tipo.blockSignals(True)
        self.ed_nome.setText(src.nome)
        self.ed_valor.setValue(src.valor_mensal)
        self.ed_dia.setValue(src.dia_recebimento)
        self.chk_ativo.setChecked(src.ativo)
        self.ed_obs.setPlainText(src.observacao or "")
        for i in range(self.cmb_tipo.count()):
            if self.cmb_tipo.itemData(i) == src.tipo:
                self.cmb_tipo.setCurrentIndex(i)
                break
        if src.mes_referencia:
            y, m = map(int, src.mes_referencia.split("-"))
            self.dt_mes_ref.setDate(QDate(y, m, 1))
        if src.total_parcelas is not None:
            self.sp_total_parcelas.setValue(src.total_parcelas)
        self.sp_parcelas_recebidas.setValue(src.parcelas_recebidas)
        self._ajusta_max_parcelas_recebidas(self.sp_total_parcelas.value())
        if src.forma_recebimento:
            for i in range(self.cmb_forma.count()):
                if self.cmb_forma.itemData(i) == src.forma_recebimento:
                    self.cmb_forma.setCurrentIndex(i)
                    break
        if src.account_id is not None:
            for i in range(self.cmb_conta.count()):
                if self.cmb_conta.itemData(i) == src.account_id:
                    self.cmb_conta.setCurrentIndex(i)
                    break
        self.cmb_tipo.blockSignals(False)

    def _on_tipo_changed(self, _idx: int = 0) -> None:
        t = self.cmb_tipo.currentData()
        is_rec = t == "recorrente"
        is_par = t == "parcelada"
        self._set_row_visible(self._row_mes, not is_rec)
        self._set_row_visible(self._row_mes + 1, is_par)
        self._set_row_visible(self._row_mes + 2, is_par)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSuffix(" / parcela" if is_par else "")

    def _set_row_visible(self, row: int, vis: bool) -> None:
        li = self.form.itemAt(row, QFormLayout.LabelRole)
        fi = self.form.itemAt(row, QFormLayout.FieldRole)
        if li and li.widget():
            li.widget().setVisible(vis)
        if fi and fi.widget():
            fi.widget().setVisible(vis)

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        if self.ed_valor.value() <= 0:
            return False, "Valor deve ser maior que zero"
        t = self.cmb_tipo.currentData()
        if t in ("avulsa", "parcelada") and not self.dt_mes_ref.date().isValid():
            return False, "Mês de referência inválido"
        if t == "parcelada":
            if self.sp_total_parcelas.value() < 1:
                return False, "Informe o total de parcelas"
            if self.sp_parcelas_recebidas.value() > self.sp_total_parcelas.value():
                return False, "Parcelas recebidas não pode exceder o total"
        return True, None

    def payload(self) -> IncomeSource:
        cid = self.cmb_conta.currentData()
        fid = self.cmb_forma.currentData()
        t = str(self.cmb_tipo.currentData())
        d = self.dt_mes_ref.date()
        mes_ref = f"{d.year():04d}-{d.month():02d}" if t != "recorrente" else None
        total_p = self.sp_total_parcelas.value() if t == "parcelada" else None
        pr = self.sp_parcelas_recebidas.value() if t == "parcelada" else 0
        return IncomeSource(
            id=self._src.id if self._src else None,
            nome=self.ed_nome.text().strip(),
            valor_mensal=float(self.ed_valor.value()),
            ativo=self.chk_ativo.isChecked(),
            dia_recebimento=int(self.ed_dia.value()),
            account_id=int(cid) if cid is not None else None,
            observacao=self.ed_obs.toPlainText().strip() or None,
            tipo=t,
            mes_referencia=mes_ref,
            total_parcelas=total_p,
            parcelas_recebidas=pr,
            forma_recebimento=str(fid) if fid else None,
        )


class _IncomeCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Renda recorrente",
            "Salário, aluguéis e outras rendas que se repetem todo mês.",
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
        ym = current_month()
        total_ativas = sum(
            s.valor_mensal
            for s in self._by_id.values()
            if s.ativo and income_sources_service.applies_to_month(s, ym)
        )
        n_ativas = sum(1 for s in self._by_id.values() if s.ativo)
        self._kp_mensal.set_value(format_currency(total_ativas))
        self._kp_ativas.set_value(str(n_ativas))
        self._kp_cad.set_value(str(len(self._by_id)))

    def reload(self) -> None:
        self._by_id.clear()
        rows = []
        for s in income_sources_service.list_all():
            if s.tipo != "recorrente":
                continue
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
        ym = current_month()
        if not self._by_id:
            self.set_footer_text("", "")
            return
        vis = [self._by_id[i] for i in visible_ids if i in self._by_id]
        total = sum(
            s.valor_mensal
            for s in vis
            if income_sources_service.applies_to_month(s, ym)
        )
        self.set_footer_text(
            f"Total no mês (visíveis): {format_currency(total)}",
            f"Itens: {len(vis)}",
        )

    def _add(self) -> None:
        dlg = IncomeSourceDialog(self, allowed_tipos=("recorrente",))
        if dlg.exec():
            try:
                income_sources_service.create(dlg.payload())
            except ValueError as e:
                QMessageBox.warning(self, "Validação", str(e))
                return
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
        dlg = IncomeSourceDialog(self, src, allowed_tipos=("recorrente",))
        if dlg.exec():
            try:
                income_sources_service.update(dlg.payload())
            except ValueError as e:
                QMessageBox.warning(self, "Validação", str(e))
                return
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


class _IncomeAvulsasCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Rendas avulsas",
            "Serviços e outros recebimentos pontuais ou parcelados.",
            [
                "Nome",
                "Tipo",
                "Valor",
                "Mês ref.",
                "Parcelas",
                "Total recebido",
                "A receber",
                "Forma",
                "Conta",
                "Ativa",
                "Observação",
            ],
        )
        self._by_id: dict[int, IncomeSource] = {}
        self.totals_wrap.setVisible(True)
        self._kp_mes = KpiCard("Total no mês atual", "-", compact=True)
        self._kp_a_receber = KpiCard("Saldo a receber", "-", compact=True)
        self._kp_cad = KpiCard("Cadastradas", "-", compact=True)
        self.totals_bar.addWidget(self._kp_mes)
        self.totals_bar.addWidget(self._kp_a_receber)
        self.totals_bar.addWidget(self._kp_cad)
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def _tipo_label(self, s: IncomeSource) -> str:
        return {"avulsa": "Avulsa", "parcelada": "Parcelada"}.get(s.tipo, s.tipo)

    def _parcelas_txt(self, s: IncomeSource) -> str:
        if s.tipo != "parcelada" or s.total_parcelas is None:
            return "—"
        return f"{s.parcelas_recebidas}/{s.total_parcelas}"

    def _refresh_kpi_cards(self) -> None:
        ym = current_month()
        total = sum(
            s.valor_mensal
            for s in self._by_id.values()
            if income_sources_service.applies_to_month(s, ym)
        )
        a_receber = sum(
            income_sources_service.paid_remaining(s)[1]
            for s in self._by_id.values()
        )
        self._kp_mes.set_value(format_currency(total))
        self._kp_a_receber.set_value(format_currency(a_receber))
        self._kp_cad.set_value(str(len(self._by_id)))

    def reload(self) -> None:
        self._by_id.clear()
        rows = []
        for s in income_sources_service.list_all():
            if s.tipo not in ("avulsa", "parcelada"):
                continue
            if s.id is not None:
                self._by_id[s.id] = s
            obs = (s.observacao or "").replace("\n", " ")
            if len(obs) > 60:
                obs = obs[:57] + "..."
            cn = s.conta_nome or "—"
            forma = s.forma_recebimento or "—"
            recebido, a_receber = income_sources_service.paid_remaining(s)
            rows.append((s.id or 0, [
                s.nome,
                self._tipo_label(s),
                format_currency(s.valor_mensal),
                _format_ano_mes(s.mes_referencia),
                self._parcelas_txt(s),
                format_currency(recebido),
                format_currency(a_receber),
                forma,
                cn,
                "Sim" if s.ativo else "Não",
                obs or "—",
            ]))
        self.model.set_rows(rows)
        self._refresh_kpi_cards()
        self.refresh_totals()

    def compute_totals(self, visible_ids: list[int]) -> None:
        ym = current_month()
        if not self._by_id:
            self.set_footer_text("", "")
            return
        vis = [self._by_id[i] for i in visible_ids if i in self._by_id]
        total = sum(
            s.valor_mensal
            for s in vis
            if income_sources_service.applies_to_month(s, ym)
        )
        self.set_footer_text(
            f"Total no mês (visíveis): {format_currency(total)}",
            f"Itens: {len(vis)}",
        )

    def _add(self) -> None:
        dlg = IncomeSourceDialog(self, allowed_tipos=("avulsa", "parcelada"))
        if dlg.exec():
            try:
                income_sources_service.create(dlg.payload())
            except ValueError as e:
                QMessageBox.warning(self, "Validação", str(e))
                return
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Editar", "Selecione um item.")
            return
        src = income_sources_service.get(sid)
        if src is None:
            return
        dlg = IncomeSourceDialog(self, src, allowed_tipos=("avulsa", "parcelada"))
        if dlg.exec():
            try:
                income_sources_service.update(dlg.payload())
            except ValueError as e:
                QMessageBox.warning(self, "Validação", str(e))
                return
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Excluir", "Selecione um item.")
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
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        hint = QLabel(
            "Fontes com conta de crédito definida e competência no mês selecionado. "
            "Marque como Recebido quando o valor entrar na conta."
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
            min_height=120,
            vertical_header_default_section_size=44,
            size_policy=(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
        )
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
            if s.account_id is not None
            and s.id is not None
            and income_sources_service.applies_to_month(s, ym)
        ]
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
        self._avulsas = _IncomeAvulsasCrud()
        self._month = _IncomeMonthlyControl()
        self._crud.data_changed.connect(self.data_changed.emit)
        self._avulsas.data_changed.connect(self.data_changed.emit)
        self._month.data_changed.connect(self.data_changed.emit)
        tabs = QTabWidget()
        tabs.addTab(self._crud, "Recorrentes")
        tabs.addTab(self._avulsas, "Avulsas e parceladas")
        tabs.addTab(self._month, "Situação mensal")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs, 1)

    def reload(self) -> None:
        self._crud.reload()
        self._avulsas.reload()
        self._month.reload_table()
