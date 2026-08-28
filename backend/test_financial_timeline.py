import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.services.financial_timeline.enums import TimelineEventType, TimelineEventSeverity
from app.services.financial_timeline.models import TimelineEvent
from app.services.financial_timeline.engine import FinancialTimelineEngine
from app.services.financial_timeline.event_base import TimelineContext
from app.services.financial_timeline.builders.transaction_events import SalaryEventBuilder, LargeTransactionEventBuilder

def test_salary_builder():
    builder = SalaryEventBuilder()
    
    # Mock transaction class
    class MockTx:
        def __init__(self, id, type, amt, desc, cat, dt):
            self.id = id
            self.transaction_type = type
            self.amount = amt
            self.description = desc
            self.category = cat
            self.transaction_date = dt
            self.merchant = desc

    txs = [
        MockTx(uuid4(), 'income', Decimal('60000'), 'Payroll', None, date.today()),
        MockTx(uuid4(), 'income', Decimal('100'), 'Gift', None, date.today())
    ]
    
    ctx = TimelineContext(
        user_id=str(uuid4()),
        today=date.today(),
        transactions=txs
    )
    
    events = builder.build(ctx)
    assert len(events) == 1
    assert events[0].type == TimelineEventType.SALARY_CREDITED
    assert events[0].title == "Salary Credited"

def test_large_transaction_builder():
    builder = LargeTransactionEventBuilder()
    
    # Mock transaction class
    class MockTx:
        def __init__(self, id, type, amt, desc, cat, dt):
            self.id = id
            self.transaction_type = type
            self.amount = amt
            self.description = desc
            self.category = cat
            self.transaction_date = dt
            self.merchant = desc

    txs = [
        MockTx(uuid4(), 'expense', Decimal('60000'), 'Apple Store', None, date.today()),
        MockTx(uuid4(), 'expense', Decimal('100'), 'Coffee', None, date.today())
    ]
    
    ctx = TimelineContext(
        user_id=str(uuid4()),
        today=date.today(),
        transactions=txs
    )
    
    events = builder.build(ctx)
    assert len(events) == 1
    assert events[0].type == TimelineEventType.LARGE_PURCHASE
    assert events[0].title == "Large Purchase"
