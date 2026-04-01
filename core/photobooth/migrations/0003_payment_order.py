from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('photobooth', '0002_seed_default_packages'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('txn_ref', models.CharField(db_index=True, max_length=100, unique=True)),
                ('amount_vnd', models.PositiveIntegerField()),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('pending', 'Chờ thanh toán'),
                            ('paid', 'Đã thanh toán'),
                            ('failed', 'Thất bại'),
                            ('expired', 'Hết hạn'),
                        ],
                        db_index=True,
                        default='pending',
                        max_length=16,
                    ),
                ),
                ('booth_id', models.CharField(blank=True, default='', max_length=64)),
                ('vnp_transaction_no', models.CharField(blank=True, default='', max_length=32)),
                ('vnp_response_code', models.CharField(blank=True, default='', max_length=8)),
                ('vnp_transaction_status', models.CharField(blank=True, default='', max_length=8)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'capture_package',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='payment_orders',
                        to='photobooth.capturepackage',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Đơn thanh toán VNPAY',
                'verbose_name_plural': 'Đơn thanh toán VNPAY',
                'db_table': 'photobooth_payment_order',
                'ordering': ['-id'],
            },
        ),
    ]
