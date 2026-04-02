from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photobooth', '0008_alter_paymentorder_capture_package'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhotoboothDecorFrame',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(help_text='Mã cố định cho API/FE, ví dụ: classic-gold, polaroid-01', max_length=64, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('image', models.ImageField(blank=True, help_text='Ảnh thumbnail / preview khung trên UI.', null=True, upload_to='photobooth/decor_frames/')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Khung trang trí',
                'verbose_name_plural': 'Khung trang trí',
                'db_table': 'photobooth_decor_frame',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='photoboothdevice',
            name='decor_frames',
            field=models.ManyToManyField(
                blank=True,
                related_name='devices',
                to='photobooth.photoboothdecorframe',
                verbose_name='Khung trang trí',
            ),
        ),
    ]
