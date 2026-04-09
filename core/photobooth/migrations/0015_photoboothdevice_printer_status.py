from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photobooth', '0014_capturepackage_description_line_1_en_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='photoboothdevice',
            name='printer_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='photoboothdevice',
            name='printer_connected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='photoboothdevice',
            name='printer_ready',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='photoboothdevice',
            name='printer_has_error',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='photoboothdevice',
            name='printer_status',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='photoboothdevice',
            name='printer_error_state',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='photoboothdevice',
            name='printer_message',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='photoboothdevice',
            name='printer_status_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
