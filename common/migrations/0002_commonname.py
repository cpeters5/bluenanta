# Generated by Django 3.2.15 on 2024-05-07 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommonName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('common_name', models.CharField(blank=True, max_length=500, null=False)),
                ('application', models.CharField(choices=[('animalia', 'animalia'), ('aves', 'aves'), ('fungi', 'fungi'), ('other', 'other'), ('orchidaceae', 'orchidaceae')], default='', max_length=20)),
                ('level', models.CharField(choices=[('Family', 'Family'), ('Genus', 'Genus'), ('Accepted', 'Accepted')], default='', max_length=20)),
                ('taxon_id', models.CharField(blank=True, max_length=20, null=True)),
            ],
        ),
    ]
