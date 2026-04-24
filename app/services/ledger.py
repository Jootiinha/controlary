"""Chaves idempotentes do livro-caixa (transaction_key)."""
from __future__ import annotations


class LedgerKey:
    @staticmethod
    def payment(payment_id: int) -> str:
        return f"payment:{payment_id}"

    @staticmethod
    def invoice(invoice_id: int) -> str:
        return f"invoice:{invoice_id}"

    @staticmethod
    def fixed(fe_id: int, ano_mes: object) -> str:
        return f"fixed:{fe_id}:{str(ano_mes)}"

    @staticmethod
    def subscription(sub_id: int, ano_mes: object) -> str:
        return f"subscription:{sub_id}:{str(ano_mes)}"

    @staticmethod
    def installment(inst_id: int, ano_mes: object) -> str:
        return f"installment:{inst_id}:{str(ano_mes)}"

    @staticmethod
    def income(src_id: int, ano_mes: object) -> str:
        return f"income:{src_id}:{str(ano_mes)}"
