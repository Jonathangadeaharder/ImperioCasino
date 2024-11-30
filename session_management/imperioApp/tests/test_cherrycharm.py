from ..game_logic.cherrycharm import spin_reels, get_fruits, calculate_winnings, executeSpin, Fruit, segment_to_fruit
from ..utils.services import create_user
from .. import db
from .base_test import BaseTestCase

class CherryCharmTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = create_user('testuser', 'test@example.com', 'testpassword')

    def test_spin_reels(self):
        segments = spin_reels()
        self.assertEqual(len(segments), 3)
        for segment in segments:
            self.assertTrue(15 <= segment <= 30)

    def test_segment_to_fruit(self):
        fruit = segment_to_fruit(0, 16)  # 16 /2 = 8
        self.assertEqual(fruit, Fruit.CHERRY)
        fruit = segment_to_fruit(1, 24)  # 24 /2 =12
        self.assertEqual(fruit, Fruit.CHERRY)
        fruit = segment_to_fruit(2, 24)  # 24 /2 =12
        self.assertEqual(fruit, Fruit.CHERRY)

    def test_get_fruits(self):
        stop_segments = [16, 24, 24]  # Should map to CHERRY, CHERRY, CHERRY
        fruits = get_fruits(stop_segments)
        self.assertEqual(fruits, [Fruit.CHERRY, Fruit.CHERRY, Fruit.CHERRY])

    def test_calculate_winnings(self):
        winnings = calculate_winnings([Fruit.CHERRY, Fruit.CHERRY, Fruit.CHERRY])
        self.assertEqual(winnings, 50)
        winnings = calculate_winnings([Fruit.CHERRY, Fruit.CHERRY, Fruit.APPLE])
        self.assertEqual(winnings, 40)
        winnings = calculate_winnings([Fruit.LEMON, Fruit.LEMON, Fruit.LEMON])
        self.assertEqual(winnings, 3)
        winnings = calculate_winnings([Fruit.BANANA, Fruit.BANANA, Fruit.BANANA])
        self.assertEqual(winnings, 15)

    def test_executeSpin(self):
        self.user.coins = 10
        db.session.commit()
        response, status_code = executeSpin(self.user)
        self.assertEqual(status_code, 200)
        data = response.get_json()
        self.assertIn('stopSegments', data)
        self.assertIn('totalCoins', data)
        self.assertEqual(data['totalCoins'], self.user.coins)

    def test_executeSpin_not_enough_coins(self):
        self.user.coins = 0
        db.session.commit()
        response, status_code = executeSpin(self.user)
        self.assertEqual(status_code, 400)
        data = response.get_json()
        self.assertEqual(data['message'], 'Not enough coins to spin')
