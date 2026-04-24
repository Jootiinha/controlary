"""Cadastro de gastos fixos e controle mensal (pago / pendente)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QDialog,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.fixed_expense import FixedExpense
from app.services import accounts_service, fixed_expenses_service, payments_service
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.card import KpiCard
from app.ui.widgets.category_picker import CategoryPicker, emit_parent_view_data_changed
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.ui.widgets.form_dialog import FormDialog
from app.ui.widgets.payment_confirmation_dialog import FixedExpensePaidDialog
from app.utils.formatting import format_currency, format_month_br


FORMAS = [
    "Pix", "Débito", "Crédito", "Dinheiro", "Boleto", "Transferência", "Débito Automático",
]


def _fixed_due_date_for_month(ym: str, dia_referencia: int) -> QDate:
    y, m = map(int, ym.split("-"))
    first = QDate(y, m, 1)
    day = min(int(dia_referencia), first.daysInMonth())
    return QDate(y, m, day)


def _apply_fixed_monthly_status_icon(
    item: QTableWidgetItem,
    paid: bool,
    ym: str,
    dia_referencia: int,
) -> None:
    item.setTextAlignment(ReadOnlyTable.ALIGN_CENTER)
    due = _fixed_due_date_for_month(ym, dia_referencia)
    today = QDate.currentDate()
    if paid:
        item.setText("➤")
        item.setForeground(QBrush(QColor(34, 139, 34)))
        item.setToolTip("Pago")
        return
    if due < today:
        item.setText("🔴")
        item.setToolTip(f"Atrasado — vencimento {due.toString('dd/MM/yyyy')}")
    else:
        item.setText("⚠️")
        item.setToolTip(f"Pendente — vence em {due.toString('dd/MM/yyyy')}")


class FixedExpenseDialog(FormDialog):
    def __init__(self, parent=None, fe: Optional[FixedExpense] = None) -> None:
        super().__init__("Editar gasto fixo" if fe else "Novo gasto fixo", parent)
        self._fe = fe

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Aluguel, Luz, Internet, Condomínio")

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 500_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(50.0)

        self.ed_dia = QSpinBox()
        self.ed_dia.setRange(1, 31)
        self.ed_dia.setValue(5)

        self.cmb_conta = QComboBox()
        self.cmb_conta.setEditable(False)
        self._fill_contas()

        self.cmb_forma = QComboBox()
        self.cmb_forma.addItems(FORMAS)

        self._picker_cat = CategoryPicker(self, allow_empty=False)
        self._picker_cat.connect_new_button(self._nova_categoria)

        self.chk_ativo = QCheckBox("Ativo (entra nas projeções)")
        self.chk_ativo.setChecked(True)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Valor mensal *", self.ed_valor)
        self.form.addRow("Dia de vencimento *", self.ed_dia)
        self.form.addRow("Conta", self.cmb_conta)
        self.form.addRow("Categoria *", self._picker_cat)
        self.form.addRow("Forma de pagamento *", self.cmb_forma)
        self.form.addRow("", self.chk_ativo)
        self.form.addRow("Observação", self.ed_obs)

        if fe:
            self.ed_nome.setText(fe.nome)
            self.ed_valor.setValue(fe.valor_mensal)
            self.ed_dia.setValue(fe.dia_referencia)
            if fe.conta_id is not None:
                for i in range(self.cmb_conta.count()):
                    if self.cmb_conta.itemData(i) == fe.conta_id:
                        self.cmb_conta.setCurrentIndex(i)
                        break
            idx = self.cmb_forma.findText(fe.forma_pagamento)
            if idx >= 0:
                self.cmb_forma.setCurrentIndex(idx)
            self.chk_ativo.setChecked(fe.ativo)
            self.ed_obs.setPlainText(fe.observacao or "")
            if fe.category_id is not None:
                self._picker_cat.set_category_id(fe.category_id)

    def _nova_categoria(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()
            emit_parent_view_data_changed(self)

    def _fill_contas(self) -> None:
        self.cmb_conta.clear()
        self.cmb_conta.addItem("(Nenhuma)", None)
        for a in accounts_service.list_all():
            self.cmb_conta.addItem(a.nome, a.id)

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Informe o nome"
        if self.ed_valor.value() <= 0:
            return False, "Valor deve ser maior que zero"
        if self._picker_cat.current_category_id() is None:
            return False, "Selecione uma categoria"
        return True, None

    def payload(self) -> FixedExpense:
        cid = self.cmb_conta.currentData()
        return FixedExpense(
            id=self._fe.id if self._fe else None,
            nome=self.ed_nome.text().strip(),
            valor_mensal=float(self.ed_valor.value()),
            dia_referencia=int(self.ed_dia.value()),
            forma_pagamento=self.cmb_forma.currentText(),
            conta_id=int(cid) if cid is not None else None,
            observacao=self.ed_obs.toPlainText().strip() or None,
            ativo=self.chk_ativo.isChecked(),
            category_id=self._picker_cat.current_category_id(),
        )


class _FixedCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Itens de gasto fixo",
            "Aluguel, contas de consumo, telefone etc. O valor entra no previsto até marcar como pago no mês.",
            ["Nome", "Valor/mês", "Dia", "Conta", "Categoria", "Forma", "Ativo"],
        )
        self._by_id: dict[int, FixedExpense] = {}
        self.totals_wrap.setVisible(True)
        self._kp_mensal = KpiCard("Total mensal (ativos)", "-", compact=True)
        self._kp_ativos = KpiCard("Ativos", "-", compact=True)
        self._kp_cad = KpiCard("Cadastrados", "-", compact=True)
        self.totals_bar.addWidget(self._kp_mensal)
        self.totals_bar.addWidget(self._kp_ativos)
        self.totals_bar.addWidget(self._kp_cad)
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)

    def _refresh_kpi_cards(self) -> None:
        ativos = [fe for fe in self._by_id.values() if fe.ativo]
        total_m = sum(fe.valor_mensal for fe in ativos)
        self._kp_mensal.set_value(format_currency(total_m))
        self._kp_ativos.set_value(str(len(ativos)))
        self._kp_cad.set_value(str(len(self._by_id)))

    def reload(self) -> None:
        self._by_id.clear()
        rows = []
        for fe in fixed_expenses_service.list_all():
            if fe.id is not None:
                self._by_id[fe.id] = fe
            cat = fe.categoria_nome or "—"
            rows.append((fe.id or 0, [
                fe.nome,
                format_currency(fe.valor_mensal),
                str(fe.dia_referencia),
                fe.conta_nome or "—",
                cat,
                fe.forma_pagamento,
                "Sim" if fe.ativo else "Não",
            ]))
        self.model.set_rows(rows)
        self._refresh_kpi_cards()
        self.refresh_totals()

    def compute_totals(self, visible_ids: list[int]) -> None:
        if not self._by_id:
            self.set_footer_text("", "")
            return
        vis = [self._by_id[i] for i in visible_ids if i in self._by_id]
        total = sum(fe.valor_mensal for fe in vis)
        self.set_footer_text(
            f"Total mensal (visíveis): {format_currency(total)}",
            f"Itens: {len(vis)}",
        )

    def _add(self) -> None:
        dlg = FixedExpenseDialog(self)
        if dlg.exec():
            fixed_expenses_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        fid = self.selected_id()
        if fid is None:
            QMessageBox.information(self, "Editar", "Selecione um item.")
            return
        fe = fixed_expenses_service.get(fid)
        if fe is None:
            return
        dlg = FixedExpenseDialog(self, fe)
        if dlg.exec():
            fixed_expenses_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        fid = self.selected_id()
        if fid is None:
            QMessageBox.information(self, "Excluir", "Selecione um item.")
            return
        if (
            QMessageBox.question(
                self,
                "Excluir",
                "Excluir este gasto fixo? Pagamentos espelhados e marcações em "
                "Situação mensal deixam de existir; o livro-caixa pode ter sido "
                "ajustado ao marcar o fixo como pago.",
            )
            != QMessageBox.Yes
        ):
            return
        fixed_expenses_service.delete(fid)
        self.reload()
        self.data_changed.emit()


class _MonthlyControl(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._rows: list[tuple[int, QComboBox]] = []
        self._monthly_hints: list[str] = []
        self._hdr_sort_col: int | None = None
        self._hdr_sort_order = Qt.SortOrder.AscendingOrder

        hint = QLabel(
            "Marque cada gasto fixo ativo como Pago na competência escolhida. "
            "Totais e projeção consideram apenas o que ainda está pendente."
        )
        hint.setWordWrap(True)
        hint.setObjectName("PageSubtitle")
        hint.setToolTip(
            "Escolha o mês/ano (competência). Cada item ativo começa como Pendente até você marcar Pago. "
            "O previsto do mês e o total do restante do ano usam só valores ainda pendentes."
        )

        row = QHBoxLayout()
        row.addWidget(QLabel("Competência:"))
        self.dt = QDateEdit()
        self.dt.setDisplayFormat("MM/yyyy")
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())
        self.dt.dateChanged.connect(self._reload_table)
        self.dt.setToolTip("Competência (mês/ano) para marcar pagamentos e ver totais.")
        row.addWidget(self.dt)
        self._monthly_search = QLineEdit()
        self._monthly_search.setPlaceholderText("Buscar…")
        self._monthly_search.setClearButtonEnabled(True)
        self._monthly_search.textChanged.connect(self._apply_monthly_search)
        row.addWidget(self._monthly_search, 1)
        self.btn_edit = QPushButton("Editar despesa…")
        self.btn_edit.setObjectName("PrimaryButton")
        self.btn_edit.setToolTip(
            "Abre o cadastro do gasto fixo selecionado. "
            "Também é possível dar duplo clique em Nome, Valor ou Dia."
        )
        self.btn_edit.clicked.connect(self._edit_selected)
        row.addWidget(self.btn_edit)

        kpi_row = QHBoxLayout()
        self._kp_pago = KpiCard("Pago no mês", "-", compact=True)
        self._kp_pend = KpiCard("Pendente no mês", "-", compact=True)
        self._kp_mes = KpiCard("Total do mês", "-", compact=True)
        kpi_row.addWidget(self._kp_pago)
        kpi_row.addWidget(self._kp_pend)
        kpi_row.addWidget(self._kp_mes)

        self.tbl = ReadOnlyTable(
            ["", "Nome", "Valor", "Dia", "Status"],
            selectable=True,
            selection_behavior=QAbstractItemView.SelectionBehavior.SelectRows,
            alternating_row_colors=True,
            show_grid=True,
            word_wrap=False,
            vertical_header_default_section_size=44,
            section_resize_modes=[
                QHeaderView.ResizeMode.Fixed,
                QHeaderView.ResizeMode.Stretch,
                QHeaderView.ResizeMode.Fixed,
                QHeaderView.ResizeMode.Fixed,
                QHeaderView.ResizeMode.Fixed,
            ],
            column_widths={0: 48, 2: 112, 3: 44, 4: 178},
            header_default_alignment=(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            ),
            stretch_last_section=False,
            sorting_enabled=False,
        )

        self.tbl.horizontalHeader().sectionClicked.connect(
            self._on_monthly_header_clicked
        )
        self.tbl.cellDoubleClicked.connect(self._on_cell_double_clicked)

        proj_title = QLabel("Projeção — meses restantes do ano (só pendentes)")
        proj_title.setObjectName("PageSubtitle")
        self.tbl_proj = ReadOnlyTable(
            ["Mês", "Total pendente (fixos)"],
            section_resize_modes=[
                QHeaderView.ResizeMode.Stretch,
                QHeaderView.ResizeMode.ResizeToContents,
            ],
            min_height=100,
        )

        month_panel = QWidget()
        month_lay = QVBoxLayout(month_panel)
        month_lay.setContentsMargins(0, 0, 0, 0)
        month_lay.setSpacing(12)
        month_lay.addWidget(hint)
        month_lay.addLayout(row)
        month_lay.addLayout(kpi_row)
        month_lay.addWidget(self.tbl, 1)

        proj_panel = QWidget()
        proj_lay = QVBoxLayout(proj_panel)
        proj_lay.setContentsMargins(0, 0, 0, 0)
        proj_lay.setSpacing(8)
        proj_lay.addWidget(proj_title)
        proj_lay.addWidget(self.tbl_proj, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(month_panel)
        splitter.addWidget(proj_panel)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([720, 300])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(splitter, 1)
        self._reload_table()
        self._reload_projection()

    def ano_mes(self) -> str:
        d = self.dt.date()
        return f"{d.year():04d}-{d.month():02d}"

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        if col == 4:
            return
        self._edit_row(row)

    def _edit_selected(self) -> None:
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Editar", "Selecione uma linha na tabela (clique no nome ou em outra coluna)."
            )
            return
        self._edit_row(row)

    def _refresh_monthly_kpis(self) -> None:
        ym = self.ano_mes()
        pago = fixed_expenses_service.sum_paid_for_month(ym)
        pend = fixed_expenses_service.sum_unpaid_for_month(ym)
        total = pago + pend
        self._kp_pago.set_value(format_currency(pago))
        self._kp_pend.set_value(format_currency(pend))
        self._kp_mes.set_value(format_currency(total))

    def _apply_monthly_search(self) -> None:
        needle = self._monthly_search.text().strip().lower()
        for i in range(self.tbl.rowCount()):
            if i >= len(self._monthly_hints):
                continue
            if not needle:
                self.tbl.setRowHidden(i, False)
            else:
                self.tbl.setRowHidden(i, needle not in self._monthly_hints[i])

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
        self._reload_table()

    def _edit_row(self, row: int) -> None:
        if row < 0 or row >= len(self._rows):
            return
        fid = self._rows[row][0]
        fe = fixed_expenses_service.get(fid)
        if fe is None:
            return
        dlg = FixedExpenseDialog(self, fe)
        if dlg.exec():
            fixed_expenses_service.update(dlg.payload())
            self.data_changed.emit()
            self._reload_table()
            self._reload_projection()

    def _reload_table(self) -> None:
        self._rows.clear()
        self._monthly_hints.clear()
        ym = self.ano_mes()
        raw = [fe for fe in fixed_expenses_service.list_active() if fe.id is not None]

        def sort_key(fe: FixedExpense) -> tuple[int, int]:
            assert fe.id is not None
            pago = fixed_expenses_service.is_paid(fe.id, ym)
            due = _fixed_due_date_for_month(ym, fe.dia_referencia)
            return (0 if pago else 1, due.toJulianDay())

        def valor_efetivo_para_sort(fe: FixedExpense) -> float:
            assert fe.id is not None
            pr = fixed_expenses_service.is_paid(fe.id, ym)
            ve = (
                fixed_expenses_service.get_valor_efetivo(fe.id, ym) if pr else None
            )
            return float(ve) if ve is not None else float(fe.valor_mensal)

        if self._hdr_sort_col is None:
            items = sorted(raw, key=sort_key)
        else:
            col = self._hdr_sort_col
            rev = self._hdr_sort_order == Qt.SortOrder.DescendingOrder

            def hdr_key(fe: FixedExpense):
                assert fe.id is not None
                pr = fixed_expenses_service.is_paid(fe.id, ym)
                if col == 0:
                    return (pr, fe.nome.lower())
                if col == 1:
                    return (fe.nome.lower(),)
                if col == 2:
                    return (valor_efetivo_para_sort(fe),)
                if col == 3:
                    return (fe.dia_referencia,)
                if col == 4:
                    return (pr,)
                return (0,)

            items = sorted(raw, key=hdr_key, reverse=rev)

        self.tbl.setRowCount(len(items))
        for i, fe in enumerate(items):
            pago_row = fixed_expenses_service.is_paid(fe.id, ym)
            ve = (
                fixed_expenses_service.get_valor_efetivo(fe.id, ym)
                if pago_row
                else None
            )
            v_show = (
                float(ve)
                if ve is not None
                else float(fe.valor_mensal)
            )

            it_icon = QTableWidgetItem()
            _apply_fixed_monthly_status_icon(it_icon, pago_row, ym, fe.dia_referencia)
            self.tbl.setItem(i, 0, it_icon)

            it_nome = QTableWidgetItem(fe.nome)
            it_nome.setTextAlignment(ReadOnlyTable.ALIGN_LEFT)
            self.tbl.setItem(i, 1, it_nome)

            it_val = QTableWidgetItem(format_currency(v_show))
            it_val.setTextAlignment(ReadOnlyTable.ALIGN_RIGHT)
            self.tbl.setItem(i, 2, it_val)

            it_dia = QTableWidgetItem(str(fe.dia_referencia))
            it_dia.setTextAlignment(ReadOnlyTable.ALIGN_CENTER)
            self.tbl.setItem(i, 3, it_dia)

            cb = QComboBox()
            cb.addItems(["Pendente", "Pago"])
            cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cb.setMinimumWidth(138)
            cb.blockSignals(True)
            cb.setCurrentIndex(1 if pago_row else 0)
            cb.blockSignals(False)
            fid = fe.id

            def make_handler(f_id: int, combo: QComboBox, competencia: str):
                def on_change(_idx: int) -> None:
                    want_pago = combo.currentIndex() == 1
                    was_pago = fixed_expenses_service.is_paid(f_id, competencia)
                    if want_pago == was_pago:
                        return
                    if want_pago and not was_pago:
                        fe_local = fixed_expenses_service.get(f_id)
                        if fe_local is None:
                            return
                        dlg = FixedExpensePaidDialog(self, fe_local, competencia)
                        if dlg.exec() != QDialog.Accepted:
                            combo.blockSignals(True)
                            combo.setCurrentIndex(0)
                            combo.blockSignals(False)
                            return
                        mp = dlg.mirror_payment()
                        try:
                            fixed_expenses_service.set_month_status(
                                f_id,
                                competencia,
                                pago=True,
                                valor_efetivo=dlg.valor_efetivo(),
                                conta_debito_id=dlg.conta_debito_para_livro(),
                            )
                        except ValueError as err:
                            QMessageBox.warning(self, "Validação", str(err))
                            combo.blockSignals(True)
                            combo.setCurrentIndex(0)
                            combo.blockSignals(False)
                            return
                        if mp is not None:
                            payments_service.create(mp, record_ledger=False)
                    else:
                        fe_local = fixed_expenses_service.get(f_id)
                        if fe_local is not None:
                            payments_service.delete_mirrors_for_fixed_month(
                                fe_local.nome, competencia
                            )
                        fixed_expenses_service.set_month_status(
                            f_id, competencia, pago=want_pago
                        )
                    self.data_changed.emit()
                    self._reload_projection()
                    self._reload_table()

                return on_change

            cb.currentIndexChanged.connect(make_handler(fid, cb, ym))

            status_cell = QWidget()
            status_lay = QHBoxLayout(status_cell)
            status_lay.setContentsMargins(6, 2, 6, 2)
            status_lay.setSpacing(0)
            status_lay.addWidget(cb, 1, Qt.AlignmentFlag.AlignVCenter)
            self.tbl.setCellWidget(i, 4, status_cell)
            self._rows.append((fid, cb))

            st_txt = "pago" if pago_row else "pendente"
            hint = " ".join(
                [
                    fe.nome.lower(),
                    format_currency(v_show).lower(),
                    str(fe.dia_referencia),
                    st_txt,
                    (fe.observacao or "").lower(),
                ]
            )
            self._monthly_hints.append(hint)

        self._refresh_monthly_kpis()
        self._apply_monthly_search()

        hdr = self.tbl.horizontalHeader()
        if self._hdr_sort_col is not None:
            hdr.setSortIndicatorShown(True)
            hdr.setSortIndicator(self._hdr_sort_col, self._hdr_sort_order)
        else:
            hdr.setSortIndicatorShown(False)

    def reload_table(self) -> None:
        self._reload_table()

    def _reload_projection(self) -> None:
        data = fixed_expenses_service.projection_by_month_rest_of_year()
        self.tbl_proj.set_rows(
            [[format_month_br(ym), format_currency(total)] for ym, total in data],
            sort_keys=[[ym, float(total)] for ym, total in data],
        )

    def reload_all(self) -> None:
        self._reload_table()
        self._reload_projection()


class FixedExpensesView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._crud = _FixedCrud()
        self._month = _MonthlyControl()
        self._crud.data_changed.connect(self._month.reload_table)
        self._month.data_changed.connect(self._crud.reload)

        tabs = QTabWidget()
        tabs.addTab(self._crud, "Cadastro")
        tabs.addTab(self._month, "Situação mensal")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs, 1)

    def reload(self) -> None:
        self._crud.reload()
        self._month.reload_all()
