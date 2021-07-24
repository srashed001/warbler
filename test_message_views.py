"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_delete_message(self):
        """Can use delete a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message(text='test', user_id=self.testuser.id)
            mid = 99999
            m.id = mid 
            db.session.add(m)
            db.session.commit()

            resp = c.post(f'messages/{mid}/delete')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(Message.query.all()), 0)
   
   
    def test_add_message_without_logging_in(self):
        """Can use add a message?"""

        with self.client as c:
            # no sess[CURR_USER_KEY] to emulate not being logged in
            resp = c.post("/messages/new", data={"text": "Hello"})

            msg = Message.query.first()

            self.assertEqual(resp.status_code, 302)
            self.assertIsNone(msg)
            self.assertEqual(resp.location, "http://localhost/")
        
        
    def test_delete_message_without_logging_in(self):
        """Can use delete a message?"""

        with self.client as c:
            m = Message(text='test', user_id=self.testuser.id)
            mid = 99999
            m.id = mid 
            db.session.add(m)
            db.session.commit()

            resp = c.post(f'messages/{mid}/delete')
            msg = Message.query.first()

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(Message.query.all()), 1)
            self.assertEqual(Message.query.get(mid), msg)
            self.assertEqual(resp.location, "http://localhost/")

    def test_add_message_as_another_user(self):
        """Tests that you cannot add a message as another user"""

        with self.client as c:
            with c.session_transaction() as sess:

                sess[CURR_USER_KEY] = self.testuser.id

            other_user = User.signup(username="testuser2",
                                        email="test@test2.com",
                                        password="testuser2",
                                        image_url=None)
            uid = 99999
            other_user.id = uid
            db.session.add(other_user)
            db.session.commit()
            
            resp = c.post("/messages/new", data={"text": "Hello", "user_id": uid})

            other_user = User.query.get(uid)
            user = User.query.get(self.testuser.id)
            

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/users/{self.testuser.id}")
            self.assertEqual(len(other_user.messages), 0)
            self.assertEqual(len(user.messages), 1)



    def test_delete_message_as_another_user(self):
        """Tests that you cannot delete a nessage as another user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            other_user = User.signup(username="testuser2",
                                        email="test@test2.com",
                                        password="testuser2",
                                        image_url=None)
            uid = 99999
            other_user.id = uid
            db.session.add(other_user)
            db.session.commit()

            m = Message(text='test', user_id=uid)
            mid = 99999
            m.id = mid 
            db.session.add(m)
            db.session.commit()

            resp = c.post(f'messages/{mid}/delete')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/")
            self.assertEqual(len(other_user.messages), 1)
       
            

    
