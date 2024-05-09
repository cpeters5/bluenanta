# Generated by Django 3.2.15 on 2024-05-09 03:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orchidaceae', '0007_auto_20240506_1839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accepted',
            name='gen',
            field=models.ForeignKey(blank=True, db_column='gen', null=True, on_delete=django.db.models.deletion.CASCADE, to='orchidaceae.genus'),
        ),
        migrations.AlterField(
            model_name='accepted',
            name='pid',
            field=models.OneToOneField(db_column='pid', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='accepted', serialize=False, to='orchidaceae.species'),
        ),
        migrations.AlterField(
            model_name='gensyn',
            name='acc',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Gensyn', to='orchidaceae.genus', verbose_name='genus'),
        ),
        migrations.AlterField(
            model_name='genusrelation',
            name='gen',
            field=models.OneToOneField(db_column='gen', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='genusrelation', serialize=False, to='orchidaceae.genus'),
        ),
        migrations.AlterField(
            model_name='hybrid',
            name='pid',
            field=models.OneToOneField(db_column='pid', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='hybrid', serialize=False, to='orchidaceae.species'),
        ),
        migrations.AlterField(
            model_name='synonym',
            name='spid',
            field=models.OneToOneField(db_column='spid', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='synonym', serialize=False, to='orchidaceae.species'),
        ),
    ]