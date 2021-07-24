"""User model tests."""

import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app

db.create_all()


class MessageModelTestCase(TestCase):
    """Tests for Message Model"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.u_id = u.id 
        self.u = u

    
    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="test",
            user_id = self.u_id
        )

        mid = 99999
        m.id = mid

        db.session.add(m)
        db.session.commit()

        m = Message.query.get(mid)

    
        self.assertIn('test', m.text)
        self.assertEqual(self.u_id, m.user_id)
        self.assertEqual(len(Message.query.all()), 1)
        self.assertEqual(len(self.u.messages), 1)
    
    def test_message_no_text_entry(self):
        """Tests whether error is raised if no text entry is provided"""

        m = Message(user_id = self.u_id)
        db.session.add(m)

        with self.assertRaises(IntegrityError) as cm:
            db.session.commit()
            
            self.assertIsInstance(cm.exception, IntegrityError)
            self.assertEqual(len(Message.query.all()), 1)

    def test_message_no_user_id_entry(self):
        """Tests whether error is raised if no text entry is provided"""

        m = Message(text = 'test')
        db.session.add(m)

        with self.assertRaises(IntegrityError) as cm:
            db.session.commit()
            
            self.assertIsInstance(cm.exception, IntegrityError)
            self.assertEqual(len(Message.query.all()), 1)


