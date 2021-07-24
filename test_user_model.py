"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Tests for User Model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
    
    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_repr_user(self):
        """Tests repr method in User Model"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        return_value = repr(u)
        self.assertEqual(return_value, f"<User #{u.id}: {u.username}, {u.email}>" )

    def test_not_following(self):
        """Tests whether is_following successfully detects when user1 is not following user2"""
        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD1"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add_all([u1, u2])
        db.session.commit()

        return_value = u1.is_following(u2)
        self.assertFalse(return_value)

    def test_is_following(self):
        """Tests whether is_following successfully detects when user1 is following user2"""
        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD1"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add_all([u1, u2])
        db.session.commit()

        u1_follows_u2 = Follows(
            user_being_followed_id = u2.id,
            user_following_id = u1.id
        )

        db.session.add(u1_follows_u2)
        db.session.commit()

        return_value = u1.is_following(u2)
        self.assertTrue(return_value)

    def test_not_followed(self):
        """Tests whether is_followed successfully detects when user1 is not following user2"""
        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD1"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add_all([u1, u2])
        db.session.commit()

        return_value = u1.is_followed_by(u2)
        self.assertFalse(return_value)

    def test_is_followed(self):
        """Tests whether is_followed successfully detects when user1 is following user2"""
        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD1"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add_all([u1, u2])
        db.session.commit()

        u1_followed_by_u2 = Follows(
            user_being_followed_id = u1.id,
            user_following_id = u2.id
        )

        db.session.add(u1_followed_by_u2)
        db.session.commit()

        return_value = u1.is_followed_by(u2)
        self.assertTrue(return_value)
    
    def test_signup_valid(self):
        """Tests if class method signup creates a new user given valid credentials"""

        return_value = User.signup(
            'testuser',
            'testuser@test.com',
            'HASHED_PASSWORD',
            'test.jpg'
        )

        db.session.commit()
        user = repr(return_value)
        

        self.assertIsInstance(return_value, User)
        self.assertIn('testuser', user)
        self.assertIn('testuser@test.com', user)
        self.assertEqual(len(User.query.all()), 1)


    def test_signup_invalid_duplicate_entry(self):
        """Tests if class method signup raises an error when given invalid credentials (duplicate entry)"""

        return_value = User.signup(
            'testuser',
            'testuser@test.com',
            'HASHED_PASSWORD',
            'test.jpg'
        )

        db.session.commit()

        self.assertEqual(len(User.query.all()), 1)
        with self.assertRaises(IntegrityError):
            User.signup('testuser', 'testuser@gtest.com', 'HASHED_PASSWORD', 'test.jpg')
            db.session.commit()
            self.assertIsInstance(cm.exception, IntegrityError)
            self.assertEqual(len(User.query.all()), 1)

    def test_signup_invalid_missing_entry(self):
        """Tests if class method signup raises an error when given invalid credentials (missing required input)"""


        with self.assertRaises(IntegrityError) as cm:
            User.signup('testuser2', None, 'HASHED_PASSWORD', 'test.jpg')
            db.session.commit()
       
            self.assertIsInstance(cm.exception, IntegrityError)
            self.assertEqual(len(User.query.all()), 1)

    def test_authenticate_valid_credentials(self):
        """Tests if class method autheticate returns a user with valid credentials"""
    
        u = User.signup(
            'testuser',
            'testuser@test.com',
            'HASHED_PASSWORD',
            'test.jpg'
        )
        uid = 99999
        u.id = uid
        db.session.commit()

        user = User.query.get(uid)
        return_value = User.authenticate("testuser", "HASHED_PASSWORD")

        self.assertEqual(user, return_value)

    def test_authenticate_invalid_username(self):
        """Tests if class method autheticate returns false with invalid username"""
    
        u = User.signup(
            'testuser',
            'testuser@test.com',
            'HASHED_PASSWORD',
            'test.jpg'
        )
        uid = 99999
        u.id = uid
        db.session.commit()

        user = User.query.get(uid)
        return_value = User.authenticate("testuser2", "HASHED_PASSWORD")

        self.assertNotEqual(user, return_value)
        self.assertFalse(return_value)

    def test_authenticate_invalid_password(self):
        """Tests if class method autheticate returns false with invalid password"""

        u = User.signup(
            'testuser',
            'testuser@test.com',
            'HASHED_PASSWORD',
            'test.jpg'
        )
        uid = 99999
        u.id = uid
        db.session.commit()

        user = User.query.get(uid)
        return_value = User.authenticate("testuser", "HASHED_PASSWORD2")

        self.assertNotEqual(user, return_value)
        self.assertFalse(return_value)



        
        


