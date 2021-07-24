"""User View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for User."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.t1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="testuser1",
                                    image_url=None)
        self.t2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)
        db.session.commit()

        self.t2_follows_t1 = Follows(
            user_being_followed_id=self.t1.id,
            user_following_id = self.t2.id
        )
        self.t1_follows_t2 = Follows(
            user_being_followed_id=self.t2.id,
            user_following_id = self.t1.id
        )

        db.session.add_all([self.t2_follows_t1, self.t1_follows_t2])
        db.session.commit()

        self.t1_id = self.t1.id
        self.t2_id = self.t2.id
    
    def tearDown(self):
        db.session.rollback()

    def test_show_following_when_logged_in(self):
        """Tests that you are able to see your who you are following when you are logged in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.t1.id

            resp = c.get(f"/users/{self.t1.id}/following")
            html = resp.get_data(as_text=True)
    
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser2', html)
            self.assertIn('Unfollow', html)

    def test_show_following_when_logged_out(self):
        """Tests that you cannot see who you are following when you are logged out.
        It should redirect you to home page with Access unauthorized message"""

        with self.client as c:
            resp = c.get(f"/users/{self.t1.id}/following")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')
            
            resp = c.get(f"/users/{self.t1.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized', html)

    def test_show_followers_when_logged_in(self):
        """Tests that you are able to see your followers when you are logged in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.t1.id

            resp = c.get(f"/users/{self.t1.id}/followers")
            html = resp.get_data(as_text=True)
    
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser2', html)
            self.assertIn('Unfollow', html)

    def test_show_followers_when_logged_out(self):
        """Tests that you cannot see who your followers when you are logged out
        It should redirect you to home page with Access unauthorized message"""

        with self.client as c:
            resp = c.get(f"/users/{self.t1.id}/followers")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')
            
            resp = c.get(f"/users/{self.t1.id}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized', html)
    
    def test_add_follow_when_logged_in(self):
        """Test ability to add a follow when you are logged in.
        It should add follower and redirect you to following page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.t1.id
            
            t3 = User.signup(username="testuser3",
                                    email="test3@test.com",
                                    password="testuser3",
                                    image_url=None)
            tid = 99999
            t3.id = tid
            db.session.add(t3)
            db.session.commit()

            resp = c.post(f"/users/follow/{tid}")

            t1 = User.query.get(self.t1_id)
            follows = [follows.username for follows in t1.following]
    
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/users/{self.t1.id}/following")
            self.assertIn('testuser3', follows)
            
            resp = c.post(f"/users/follow/{tid}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn('testuser3', html)
            self.assertIn('Unfollow', html)

    def test_add_follow_when_logged_out(self):
        """Test ability to add a follow when you are logged out.
        It should not add follower and redirect you to home page with Access unauthorized message"""

        with self.client as c:
            t3 = User.signup(username="testuser3",
                                    email="test3@test.com",
                                    password="testuser3",
                                    image_url=None)
            tid = 99999
            t3.id = tid
            db.session.add(t3)
            db.session.commit()

            resp = c.post(f"/users/follow/{tid}")

            t1 = User.query.get(self.t1_id)
            follows = [follows.username for follows in t1.following]
    
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')
            self.assertNotIn('testuser3', follows)
            
            resp = c.post(f"/users/follow/{tid}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn('Access unauthorized', html)
    
    def test_get_show_profile_when_logged_in(self):
        """Tests rendering of edit profile page for user when logged in for you to edit profile information"""      
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.t1.id

            resp = c.get('/users/profile')
            html = resp.get_data(as_text=True)

            t1 = User.query.get(self.t1_id)

            self.assertIn('<form method="POST" id="user_form">', html)
            self.assertIn('input', html)
            self.assertIn(t1.username, html)
            self.assertIn(t1.email, html)
            self.assertIn('type="password"', html)

    def test_get_show_profile_when_logged_out(self):
        """Tests rendering of edit profile page for user when logged out.
        It should not render page and redirect you to home page with Access unauthorized message"""  

        with self.client as c:
            resp = c.get("/users/profile")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')
            
            resp = c.get(f"/users/profile", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized', html)
    
    def test_post_edit_profile_with_password(self):
        """Tests post request to edit profile information with password authentication
        It should process request and redirect to user details page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.t1.id

            resp = c.post("/users/profile", data={'username':"TESTUSER001",
                                    "bio":"testbio",
                                    "email":"test1@test.com",
                                    "password":"testuser1"})
                                    
            t1 = User.query.get(self.t1_id)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f'http://localhost/users/{self.t1.id}')
            self.assertEqual('TESTUSER001', t1.username)

    def test_post_edit_profile_without_password(self):
        """Tests post request to edit profile information without password authentication
        It should not process request and redirect to home page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.t1.id

            resp = c.post("/users/profile", data={'username':"TESTUSER001",
                                    "bio":"testbio",
                                    "email":"test1@test.com"})
                                    
            t1 = User.query.get(self.t1_id)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f'http://localhost/')
            self.assertNotEqual('TESTUSER001', t1.username)
    
    def test_delete_user_when_logged_in(self):
        """Tests the ability to delete yourself as a user when logged in.
        It should process delete request and redirect you to the signup page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.t1.id

            resp = c.post("/users/delete")
            t1 = User.query.filter_by(id = self.t1_id).first()

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/signup')
            self.assertIsNone(t1)

    def test_delete_user_when_logged_out(self):
        """Tests the ability to delete yourself as a user when logged out.
        It should not process delete request and redirect you to the signup page"""

        with self.client as c:
         
            resp = c.post("/users/delete")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f'http://localhost/')
            
            resp = c.post("/users/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized', html)











    