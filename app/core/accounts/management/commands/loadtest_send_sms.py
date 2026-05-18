from django.utils import timezone  # pragma: nocover
from django.conf import settings  # pragma: nocover
from django.core.management.base import BaseCommand  # pragma: nocover

from core.accounts.tasks import send_sms_real  # pragma: nocover
from core.accounts.utils import login_content_generator  # pragma: nocover


class Command(BaseCommand):  # pragma: nocover
    def handle(self, *args, **options):
        total = input('How many phone numbers do you want to send sms to? ')
        str_phone_number = input('String phone number (0902... 0903... ): ')
        repeat = int(input('Number of repeat (default is 1): ') or 1)

        if not total or not str_phone_number:
            self.stdout.write('Please enter all information.')
            return

        list_phone_number = str_phone_number.split()
        if int(total) != len(list_phone_number):
            self.stdout.write(f'The list of phone numbers is not enough for {total} numbers. Please re-enter')
            return

        count = 0
        t1 = timezone.now()
        self.stdout.write('START: ' + t1.strftime('%Y-%m-%d %H:%M:%S'))

        for i in range(1, repeat + 1):
            otp = '{:06}'.format(i)
            for phone_number in list_phone_number:
                send_sms_real.delay(phone_number, login_content_generator(otp, settings.SMS_OPT_TIMEOUT))
                count += 1
        t2 = timezone.now()
        self.stdout.write('END: ' + t2.strftime('%Y-%m-%d %H:%M:%S'))
        self.stdout.write(f'Total seconds: {(t2 - t1).total_seconds()}')
        self.stdout.write(f'Total number of sms: {count}')
        self.stdout.write('Done.')
