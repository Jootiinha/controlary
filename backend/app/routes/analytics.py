from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.decorators import get_current_user
from app.repositories.payments_repo import PaymentsRepository
from app.repositories.accounts_repo import AccountsRepository, AccountTransactionsRepository
from app.models.payment import Payment
from app.models.account import AccountTransaction

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _verify_payment_ownership(db: Session, user_id: str, payment_id: str) -> bool:
    """Verify that a payment belongs to the authenticated user."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    return payment and payment.user_id == user_id


@router.get("/dashboard-kpis")
async def get_dashboard_kpis(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard KPIs for current month with previous month comparison"""
    now = datetime.now()

    # Current month
    month_start = datetime(now.year, now.month, 1)
    if now.month == 12:
        month_end = datetime(now.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

    # Previous month
    if now.month == 1:
        prev_month_start = datetime(now.year - 1, 12, 1)
        prev_month_end = datetime(now.year, 1, 1) - timedelta(days=1)
    else:
        prev_month_start = datetime(now.year, now.month - 1, 1)
        prev_month_end = datetime(now.year, now.month, 1) - timedelta(days=1)

    # Current month income
    income = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.data >= month_start,
        Payment.data <= month_end,
        Payment.amount > 0,
    ).with_entities(Payment.amount).all()

    monthly_income = sum(p.amount for p in income) if income else 0

    # Current month expenses
    expenses = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.data >= month_start,
        Payment.data <= month_end,
        Payment.amount < 0,
    ).with_entities(Payment.amount).all()

    monthly_expense = sum(abs(p.amount) for p in expenses) if expenses else 0

    # Previous month income
    prev_income = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.data >= prev_month_start,
        Payment.data <= prev_month_end,
        Payment.amount > 0,
    ).with_entities(Payment.amount).all()

    previous_income = sum(p.amount for p in prev_income) if prev_income else 0

    # Previous month expenses
    prev_expenses = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.data >= prev_month_start,
        Payment.data <= prev_month_end,
        Payment.amount < 0,
    ).with_entities(Payment.amount).all()

    previous_expense = sum(abs(p.amount) for p in prev_expenses) if prev_expenses else 0

    # Outstanding balance (unpaid negative payments)
    outstanding = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.is_paid == False,
        Payment.amount < 0,
    ).with_entities(Payment.amount).all()

    outstanding_balance = sum(abs(p.amount) for p in outstanding) if outstanding else 0

    return {
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "outstanding_balance": outstanding_balance,
        "net_balance": monthly_income - monthly_expense,
        "previous_income": previous_income,
        "previous_expense": previous_expense,
        "previous_net_balance": previous_income - previous_expense,
    }


@router.get("/income-vs-expense")
async def get_income_vs_expense(
    months: int = 6,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get income vs expense trends for last N months"""
    now = datetime.now()
    data = []

    for i in range(months - 1, -1, -1):
        target_date = now - timedelta(days=now.day - 1) - timedelta(days=30 * i)
        month_start = datetime(target_date.year, target_date.month, 1)

        if target_date.month == 12:
            month_end = datetime(target_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(target_date.year, target_date.month + 1, 1) - timedelta(days=1)

        # Income for this month
        income_payments = db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.data >= month_start,
            Payment.data <= month_end,
            Payment.amount > 0,
        ).all()

        income = sum(p.amount for p in income_payments)

        # Expenses for this month
        expense_payments = db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.data >= month_start,
            Payment.data <= month_end,
            Payment.amount < 0,
        ).all()

        expense = sum(abs(p.amount) for p in expense_payments)

        month_label = month_start.strftime("%b/%y")
        data.append({
            "month": month_label,
            "income": income,
            "expense": expense,
            "balance": income - expense,
        })

    return data


@router.get("/expenses-by-category")
async def get_expenses_by_category(
    months: int = 1,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get expenses breakdown by category for last N months"""
    now = datetime.now()
    month_start = now - timedelta(days=30 * months)

    expenses = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.data >= month_start,
        Payment.amount < 0,
    ).all()

    category_totals = {}
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Sem Categoria"
        if category_name not in category_totals:
            category_totals[category_name] = 0
        category_totals[category_name] += abs(expense.amount)

    return [
        {"category": name, "amount": total}
        for name, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    ]


