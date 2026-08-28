# ============================================================
#  transaction_events.py — Builders for transaction-driven events
# ============================================================

from decimal import Decimal

from app.services.financial_timeline.enums import TimelineEventSeverity, TimelineEventType
from app.services.financial_timeline.event_base import BaseEventBuilder, TimelineContext
from app.services.financial_timeline.models import TimelineEvent
from app.services.financial_timeline.utils import to_datetime


class SalaryEventBuilder(BaseEventBuilder):
    """Detects salary credits."""
    name = "SalaryEventBuilder"

    def build(self, ctx: TimelineContext) -> list[TimelineEvent]:
        events = []
        for tx in ctx.transactions:
            if tx.transaction_type == 'income' and tx.amount > Decimal('500'):
                # Simple heuristic: category contains 'salary' or description contains 'salary/payroll'
                is_salary = False
                if tx.category and 'salary' in tx.category.name.lower():
                    is_salary = True
                elif 'salary' in tx.description.lower() or 'payroll' in tx.description.lower():
                    is_salary = True
                
                if is_salary:
                    events.append(
                        TimelineEvent(
                            type=TimelineEventType.SALARY_CREDITED,
                            severity=TimelineEventSeverity.SUCCESS,
                            title="Salary Credited",
                            description=f"Received ₹{tx.amount:,.0f} from {tx.merchant or 'employer'}.",
                            timestamp=to_datetime(tx.transaction_date),
                            related_transaction_ids=[str(tx.id)],
                            metadata={"amount": float(tx.amount), "merchant": tx.merchant},
                        )
                    )
        return events


class LargeTransactionEventBuilder(BaseEventBuilder):
    """Detects very large purchases or refunds."""
    name = "LargeTransactionEventBuilder"

    def build(self, ctx: TimelineContext) -> list[TimelineEvent]:
        events = []
        # For simplicity, let's say > 50k is large
        threshold = Decimal('50000')
        
        for tx in ctx.transactions:
            if tx.amount > threshold:
                if tx.transaction_type == 'expense':
                    events.append(
                        TimelineEvent(
                            type=TimelineEventType.LARGE_PURCHASE,
                            severity=TimelineEventSeverity.INFO,
                            title="Large Purchase",
                            description=f"Spent ₹{tx.amount:,.0f} at {tx.merchant or tx.description}.",
                            timestamp=to_datetime(tx.transaction_date),
                            related_transaction_ids=[str(tx.id)],
                            metadata={"amount": float(tx.amount), "merchant": tx.merchant},
                        )
                    )
                else:
                    # Not salary (already handled), large income = refund or other
                    events.append(
                        TimelineEvent(
                            type=TimelineEventType.LARGE_REFUND,
                            severity=TimelineEventSeverity.INFO,
                            title="Large Inflow",
                            description=f"Received ₹{tx.amount:,.0f} from {tx.merchant or tx.description}.",
                            timestamp=to_datetime(tx.transaction_date),
                            related_transaction_ids=[str(tx.id)],
                            metadata={"amount": float(tx.amount), "merchant": tx.merchant},
                        )
                    )
        return events
