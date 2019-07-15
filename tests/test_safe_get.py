from unittest import TestCase

from start import asset


class TestSafeGet(TestCase):

    def test_safe_get_should_return_1234(self):
        result = asset.safe_get({
            'test': 1234
        }, -1, 'test')
        self.assertEqual(result, 1234)

    def test_safe_get_should_return_it(self):
        result = asset.safe_get({
            'test': {
                'nested': {
                    'result': True,
                }
            }
        }, 'False', 'test', 'nested', 'result')
        self.assertTrue(result)

    def test_safe_get_should_return_default_value(self):
        result = asset.safe_get({}, 'result', 'test', 'it')
        self.assertEqual(result, 'result')
