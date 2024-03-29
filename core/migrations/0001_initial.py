# Generated by Django 3.0.9 on 2021-01-05 23:47

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Continent',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('note', models.CharField(blank=True, max_length=500, null=True)),
                ('source', models.CharField(blank=True, max_length=10, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('dist_code', models.CharField(max_length=3, primary_key=True, serialize=False)),
                ('dist_num', models.IntegerField(blank=True, null=True)),
                ('country', models.CharField(blank=True, max_length=100, null=True)),
                ('region', models.CharField(blank=True, max_length=100, null=True)),
                ('orig_code', models.CharField(blank=True, max_length=100, null=True)),
                ('uncertainty', models.CharField(blank=True, max_length=10, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('Stripe', 'Stripe'), ('Paypal', 'Paypal')], default='Stripe', max_length=10)),
                ('source_id', models.CharField(blank=True, max_length=255, null=True)),
                ('donor_name', models.CharField(blank=True, max_length=255, null=True)),
                ('donor_display_name', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(choices=[('Accepted', 'Accepted'), ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled'), ('Refunded', 'Refunded'), ('Pending', 'Pending'), ('Unverified', 'Unverified')], default='Unverified', max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=5)),
                ('country_code', models.CharField(blank=True, max_length=2, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Family',
            fields=[
                ('family', models.CharField(db_column='family', default='', max_length=50, primary_key=True, serialize=False)),
                ('author', models.CharField(blank=True, max_length=200, null=True)),
                ('year', models.IntegerField(null=True)),
                ('description', models.TextField(null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'ordering': ['family'],
            },
        ),
        migrations.CreateModel(
            name='GeoLoc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geo_id', models.CharField(blank=True, max_length=10, null=True, unique=True)),
                ('name', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('note', models.CharField(blank=True, max_length=500, null=True)),
                ('source', models.CharField(blank=True, max_length=20, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('note', models.CharField(blank=True, max_length=500, null=True)),
                ('source', models.CharField(blank=True, max_length=10, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('continent', models.ForeignKey(blank=True, db_column='continent', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Continent')),
            ],
        ),
        migrations.CreateModel(
            name='Subfamily',
            fields=[
                ('subfamily', models.CharField(db_column='subfamily', default='', max_length=50, primary_key=True, serialize=False)),
                ('author', models.CharField(blank=True, max_length=200)),
                ('year', models.IntegerField(null=True)),
                ('description', models.TextField(null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('family', models.ForeignKey(db_column='family', default='', on_delete=django.db.models.deletion.DO_NOTHING, to='core.Family')),
            ],
            options={
                'ordering': ['subfamily'],
            },
        ),
        migrations.CreateModel(
            name='Tribe',
            fields=[
                ('tribe', models.CharField(db_column='tribe', default='', max_length=50, primary_key=True, serialize=False)),
                ('author', models.CharField(blank=True, max_length=200)),
                ('year', models.IntegerField(null=True)),
                ('status', models.CharField(max_length=50, null=True)),
                ('description', models.TextField(null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('subfamily', models.ForeignKey(db_column='subfamily', default='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Subfamily')),
            ],
            options={
                'ordering': ['tribe'],
            },
        ),
        migrations.CreateModel(
            name='Subtribe',
            fields=[
                ('subtribe', models.CharField(db_column='subtribe', default='', max_length=50, primary_key=True, serialize=False)),
                ('author', models.CharField(blank=True, max_length=200, null=True)),
                ('year', models.IntegerField(null=True)),
                ('status', models.CharField(max_length=50, null=True)),
                ('description', models.TextField(null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('subfamily', models.ForeignKey(db_column='subfamily', default='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Subfamily')),
                ('tribe', models.ForeignKey(db_column='tribe', default='', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Tribe')),
            ],
            options={
                'ordering': ['subtribe'],
            },
        ),
        migrations.CreateModel(
            name='SubRegion',
            fields=[
                ('code', models.CharField(max_length=10, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('note', models.CharField(blank=True, max_length=500, null=True)),
                ('source', models.CharField(blank=True, max_length=10, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('continent', models.ForeignKey(blank=True, db_column='continent', default=0, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Continent')),
                ('region', models.ForeignKey(blank=True, db_column='region', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Region')),
            ],
        ),
        migrations.CreateModel(
            name='LocalRegion',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('continent_name', models.CharField(max_length=100, null=True)),
                ('region_name', models.CharField(max_length=100, null=True)),
                ('name', models.CharField(max_length=100, null=True, unique=True)),
                ('code', models.CharField(blank=True, max_length=100, null=True)),
                ('note', models.CharField(blank=True, max_length=500, null=True)),
                ('source', models.CharField(blank=True, max_length=10, null=True)),
                ('subregion', models.CharField(blank=True, max_length=10, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('continent', models.ForeignKey(blank=True, db_column='continent', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Continent')),
                ('region', models.ForeignKey(blank=True, db_column='region', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Region')),
                ('subregion_code', models.ForeignKey(blank=True, db_column='subregion_code', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.SubRegion')),
            ],
        ),
        migrations.CreateModel(
            name='GeoLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('mptt_level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='core.GeoLocation')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
