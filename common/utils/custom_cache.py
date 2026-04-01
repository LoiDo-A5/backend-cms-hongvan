from django.core.cache import cache
from django_redis import get_redis_connection
from celery import shared_task


class CustomRedisCache:
    connection = None

    def count(self, pattern: str = '*') -> int:
        index = 0
        result = []
        while True:
            index, scan_result = self.connection.scan(index, f'{cache.key_prefix}:*{pattern}', 1000)
            result.extend(scan_result)
            if index == 0:
                break
        return len(result)

    def __init__(self, alias: str = 'default'):
        self.connection = get_redis_connection(alias)


@shared_task(queue='custom_cache_count')
def count_key_match_from_cache(pattern: str = '*') -> int:
    return CustomRedisCache().count(pattern)
