# Generated by Django 3.2.15 on 2022-10-24 23:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0021_alter_distlocation_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='distlocation',
            name='name',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]