# Generated by Django 3.2.13 on 2022-06-20 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_alter_subfamily_family'),
    ]

    operations = [
        migrations.AlterField(
            model_name='family',
            name='year',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subtribe',
            name='year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
