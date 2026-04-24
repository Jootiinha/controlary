"""Cadastro de fontes de renda (recorrente, avulsa e parcelada)."""
from __future__ import annotations

from typing import Optional, Sequence

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.income_source import IncomeSource
from app.services import (
    accounts_service,
    calendar_service,
    income_months_service,
    income_sources_service,
    kpi_service,
)
from app.ui.widgets.card import KpiCard
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.utils.formatting import current_month, format_currency, format_date_br

_OVERVIEW_KPI_MIN_W = 168

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


class IncomeMonthReceiptDialog(FormDialog):
    """Valor e conta do crédito no livro-caixa para uma competência."""

    def __init__(
        self,
        parent: Optional[QWidget],
        nome_fonte: str,
        default_valor: float,
        default_account_id: Optional[int],
    ) -> None:
        super().__init__(f"Recebimento — {nome_fonte}", parent)
        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.01, 10_000_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(100.0)
        self.ed_valor.setValue(float(default_valor))

        self.cmb_conta = QComboBox()
        self.cmb_conta.setEditable(False)
        for a in accounts_service.list_all():
            self.cmb_conta.addItem(a.nome, a.id)
        if default_account_id is not None:
            for i in range(self.cmb_conta.count()):
                if self.cmb_conta.itemData(i) == default_account_id:
                    self.cmb_conta.setCurrentIndex(i)
                    break

        self.form.addRow("Valor creditado *", self.ed_valor)
        self.form.addRow("Conta de recebimento *", self.cmb_conta)

    def validate(self) -> tuple[bool, str | None]:
        if self.ed_valor.value() <= 0:
            return False, "Valor deve ser maior que zero"
        if self.cmb_conta.count() == 0:
            return False, "Cadastre uma conta em Contas e cartões"
        if self.cmb_conta.currentData() is None:
            return False, "Selecione a conta de recebimento"
        return True, None

    def receipt_payload(self) -> tuple[float, int]:
        return float(self.ed_valor.value()), int(self.cmb_conta.currentData())


