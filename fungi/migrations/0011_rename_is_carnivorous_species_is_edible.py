# Generated by Django 3.2.15 on 2022-12-27 11:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fungi', '0010_rename_is_succulent_species_is_poisonous'),
    ]

    operations = [
        migrations.RenameField(
            model_name='species',
            old_name='is_carnivorous',
            new_name='is_edible',
        ),
    ]