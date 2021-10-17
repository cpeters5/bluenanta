# Generated by Django 3.2.2 on 2021-07-04 08:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_taxonomy1'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taxonomy1',
            options={'ordering': ['taxon', 'parent_name']},
        ),
        migrations.AlterUniqueTogether(
            name='taxonomy1',
            unique_together={('taxon', 'parent_name')},
        ),
    ]