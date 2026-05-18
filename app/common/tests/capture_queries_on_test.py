from django.db import connection
from django.test.utils import CaptureQueriesContext


class CaptureQueriesOnTestMixin:  # pragma: nocover this is a test library
    def get_num_queries(self, queries, query_statement):
        return len([query for query in queries if query_statement in query['sql']])

    def capture_queries(self):
        return CaptureQueriesContext(connection)
