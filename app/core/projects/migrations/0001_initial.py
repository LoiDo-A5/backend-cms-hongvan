from django.conf import settings
from django.db import migrations
from django.db import models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('is_visible', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_projects', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_projects', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Dự án',
                'verbose_name_plural': 'Dự án',
                'ordering': ['-updated_at', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['id', 'active'], name='core_projec_id_e630f7_idx'),
        ),
    ]