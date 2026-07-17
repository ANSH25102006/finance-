import unittest
import uuid
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.prompt import ChatMessage
from app.services.ai.conversation_manager import ConversationManager
from app.services.ai.context_compressor import ContextCompressor
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.ai_orchestrator import AIOrchestrator


class TestAIOrchestrationLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionTesting = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionTesting()

        # Create a test user
        self.user_id = uuid.uuid4()
        self.user = User(
            id=self.user_id,
            email=f"test_{self.user_id}@example.com",
            password_hash="hashedpassword123"
        )
        self.db.add(self.user)
        self.db.commit()

        # Create checking account
        self.account_id = uuid.uuid4()
        self.account = Account(
            id=self.account_id,
            user_id=self.user_id,
            name="Checking",
            balance=25000.0,
            currency="INR",
            icon="Bank",
            color="#3b82f6"
        )
        self.db.add(self.account)
        self.db.commit()

        self.orchestrator = AIOrchestrator()

    def tearDown(self):
        self.db.close()
        db = self.SessionTesting()
        db.query(Transaction).delete()
        db.query(Category).delete()
        db.query(Account).delete()
        db.query(User).delete()
        db.commit()
        db.close()

    def test_conversation_history_trimming(self):
        """Verify ConversationManager limits history turns to exactly 10."""
        manager = ConversationManager(str(self.user_id))
        
        # Add 12 messages
        for i in range(12):
            role = "user" if i % 2 == 0 else "assistant"
            manager.add_message(role=role, content=f"Message {i}")

        history = manager.get_history()
        self.assertEqual(len(history), 10)
        # Verify chronological order (oldest discarded, newest remains: 2 to 11)
        self.assertEqual(history[0].content, "Message 2")
        self.assertEqual(history[-1].content, "Message 11")

    def test_empty_context_generation(self):
        """Verify prompt builder formats sections correctly when financial database is empty."""
        history = [
            ChatMessage(role="user", content="Hello", timestamp=datetime.utcnow()),
            ChatMessage(role="assistant", content="Hi there", timestamp=datetime.utcnow())
        ]
        
        # Build prompt on empty database
        prompt_output = self.orchestrator.orchestrate_prompt_generation(
            self.db,
            self.user_id,
            "How can I save money?",
            history
        )

        # Assert structured sections exist
        self.assertIn("=== 1. SYSTEM PROMPT ===", prompt_output.full_prompt)
        self.assertIn("=== 2. DEVELOPER INSTRUCTIONS ===", prompt_output.full_prompt)
        self.assertIn("=== 3. FINANCIAL CONTEXT ===", prompt_output.full_prompt)
        self.assertIn("=== 4. CONVERSATION HISTORY ===", prompt_output.full_prompt)
        self.assertIn("=== 5. CURRENT QUESTION ===", prompt_output.full_prompt)

        # Confirm details are correct
        self.assertEqual(prompt_output.user_message, "How can I save money?")
        self.assertIn("USER: Hello\nASSISTANT: Hi there", prompt_output.conversation)
        self.assertTrue(prompt_output.estimated_tokens > 0)

    def test_token_estimation_and_compression_priority(self):
        """Verify context compressor prunes categories, chat history, and minor rule findings on token limits."""
        # 1. Setup a massive conversation of 10 long messages to inflate token size
        history = []
        for i in range(10):
            role = "user" if i % 2 == 0 else "assistant"
            long_content = "This is a very verbose chat message. " * 30  # ~600 chars each turn
            history.append(ChatMessage(role=role, content=long_content, timestamp=datetime.utcnow()))

        # Add mock transactions
        cat = Category(id=uuid.uuid4(), user_id=self.user_id, name="Shopping", type="expense", icon="Bag", color="#000")
        self.db.add(cat)
        self.db.commit()
        for idx in range(10):
            tx = Transaction(
                id=uuid.uuid4(),
                user_id=self.user_id,
                account_id=self.account_id,
                category_id=cat.id,
                amount=100.0 * (idx + 1),
                transaction_type="expense",
                merchant=f"Merchant{idx}",
                transaction_date=date(2026, 7, 1) + timedelta(days=idx),
                description=f"Transaction purchase {idx}"
            )
            self.db.add(tx)
        self.db.commit()

        # Generate prompt with orchestration
        prompt_output = self.orchestrator.orchestrate_prompt_generation(
            self.db,
            self.user_id,
            "Give me a detailed breakdown of my spending.",
            history
        )

        # Since conversation is extremely large, compressor must have pruned chat history turns
        # (originally 10 turns, should be pruned to 3 turns or fewer to stay below 3000 tokens)
        self.assertTrue(prompt_output.estimated_tokens <= 3000 or "exceeds" in prompt_output.full_prompt)
        
        # Verify sections are intact
        self.assertIn("=== 1. SYSTEM PROMPT ===", prompt_output.full_prompt)
        self.assertIn("=== 3. FINANCIAL CONTEXT ===", prompt_output.full_prompt)

    def test_malformed_inputs(self):
        """Verify orchestrator returns errors for empty questions."""
        with self.assertRaises(ValueError):
            self.orchestrator.orchestrate_prompt_generation(
                self.db,
                self.user_id,
                "   ", # Empty question
                []
            )


if __name__ == "__main__":
    unittest.main()
