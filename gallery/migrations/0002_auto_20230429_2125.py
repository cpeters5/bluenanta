# Generated by Django 3.2.15 on 2023-04-29 21:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='city',
            name='city_name',
        ),
        migrations.RemoveField(
            model_name='gallery',
            name='city_name',
        ),
        migrations.AddField(
            model_name='city',
            name='city',
            field=models.CharField(db_column='city', default='', max_length=200, primary_key=True, serialize=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gallery',
            name='city',
            field=models.ForeignKey(db_column='city', default='', on_delete=django.db.models.deletion.DO_NOTHING, related_name='galcity', to='gallery.city'),
        ),
    ]
