# Generated by Django 3.2.15 on 2023-06-18 11:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0003_delete_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.CharField(max_length=200)),
                ('url', models.URLField(null=True)),
                ('media', models.CharField(blank=True, max_length=200, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('city', models.ForeignKey(db_column='city', default='', on_delete=django.db.models.deletion.DO_NOTHING, related_name='artcity', to='gallery.city')),
            ],
        ),
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('genre', models.CharField(db_column='genre', default='', max_length=50, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Medium',
            fields=[
                ('medium', models.CharField(db_column='family', default='', max_length=50, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Artwork',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('date', models.DateField(null=True)),
                ('description', models.CharField(blank=True, max_length=500, null=True)),
                ('image_file', models.ImageField(upload_to='gallery')),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('artist', models.ForeignKey(db_column='artist', default='', on_delete=django.db.models.deletion.DO_NOTHING, related_name='artistwork', to='gallery.artist')),
                ('genre', models.ForeignKey(db_column='genre', default='', on_delete=django.db.models.deletion.DO_NOTHING, related_name='artistgenre', to='gallery.genre')),
                ('medium', models.ForeignKey(db_column='medium', default='', on_delete=django.db.models.deletion.DO_NOTHING, related_name='artistmedium', to='gallery.medium')),
            ],
        ),
    ]
