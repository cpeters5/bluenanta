# Generated by Django 3.2.15 on 2024-04-27 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orchidaceae', '0003_remove_species_conservation_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='hybimages',
            name='binomial',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='spcimages',
            name='binomial',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]