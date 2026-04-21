from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('txn_ref', models.CharField(db_index=True, max_length=100, unique=True)),
                ('amount_vnd', models.PositiveIntegerField()),
                ('description', models.CharField(blank=True, default='', max_length=255)),
                ('extra_data', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(
                    choices=[('pending', 'Chờ thanh toán'), ('paid', 'Đã thanh toán'), ('failed', 'Thất bại'), ('expired', 'Hết hạn')],
                    db_index=True, default='pending', max_length=16,
                )),
                ('payment_method', models.CharField(
                    choices=[('vietqr', 'VietQR (payOS)'), ('vnpay', 'VNPAY'), ('paypal', 'PayPal')],
                    db_index=True, default='vietqr', max_length=16, verbose_name='Phương thức thanh toán',
                )),
                ('payos_order_code', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('payos_payment_link_id', models.CharField(blank=True, default='', max_length=64)),
                ('paypal_order_id', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('vnp_transaction_no', models.CharField(blank=True, default='', max_length=32)),
                ('vnp_response_code', models.CharField(blank=True, default='', max_length=8)),
                ('vnp_transaction_status', models.CharField(blank=True, default='', max_length=8)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Đơn thanh toán',
                'verbose_name_plural': 'Đơn thanh toán',
                'ordering': ['-id'],
            },
        ),
    ]
