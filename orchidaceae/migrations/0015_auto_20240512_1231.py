# Generated by Django 3.2.15 on 2024-05-12 12:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orchidaceae', '0014_auto_20240512_1208'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='synonym',
            name='gen',
        ),
        migrations.RemoveField(
            model_name='synonym',
            name='genus',
        ),
        migrations.RemoveField(
            model_name='synonym',
            name='is_hybrid',
        ),
        migrations.RemoveField(
            model_name='synonym',
            name='year',
        ),
    ]
