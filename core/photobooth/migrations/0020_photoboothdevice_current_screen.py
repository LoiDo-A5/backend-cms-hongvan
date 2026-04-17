from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photobooth', '0019_paymentorder_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='photoboothdevice',
            name='current_screen',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Màn hình hiện tại trên app Electron (welcome, package, payment, capture, printing, …).',
                max_length=50,
            ),
        ),
    ]
