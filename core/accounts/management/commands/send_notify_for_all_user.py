import pytz  # pragma: nocover
from django.conf import settings  # pragma: nocover
from django.core.management.base import BaseCommand  # pragma: nocover
from django.utils import timezone  # pragma: nocover

from core.accounts.models import User  # pragma: nocover
from core.kits.models import Icon  # pragma: nocover
from core.notifications.const import NOTIFICATIONS_CONTENT_CODE  # pragma: nocover
from core.notifications.const import NOTIFICATIONS_TYPE  # pragma: nocover
from core.notifications.tasks import make_notification_message  # pragma: nocover


class Command(BaseCommand):  # pragma: nocover because just run when deploy production

    def handle(self, *args, **options):
        today = timezone.now().astimezone(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%H:%M %d-%m-%Y')
        title = {
            'vi': f'Thông báo nâng cấp hệ thống {today}',
            'en': f'System upgrade notice {today}',
        }
        message = {
            'vi': 'Để mang lại trải nghiệm tốt hơn cho người dùng, [Era] sẽ tiến hành nâng cấp hệ thống. '
                  'Việc nâng cấp sẽ diễn ra trong khoảng 10 phút.\n\n'
                  'Hệ thống vẫn làm việc bình thường. Tuy nhiên có thể một số tính năng gián đoạn trong thời gian này. '
                  '[Era] kính mong quý khách hàng thông cảm cho sự bất tiện này.\n\n'
                  'Trân trọng.',
            'en': 'To provide a better user experience, [Era] will proceed with system upgrade. '
                  'The upgrade will take about 10 minutes.\n\n'
                  'The system is still working normally. However, some features may be interrupted during this time. '
                  '[Era] would like to ask for your understanding for this inconvenience.\n\n'
                  'Best regards.',
        }
        icon_kit = Icon.objects.get(name=settings.NOTIFICATION_DEFAULT_ICON_NAME)

        for user in User.objects.all():
            make_notification_message(
                user=user,
                title=title,
                content=message,
                notification_kwargs={
                    'icon': getattr(icon_kit, 'icon', None),
                    'type': NOTIFICATIONS_TYPE.NEWS,
                    'content_code': NOTIFICATIONS_CONTENT_CODE.NOTIFY_UPGRADE_SYSTEM,
                    'business': 'smart_city',
                },
                push_kwargs={
                    'small_icon': 'ic_stat_onesignal_default',
                    'data': {'content_code': NOTIFICATIONS_CONTENT_CODE.NOTIFY_UPGRADE_SYSTEM},
                },
            )
