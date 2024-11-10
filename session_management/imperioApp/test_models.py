import unittest
from . import app, db
from .models import User

class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        u = User(username='testuser', email='test@example.com')
        u.set_password('testpass')
        db.session.add(u)
        db.session.commit()
        self.assertEqual(u.username, 'testuser')
        self.assertEqual(u.email, 'test@example.com')
        self.assertTrue(u.verify_password('testpass'))
        # Check that coins default to 100
        self.assertEqual(u.coins, 100)

    def test_user_coins_assignment(self):
        # Create a user with a specific coins value
        u = User(username='richuser', email='rich@example.com', coins=1000)
        u.set_password('richpass')
        db.session.add(u)
        db.session.commit()
        self.assertEqual(u.coins, 1000)

if __name__ == '__main__':
    unittest.main()
