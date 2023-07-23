# Generated by Django 3.2.15 on 2023-07-13 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0013_artist_image_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='artwork',
            name='name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='artist',
            name='image_file',
            field=models.ImageField(blank=True, null=True, upload_to='gallery/'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='status',
            field=models.CharField(choices=[('NFS', 'not for sale'), ('AV', 'available'), ('PUR', 'price upon request')], default='', max_length=20),
        ),
    ]
