# Generated by Django 3.2.15 on 2023-07-16 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_alter_sponsor_country_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='profile_pic',
        ),
        migrations.AddField(
            model_name='profile',
            name='profile_pic_path',
            field=models.ImageField(blank=True, null=True, upload_to='images/user_profile/'),
        ),
    ]