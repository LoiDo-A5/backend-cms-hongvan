# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('artwork', '0118_rename_artwork_col_trans_idx_artwork_col_transfe_f95fb0_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='artworkedition',
            name='transferee',
            field=models.ForeignKey(
                blank=True,
                help_text='User who received this edition when the artist transferred ownership.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='artwork_edition_transfers_received',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
