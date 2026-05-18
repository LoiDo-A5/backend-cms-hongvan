from django.db import migrations
from django.db import models

import common.abstract_models.image_field


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='accordion_background_image',
            field=common.abstract_models.image_field.CustomImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='project',
            name='accordion_items',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='project',
            name='accordion_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='project',
            name='cta_button_label',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='project',
            name='cta_button_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='cta_content',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='cta_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='project',
            name='features',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='project',
            name='hero_content',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='hero_image',
            field=common.abstract_models.image_field.CustomImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='project',
            name='hero_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='project',
            name='long_description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='long_description_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='project',
            name='section_background_image',
            field=common.abstract_models.image_field.CustomImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='project',
            name='website_card_content',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='website_card_thumbnail',
            field=common.abstract_models.image_field.CustomImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='project',
            name='website_card_title',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]