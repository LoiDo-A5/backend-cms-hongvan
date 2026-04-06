from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('photobooth', '0012_imagephotobooth'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentorder',
            name='device',
            field=models.ForeignKey(
                blank=True,
                help_text='Thiết bị đã tạo đơn thanh toán này.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payment_orders',
                to='photobooth.photoboothdevice',
                verbose_name='Thiết bị photobooth',
            ),
        ),
    ]
