# Generated by Django 3.2.5 on 2021-12-19 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20201018_1242'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sponsor',
            fields=[
                ('sid', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(default='', max_length=100, unique=True)),
                ('author', models.CharField(default='', max_length=200)),
                ('sponsor_url', models.URLField(default='')),
                ('pitch', models.CharField(max_length=200, null=True)),
                ('status', models.CharField(max_length=20, null=True)),
                ('address', models.TextField(null=True)),
                ('country_code', models.CharField(blank=True, max_length=2, null=True)),
                ('phone', models.CharField(max_length=20, null=True)),
                ('image_file', models.CharField(max_length=100)),
                ('image_file_path', models.ImageField(upload_to='utils/images/sponsor')),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'ordering': ('title',),
            },
        ),
    ]