@router.get("/balance-evolution")
async def get_balance_evolution(
    days: int = 30,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get account balance evolution over time"""
    now = datetime.now()
    start_date = now - timedelta(days=days)

    transactions = db.query(AccountTransaction).filter(
        AccountTransaction.user_id == user_id,
        AccountTransaction.data >= start_date,
    ).order_by(AccountTransaction.data.asc()).all()

    # Get all accounts for initial balances
    accounts_repo = AccountsRepository(db)
    accounts = accounts_repo.list_by_user(user_id)

    # Build daily balance data
    balance_by_date = {}
    running_total = sum(a.initial_balance for a in accounts)

    for transaction in transactions:
        date_key = transaction.data.strftime("%Y-%m-%d")
        running_total += transaction.amount
        balance_by_date[date_key] = running_total

    # Fill gaps with last known value
    data = []
    current_date = start_date
    last_balance = running_total

    while current_date <= now:
        date_key = current_date.strftime("%Y-%m-%d")
        if date_key in balance_by_date:
            last_balance = balance_by_date[date_key]

        data.append({
            "date": date_key,
            "balance": last_balance,
        })

        current_date += timedelta(days=1)

    return data


@router.get("/payment-timeline")
async def get_payment_timeline(
    days: int = 30,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payment timeline for specified period"""
    now = datetime.now()
    start_date = now - timedelta(days=days)

    payments = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.data >= start_date,
    ).order_by(Payment.data).all()

    return [
        {
            "id": p.id,
            "description": p.description,
            "amount": p.amount,
            "date": p.data.isoformat(),
            "is_paid": p.is_paid,
            "category": p.category.name if p.category else None,
        }
        for p in payments
    ]


@router.get("/cash-flow")
async def get_cash_flow(
    months: int = 3,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get cash flow data (opening, income, expense, closing) for last N months"""
    now = datetime.now()
    data = []

    for i in range(months - 1, -1, -1):
        target_date = now - timedelta(days=now.day - 1) - timedelta(days=30 * i)
        month_start = datetime(target_date.year, target_date.month, 1)

        if target_date.month == 12:
            month_end = datetime(target_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(target_date.year, target_date.month + 1, 1) - timedelta(days=1)

        # Get previous month opening balance (which is last month's closing)
        prev_month_start = month_start - timedelta(days=1)
        prev_transactions = db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.data <= prev_month_start,
        ).all()

        opening_balance = sum(p.amount for p in prev_transactions if p.amount > 0) - sum(abs(p.amount) for p in prev_transactions if p.amount < 0)

        # Income for this month
        income_payments = db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.data >= month_start,
            Payment.data <= month_end,
            Payment.amount > 0,
        ).all()

        income = sum(p.amount for p in income_payments)

        # Expenses for this month
        expense_payments = db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.data >= month_start,
            Payment.data <= month_end,
            Payment.amount < 0,
        ).all()

        expense = sum(abs(p.amount) for p in expense_payments)
        closing = opening_balance + income - expense

        month_label = month_start.strftime("%b/%y")
        data.append({
            "month": month_label,
            "opening": opening_balance,
            "income": income,
            "expense": expense,
            "closing": closing,
        })

    return data


@router.get("/category-comparison")
async def get_category_comparison(
    months: int = 3,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get multi-dimensional category comparison for last N months"""
    now = datetime.now()
    month_start = now - timedelta(days=30 * months)

    payments = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.data >= month_start,
    ).all()

    category_stats = {}
    for payment in payments:
        category_name = payment.category.name if payment.category else "Sem Categoria"
        if category_name not in category_stats:
            category_stats[category_name] = {
                "total_transactions": 0,
                "total_amount": 0,
                "income_count": 0,
                "expense_count": 0,
                "income_total": 0,
                "expense_total": 0,
            }

        stats = category_stats[category_name]
        stats["total_transactions"] += 1
        stats["total_amount"] += payment.amount

        if payment.amount > 0:
            stats["income_count"] += 1
            stats["income_total"] += payment.amount
        else:
            stats["expense_count"] += 1
            stats["expense_total"] += abs(payment.amount)

    result = []
    for category, stats in category_stats.items():
        result.append({
            "category": category,
            "total_transactions": stats["total_transactions"],
            "total_amount": stats["total_amount"],
            "income_count": stats["income_count"],
            "expense_count": stats["expense_count"],
            "income_total": stats["income_total"],
            "expense_total": stats["expense_total"],
            "average_transaction": stats["total_amount"] / stats["total_transactions"] if stats["total_transactions"] > 0 else 0,
        })

    return sorted(result, key=lambda x: abs(x["total_amount"]), reverse=True)


@router.get("/expense-correlation")
async def get_expense_correlation(
    days: int = 90,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get correlation data between expenses and day of week"""
    now = datetime.now()
    start_date = now - timedelta(days=days)

    payments = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.data >= start_date,
        Payment.amount < 0,
    ).all()

    # Group by day of week
    day_names = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    day_stats = {i: {"count": 0, "total": 0} for i in range(7)}

    for payment in payments:
        day_of_week = payment.data.weekday()
        day_stats[day_of_week]["count"] += 1
        day_stats[day_of_week]["total"] += abs(payment.amount)

    result = []
    for day_num in range(7):
        stats = day_stats[day_num]
        result.append({
            "day": day_names[day_num],
            "expense_count": stats["count"],
            "total_expense": stats["total"],
            "average_expense": stats["total"] / stats["count"] if stats["count"] > 0 else 0,
        })

    return result
