from io import StringIO

from django.core.management import call_command

from common.tests.isolated_cache_test_case import TestCase


class InternalRuleTests(TestCase):
    def test_api_must_end_with_slash(self):
        out = StringIO()
        call_command('show_urls', stdout=out)
        wrong = []
        for line in out.getvalue().splitlines():
            path = line.split()[0]

            if path.startswith('/api/') and not path.endswith('/'):  # pragma: nocover as it only happen when test fail
                wrong.append(path)

        self.assertEqual(wrong, [], 'Api must end with slash.')
