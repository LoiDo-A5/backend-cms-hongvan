from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('photobooth', '0007_filter_background_and_device_m2m'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentorder',
            name='capture_package',
            field=models.ForeignKey(
                help_text='Gói chụp mà khách đã chọn khi tạo đơn VNPAY này.',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payment_orders',
                to='photobooth.capturepackage',
                verbose_name='Gói chụp đi kèm đơn',
            ),
        ),
    ]
