# Generated by Django 3.1.6 on 2021-03-22 00:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_taxonomy'),
    ]

    operations = [
        migrations.AddField(
            model_name='family',
            name='application',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
    ]
