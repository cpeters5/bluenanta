# Generated by Django 3.2.15 on 2024-05-03 23:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aves', '0003_auto_20240430_2142'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spcimages',
            name='image_file_path',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to='utils/images/photos'),
        ),
        migrations.AlterField(
            model_name='uploadfile',
            name='image_file_path',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to='images/'),
        ),
        migrations.AlterField(
            model_name='video',
            name='video_file_path',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to='utils/images/photos'),
        ),
    ]
