from django.core.cache import cache
from django.test import SimpleTestCase

from common.utils.custom_cache import count_key_match_from_cache


class CustomCacheTest(SimpleTestCase):
    def test_pattern_cache(self):
        keys = {f'UNIQUE_CACHE_TEST_{x}': x for x in range(1001)}
        cache.set_many(keys)
        self.assertEqual(1001, count_key_match_from_cache('UNIQUE_CACHE_TEST_*'))