class _IncomeOverviewTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        hint = QLabel(
            "Estes números são sempre do mês civil corrente (hoje), independentemente da "
            "competência escolhida na aba Recebimentos. «Renda pendente»: fontes com "
            "competência neste mês ainda não marcadas como recebidas."
        )
        hint.setWordWrap(True)
        hint.setObjectName("FormHint")

        self._kp_esp = KpiCard("Renda esperada", "-", compact=True)
        self._kp_rec = KpiCard("Renda recebida (livro)", "-", compact=True)
        self._kp_pend = KpiCard("Renda pendente", "-", compact=True)
        self._kp_prev = KpiCard("Despesa prevista", "-", compact=True)

        kpi_grid = QGridLayout()
        kpi_grid.setContentsMargins(0, 0, 0, 0)
        kpi_grid.setHorizontalSpacing(12)
        kpi_grid.setVerticalSpacing(12)
        for c in range(2):
            kpi_grid.setColumnMinimumWidth(c, _OVERVIEW_KPI_MIN_W)
            kpi_grid.setColumnStretch(c, 1)
        align = Qt.AlignmentFlag.AlignTop
        kpi_grid.addWidget(self._kp_esp, 0, 0, 1, 1, align)
        kpi_grid.addWidget(self._kp_rec, 0, 1, 1, 1, align)
        kpi_grid.addWidget(self._kp_pend, 1, 0, 1, 1, align)
        kpi_grid.addWidget(self._kp_prev, 1, 1, 1, 1, align)

        grp_kpi = QGroupBox("Indicadores — mês atual")
        grp_kpi.setLayout(kpi_grid)

        self.lbl_ent = QLabel(
            f"Próximas entradas (próx. {calendar_service.UPCOMING_HORIZON_DAYS} dias)"
        )
        self.lbl_ent.setObjectName("PageSubtitle")
        self.tbl_ent = ReadOnlyTable(
            ["Data", "Descrição", "Valor"],
            min_height=160,
            size_policy=(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(hint)
        lay.addWidget(grp_kpi)
        lay.addWidget(self.lbl_ent)
        lay.addWidget(self.tbl_ent, 1)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def reload(self) -> None:
        ym = current_month()
        k = kpi_service.for_month(ym)
        self._kp_esp.set_value(format_currency(k.renda_esperada))
        self._kp_rec.set_value(format_currency(k.renda_recebida))
        self._kp_pend.set_value(format_currency(k.renda_pendente))
        self._kp_prev.set_value(format_currency(k.despesa_prevista))
        evs = calendar_service.upcoming_receivables(
            calendar_service.UPCOMING_HORIZON_DAYS
        )
        if not evs:
            self.tbl_ent.set_rows(
                [],
                empty_row=["—", "Nada neste período", "—"],
            )
            return
        self.tbl_ent.set_rows(
            [
                [
                    format_date_br(ev.data),
                    ev.titulo,
                    format_currency(ev.valor),
                ]
                for ev in evs
            ],
            sort_keys=[
                [ev.data, (ev.titulo or "").casefold(), float(ev.valor)] for ev in evs
            ],
        )


class _IncomeCadastroTab(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Fontes de renda",
            "Recorrentes, avulsas e parceladas. Filtre por tipo ou use a busca. "
            "O registo de dinheiro já recebido no livro-caixa faz-se na aba Recebimentos. "
            "Avulsas e parceladas totalmente recebidas ficam ocultas até marcar "
            "«Mostrar concluídas».",
            [
                "Nome",
                "Tipo",
                "Valor",
                "Mês ref.",
                "Parcelas",
                "Recebido",
                "A receber",
                "Forma",
                "Conta",
                "Ativa",
                "Observação",
            ],
        )
        self._by_id: dict[int, IncomeSource] = {}
        self._filt_tipo = QComboBox()
        self._filt_tipo.addItem("Todos os tipos", None)
        self._filt_tipo.addItem("Recorrente", "recorrente")
        self._filt_tipo.addItem("Avulsa", "avulsa")
        self._filt_tipo.addItem("Parcelada", "parcelada")
        self._filt_tipo.currentIndexChanged.connect(lambda: self.reload())
        self._chk_completed = QCheckBox("Mostrar concluídas")
        self._chk_completed.toggled.connect(lambda: self.reload())
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Filtrar:"))
        bar.addWidget(self._filt_tipo)
        bar.addWidget(self._chk_completed)
        bar.addStretch()
        wbar = QWidget()
        wbar.setLayout(bar)
        self.toolbar_layout.insertWidget(0, wbar)

        self.totals_wrap.setVisible(True)
        self._kp_mes = KpiCard("Total no mês atual", "-", compact=True)
        self._kp_a_receber = KpiCard("Saldo a receber (ativas)", "-", compact=True)
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
        return {"avulsa": "Avulsa", "parcelada": "Parcelada", "recorrente": "Recorrente"}.get(
            s.tipo, s.tipo
        )

    def _parcelas_txt(self, s: IncomeSource) -> str:
        if s.tipo != "parcelada" or s.total_parcelas is None:
            return "—"
        return f"{s.parcelas_recebidas}/{s.total_parcelas}"

    def _filt_ok(self, s: IncomeSource) -> bool:
        ft = self._filt_tipo.currentData()
        if ft is None:
            return True
        return s.tipo == ft

    def _refresh_kpi_cards(self) -> None:
        ym = current_month()
        total = sum(
            s.valor_mensal
            for s in self._by_id.values()
            if income_sources_service.applies_to_month(s, ym)
        )
        a_receber = sum(
            income_sources_service.paid_remaining(s, include_inactive=False)[1]
            for s in self._by_id.values()
            if s.ativo and s.tipo in ("avulsa", "parcelada")
        )
        self._kp_mes.set_value(format_currency(total))
        self._kp_a_receber.set_value(format_currency(a_receber))
        self._kp_cad.set_value(str(len(self._by_id)))

    def reload(self) -> None:
        self._by_id.clear()
        rows = []
        for s in income_sources_service.list_all():
            if not self._filt_ok(s):
                continue
            if not self._chk_completed.isChecked() and income_sources_service.is_fully_received(
                s
            ):
                continue
            if s.id is not None:
                self._by_id[s.id] = s
            obs = (s.observacao or "").replace("\n", " ")
            if len(obs) > 60:
                obs = obs[:57] + "..."
            cn = s.conta_nome or "—"
            forma = s.forma_recebimento or "—"
            if s.tipo == "recorrente":
                rec_txt = "—"
                arr_txt = "—"
            else:
                recebido, a_receber = income_sources_service.paid_remaining(
                    s, include_inactive=False
                )
                rec_txt = format_currency(recebido)
                arr_txt = format_currency(a_receber)
            rows.append((s.id or 0, [
                s.nome,
                self._tipo_label(s),
                format_currency(s.valor_mensal),
                _format_ano_mes(s.mes_referencia),
                self._parcelas_txt(s),
                rec_txt,
                arr_txt,
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
        dlg = IncomeSourceDialog(self, allowed_tipos=("recorrente", "avulsa", "parcelada"))
        if dlg.exec():
            try:
                income_sources_service.create(dlg.payload())
            except income_sources_service.DuplicateAvulsaIncomeError as e:
                r = QMessageBox.question(
                    self,
                    "Renda avulsa duplicada",
                    str(e) + "\n\nDeseja criar mesmo assim?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if r != QMessageBox.StandardButton.Yes:
                    return
                try:
                    income_sources_service.create(
                        dlg.payload(), allow_duplicate_avulsa=True
                    )
                except ValueError as err2:
                    QMessageBox.warning(self, "Validação", str(err2))
                    return
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
        dlg = IncomeSourceDialog(self, src, allowed_tipos=("recorrente", "avulsa", "parcelada"))
        if dlg.exec():
            payload = dlg.payload()
            try:
                income_sources_service.update(payload)
            except income_sources_service.DuplicateAvulsaIncomeError as dup_e:
                r0 = QMessageBox.question(
                    self,
                    "Renda avulsa duplicada",
                    str(dup_e) + "\n\nDeseja salvar mesmo assim?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if r0 != QMessageBox.StandardButton.Yes:
                    return
                try:
                    income_sources_service.update(
                        payload, allow_duplicate_avulsa=True
                    )
                except income_sources_service.DestructiveIncomeUpdateError as e:
                    r = QMessageBox.question(
                        self,
                        "Confirmar alteração",
                        str(e) + "\n\nDeseja continuar?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if r != QMessageBox.StandardButton.Yes:
                        return
                    try:
                        income_sources_service.update(
                            payload,
                            confirm_destructive_prune=True,
                            allow_duplicate_avulsa=True,
                        )
                    except ValueError as err2:
                        QMessageBox.warning(self, "Validação", str(err2))
                        return
                except ValueError as err2:
                    QMessageBox.warning(self, "Validação", str(err2))
                    return
                self.reload()
                self.data_changed.emit()
                return
            except income_sources_service.DestructiveIncomeUpdateError as e:
                r = QMessageBox.question(
                    self,
                    "Confirmar alteração",
                    str(e) + "\n\nDeseja continuar?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if r != QMessageBox.StandardButton.Yes:
                    return
                try:
                    income_sources_service.update(
                        payload, confirm_destructive_prune=True
                    )
                except income_sources_service.DuplicateAvulsaIncomeError as dup2:
                    r3 = QMessageBox.question(
                        self,
                        "Renda avulsa duplicada",
                        str(dup2) + "\n\nDeseja salvar mesmo assim?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if r3 != QMessageBox.StandardButton.Yes:
                        return
                    income_sources_service.update(
                        payload,
                        confirm_destructive_prune=True,
                        allow_duplicate_avulsa=True,
                    )
                except ValueError as err2:
                    QMessageBox.warning(self, "Validação", str(err2))
                    return
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
            self,
            "Excluir",
            "Excluir esta fonte de renda? Serão removidos o cadastro, as linhas em "
            "Situação mensal e os lançamentos de renda no livro-caixa ligados a ela.",
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
        self._hdr_sort_col: int | None = None
        self._hdr_sort_order = Qt.SortOrder.AscendingOrder
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        hint = QLabel(
            "Competência é o mês a que a renda se refere (YYYY-MM). Ao marcar Recebido, "
            "indique valor e conta do crédito no livro-caixa (podem diferir do cadastro)."
        )
        hint.setWordWrap(True)
        hint.setObjectName("FormHint")
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
            sorting_enabled=False,
        )
        self.tbl.horizontalHeader().sectionClicked.connect(
            self._on_monthly_header_clicked
        )
        inner = QVBoxLayout()
        inner.setSpacing(10)
        inner.addLayout(row)
        inner.addWidget(self.tbl, 1)
        grp = QGroupBox("Competência e situação")
        grp.setLayout(inner)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(hint)
        lay.addWidget(grp, 1)
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

    def _default_valor_mes(self, s: IncomeSource, ym: str) -> float:
        row = income_months_service.get_month_record(s.id, ym)
        if row and row[1] is not None:
            return float(row[1])
        return float(s.valor_mensal)

    def _default_conta_mes(self, s: IncomeSource, ym: str) -> Optional[int]:
        row = income_months_service.get_month_record(s.id, ym)
        if row and row[2] is not None:
            return int(row[2])
        return s.account_id

    def _resolved_conta_nome(self, s: IncomeSource, ym: str) -> str:
        row = income_months_service.get_month_record(s.id, ym)
        cr = row[2] if row else None
        aid = income_months_service.resolved_account_id(s.account_id, cr)
        if aid is None:
            return "—"
        acc = accounts_service.get(int(aid))
        return acc.nome if acc else "—"

    def _dialog_recebimento(self, s: IncomeSource, ym: str) -> bool:
        assert s.id is not None
        dlg = IncomeMonthReceiptDialog(
            self,
            s.nome,
            self._default_valor_mes(s, ym),
            self._default_conta_mes(s, ym),
        )
        if not dlg.exec():
            return False
        val, acc = dlg.receipt_payload()
        cid_spec: Optional[int] = None
        if s.account_id is None or acc != s.account_id:
            cid_spec = acc
        income_months_service.set_month_status(
            s.id,
            ym,
            recebido=True,
            valor_efetivo=val,
            conta_recebimento_id=cid_spec,
        )
        return True

    def _make_situacao_widget(self, s: IncomeSource, ym: str) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(2, 0, 2, 0)
        lay.setSpacing(6)
        cb = QComboBox()
        cb.addItems(["Pendente", "Recebido"])
        rec = income_months_service.is_received(s.id, ym)
        cb.blockSignals(True)
        cb.setCurrentIndex(1 if rec else 0)
        cb.blockSignals(False)
        cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn = QPushButton("Ajustar…")
        btn.setEnabled(rec)

        def on_adjust() -> None:
            if self._dialog_recebimento(s, ym):
                self.reload_table()
                self.data_changed.emit()

        def on_change(_idx: int) -> None:
            want = cb.currentIndex() == 1
            if want:
                if not self._dialog_recebimento(s, ym):
                    cb.blockSignals(True)
                    cb.setCurrentIndex(0)
                    cb.blockSignals(False)
            else:
                income_months_service.set_month_status(s.id, ym, recebido=False)
            self.reload_table()
            self.data_changed.emit()

        btn.clicked.connect(on_adjust)
        cb.currentIndexChanged.connect(on_change)
        lay.addWidget(cb, 1)
        lay.addWidget(btn, 0)
        return w

    def reload_table(self) -> None:
        ym = self.ano_mes()
        items: list[IncomeSource] = []
        for s in income_sources_service.list_all():
            if s.id is None:
                continue
            if not income_sources_service.applies_to_month(s, ym):
                continue
            items.append(s)
        if self._hdr_sort_col is not None:
            col = self._hdr_sort_col
            rev = self._hdr_sort_order == Qt.SortOrder.DescendingOrder

            def hdr_key(s: IncomeSource):
                assert s.id is not None
                cn = self._resolved_conta_nome(s, ym).lower()
                rec = income_months_service.is_received(s.id, ym)
                if col == 0:
                    return (s.nome.lower(),)
                if col == 1:
                    return (float(s.valor_mensal),)
                if col == 2:
                    return (cn,)
                if col == 3:
                    return (rec,)
                return (0,)

            items = sorted(items, key=hdr_key, reverse=rev)

        self.tbl.setRowCount(len(items))
        for i, s in enumerate(items):
            assert s.id is not None
            it_n = QTableWidgetItem(s.nome)
            it_n.setTextAlignment(ReadOnlyTable.ALIGN_LEFT)
            self.tbl.setItem(i, 0, it_n)
            mr = income_months_service.get_month_record(s.id, ym)
            v_cell = (
                float(mr[1])
                if mr is not None and mr[1] is not None
                else float(s.valor_mensal)
            )
            it_v = QTableWidgetItem(format_currency(v_cell))
            it_v.setTextAlignment(ReadOnlyTable.ALIGN_RIGHT)
            self.tbl.setItem(i, 1, it_v)
            it_c = QTableWidgetItem(self._resolved_conta_nome(s, ym))
            it_c.setTextAlignment(ReadOnlyTable.ALIGN_LEFT)
            self.tbl.setItem(i, 2, it_c)
            self.tbl.setCellWidget(i, 3, self._make_situacao_widget(s, ym))

        hdr = self.tbl.horizontalHeader()
        if self._hdr_sort_col is not None:
            hdr.setSortIndicatorShown(True)
            hdr.setSortIndicator(self._hdr_sort_col, self._hdr_sort_order)
        else:
            hdr.setSortIndicatorShown(False)


class _IncomeHistoryTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        hint = QLabel(
            "Créditos já lançados nas contas com origem «renda» no livro-caixa "
            "(últimos lançamentos)."
        )
        hint.setWordWrap(True)
        hint.setObjectName("FormHint")
        self.tbl = ReadOnlyTable(
            ["Data", "Valor", "Conta", "Descrição"],
            min_height=200,
            size_policy=(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(hint)
        lay.addWidget(self.tbl, 1)

    def reload(self) -> None:
        rows = income_sources_service.list_renda_ledger_rows(400)
        if not rows:
            self.tbl.set_rows([], empty_message="Nenhum crédito de renda no livro-caixa.")
            return
        self.tbl.set_rows(
            [
                [
                    format_date_br(d),
                    format_currency(v),
                    conta,
                    desc or "—",
                ]
                for d, v, desc, conta in rows
            ],
            sort_keys=[[d, float(v), conta.casefold(), desc.casefold()] for d, v, desc, conta in rows],
        )


class IncomeSourcesView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._overview = _IncomeOverviewTab()
        self._cadastro = _IncomeCadastroTab()
        self._month = _IncomeMonthlyControl()
        self._hist = _IncomeHistoryTab()

        def _on_child_change() -> None:
            self.reload()

        self._cadastro.data_changed.connect(_on_child_change)
        self._month.data_changed.connect(_on_child_change)
        tabs = QTabWidget()
        tabs.addTab(self._month, "Recebimentos")
        tabs.addTab(self._cadastro, "Fontes")
        tabs.addTab(self._overview, "Resumo (mês atual)")
        tabs.addTab(self._hist, "Livro-caixa")
        tabs.setTabToolTip(
            0,
            "Marque renda como recebida por competência (qualquer mês) e lance no livro-caixa.",
        )
        tabs.setTabToolTip(
            1,
            "Cadastro de fontes: salário, avulsas e parceladas; conta padrão e valores esperados.",
        )
        tabs.setTabToolTip(
            2,
            "Indicadores e próximas entradas apenas do mês civil corrente (calendário).",
        )
        tabs.setTabToolTip(
            3,
            "Lista de créditos de renda já registados nas contas (histórico do livro-caixa).",
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs, 1)

    def reload(self) -> None:
        self._overview.reload()
        self._cadastro.reload()
        self._month.reload_table()
        self._hist.reload()
