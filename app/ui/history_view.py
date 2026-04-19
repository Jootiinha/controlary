"""Tela de histórico consolidado + gráficos."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.charts import (
    category_breakdown,
    comprometimento_renda,
    debt_evolution,
    fluxo_acumulado,
    investments_overview,
    invoice_evolution,
    monthly_expenses,
    renda_vs_despesa,
)
from app.services import accounts_service, cards_service, import_service, payments_service
from app.ui.widgets.chart_canvas import ChartCanvas
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.utils.formatting import format_currency, format_date_br


class HistoryView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        lbl_title = QLabel("Histórico e análises")
        lbl_title.setObjectName("PageTitle")
        lbl_sub = QLabel(
            "Transações, projeções e indicadores consolidados (renda, gastos, categorias, investimentos)."
        )
        lbl_sub.setObjectName("PageSubtitle")

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_history_tab(), "Transações")
        self.tabs.addTab(self._build_imports_tab(), "Importações")
        self.tabs.addTab(self._build_chart_tab(renda_vs_despesa.plot), "Renda vs despesa")
        self.tabs.addTab(self._build_chart_tab(fluxo_acumulado.plot), "Fluxo acumulado")
        self.tabs.addTab(
            self._build_chart_tab(comprometimento_renda.plot), "Comprometimento %"
        )
        self.tabs.addTab(self._build_chart_tab(monthly_expenses.plot), "Custo de vida")
        self.tabs.addTab(self._build_chart_tab(invoice_evolution.plot), "Evolução da fatura")
        self.tabs.addTab(self._build_chart_tab(category_breakdown.plot), "Categorias")
        self.tabs.addTab(self._build_chart_tab(debt_evolution.plot), "Saldo devedor")
        self.tabs.addTab(
            self._build_chart_tab(investments_overview.plot), "Investimentos"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)
        layout.addWidget(self.tabs)

    def _build_imports_tab(self) -> QWidget:
        hint = QLabel(
            "Lotes de arquivos importados (extrato ou fatura). Desfazer remove os "
            "lançamentos criados naquele lote."
        )
        hint.setWordWrap(True)
        hint.setObjectName("PageSubtitle")
        self.tbl_imports = ReadOnlyTable(
            ["ID", "Quando", "Tipo", "Arquivo", "Itens", "Total", "Alvo"],
            selectable=True,
        )
        self.btn_undo_import = QPushButton("Desfazer lote selecionado")
        self.btn_undo_import.clicked.connect(self._undo_import_batch)
        row = QHBoxLayout()
        row.addWidget(self.btn_undo_import)
        row.addStretch()
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(hint)
        lay.addLayout(row)
        lay.addWidget(self.tbl_imports)
        return w

    def _undo_import_batch(self) -> None:
        r = self.tbl_imports.currentRow()
        if r < 0:
            QMessageBox.information(
                self, "Importações", "Selecione um lote na tabela."
            )
            return
        id_item = self.tbl_imports.item(r, 0)
        if id_item is None:
            return
        try:
            batch_id = int(id_item.text())
        except ValueError:
            return
        if (
            QMessageBox.question(
                self,
                "Desfazer importação",
                "Remover todos os lançamentos deste lote?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            import_service.undo_batch(batch_id)
        except Exception as e:
            QMessageBox.warning(self, "Importações", str(e))
            return
        self.reload()

    def _build_history_tab(self) -> QWidget:
        self.tbl_history = ReadOnlyTable(
            ["Data", "Descrição", "Origem", "Categoria", "Forma", "Valor"],
            selectable=True,
        )

        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(self.tbl_history)
        return wrapper

    def _build_chart_tab(self, renderer) -> QWidget:
        canvas = ChartCanvas(renderer)
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(canvas)
        wrapper._canvas = canvas  # type: ignore[attr-defined]
        return wrapper

    def reload(self) -> None:
        payments = payments_service.list_all()
        rows = []
        for p in payments:
            orig = p.conta_nome or p.cartao_nome or "—"
            rows.append(
                [
                    format_date_br(p.data),
                    p.descricao,
                    orig,
                    p.categoria_nome or "—",
                    p.forma_pagamento,
                    format_currency(p.valor),
                ]
            )
        self.tbl_history.set_rows(rows)

        imp_rows = []
        for b in import_service.list_batches(100):
            tid = int(b["target_id"])
            kind = b["kind"]
            if kind == "extrato":
                acc = accounts_service.get(tid)
                alvo = acc.nome if acc else str(tid)
            else:
                c = cards_service.get(tid)
                alvo = c.nome if c else str(tid)
            imp_rows.append(
                [
                    str(b["id"]),
                    (b["imported_at"] or "")[:19],
                    kind,
                    b["file_name"] or "—",
                    str(b["n_items"] or 0),
                    format_currency(float(b["total"] or 0)),
                    alvo,
                ]
            )
        self.tbl_imports.set_rows(imp_rows)

        for i in range(1, self.tabs.count()):
            tab = self.tabs.widget(i)
            canvas = getattr(tab, "_canvas", None)
            if canvas is not None:
                canvas.refresh()
