import unittest
import redis
import bcrypt
from config_redis import username, password, host, port
from utils import key_user_password

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.red = redis.Redis(
            host=host,
            port=port,
            db=0,
            username=username,
            password=password,
            decode_responses=True
        )
        self.test_user_id = "test:99"
        self.test_password = "1234"
        self.test_key = key_user_password(self.test_user_id)

        # Pulizia prima del test
        self.red.delete(self.test_key)

    def test_registrazione_password_hashata(self):
        hashed_pw = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.red.set(self.test_key, hashed_pw)

        stored = self.red.get(self.test_key)
        self.assertTrue(bcrypt.checkpw(self.test_password.encode('utf-8'), stored.encode('utf-8')))

    def tearDown(self):
        self.red.delete(self.test_key)

if __name__ == '__main__':
    unittest.main()
