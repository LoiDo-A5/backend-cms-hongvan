# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('artwork', '0116_alter_artwork_inventory_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectorOwnershipTransfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snapshot', models.JSONField()),
                ('transferred_at', models.DateTimeField(auto_now_add=True)),
                ('artwork', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='collector_ownership_transfers',
                    to='artwork.artwork',
                )),
                ('certificate', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='collector_ownership_transfers',
                    to='artwork.artworkcertificate',
                )),
                ('transferee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='collector_ownership_transfers_received',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('transferrer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='collector_ownership_transfers_sent',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ('-transferred_at', '-id'),
            },
        ),
        migrations.AddIndex(
            model_name='collectorownershiptransfer',
            index=models.Index(fields=['transferrer', '-transferred_at'], name='artwork_col_trans_idx'),
        ),
    ]
