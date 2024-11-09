import unittest
from .. import app, db
from ..models import User
from werkzeug.security import generate_password_hash

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
        self.assertTrue(u.verify_password('testpass'))

if __name__ == '__main__':
    unittest.main()
