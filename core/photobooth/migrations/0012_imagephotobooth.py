from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('photobooth', '0011_alter_paymentorder_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImagePhotobooth',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='photobooth/images/%Y/%m/%d/', verbose_name='Ảnh chụp')),
                ('round_index', models.PositiveSmallIntegerField(default=0, help_text='Thứ tự lượt chụp (0-based).')),
                ('photo_index', models.PositiveSmallIntegerField(default=0, help_text='Thứ tự ảnh trong lượt (0-based).')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payment_order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='images',
                    to='photobooth.paymentorder',
                    verbose_name='Đơn thanh toán',
                )),
            ],
            options={
                'verbose_name': 'Ảnh Photobooth',
                'verbose_name_plural': 'Ảnh Photobooth',
                'db_table': 'photobooth_image',
                'ordering': ['payment_order', 'round_index', 'photo_index', 'id'],
            },
        ),
    ]
