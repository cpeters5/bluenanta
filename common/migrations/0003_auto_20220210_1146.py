# Generated by Django 3.2.5 on 2022-02-10 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_datasource'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasource',
            name='short_description',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='datasource',
            name='description',
            field=models.TextField(null=True),
        ),
    ]
