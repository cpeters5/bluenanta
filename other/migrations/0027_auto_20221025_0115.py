# Generated by Django 3.2.15 on 2022-10-25 01:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0026_distribution_dist'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='distribution',
            name='dist',
        ),
        migrations.RemoveField(
            model_name='distribution',
            name='pid',
        ),
        migrations.AlterField(
            model_name='distribution',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]