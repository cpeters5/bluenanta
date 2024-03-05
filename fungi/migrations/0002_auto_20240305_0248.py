# Generated by Django 3.2.15 on 2024-03-05 02:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fungi', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            'ALTER TABLE fungi_accepted ADD FULLTEXT(binomial, common_name)',
            reverse_sql='ALTER TABLE fungi_accepted DROP INDEX accepted_content_fulltext'
        ),
    ]
