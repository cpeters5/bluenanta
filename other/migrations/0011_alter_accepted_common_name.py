# Generated by Django 3.2.13 on 2022-06-20 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0010_alter_species_genus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accepted',
            name='common_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
