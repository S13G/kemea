# Generated by Django 4.2.5 on 2024-05-04 07:17

import apps.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('floors', models.PositiveIntegerField(default=20)),
                ('ground_level', models.BooleanField(default=False)),
                ('street', models.CharField(max_length=255)),
                ('street_number', models.PositiveIntegerField(default=0)),
                ('area', models.CharField(max_length=255)),
                ('number_of_rooms', models.PositiveIntegerField(default=0)),
                ('surface_build', models.PositiveIntegerField(default=0)),
                ('total_surface', models.PositiveIntegerField(default=0)),
                ('price', models.PositiveIntegerField(default=0)),
                ('discount', models.PositiveIntegerField(default=0)),
                ('entry_date', models.DateField(null=True)),
                ('number_of_balcony', models.PositiveIntegerField(default=1)),
                ('car_parking', models.PositiveIntegerField(default=1)),
                ('description', models.TextField()),
                ('matterport_view_link', models.CharField(max_length=255, null=True)),
                ('name_of_lister', models.CharField(max_length=255, null=True)),
                ('reachable_phone_number', models.CharField(max_length=255, null=True, validators=[apps.core.validators.validate_phone_number])),
                ('ad_status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=100)),
                ('terminate_ad', models.BooleanField(default=False)),
                ('buy', models.BooleanField(default=False)),
                ('ad_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ad_category', to='property.adcategory')),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PropertyFeature',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PropertyState',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PropertyType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PropertyMedia',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('media', models.FileField(upload_to='property_media')),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='property_media', to='property.property')),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='property',
            name='features',
            field=models.ManyToManyField(blank=True, related_name='property_features', to='property.propertyfeature'),
        ),
        migrations.AddField(
            model_name='property',
            name='lister',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='property_lister', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='property',
            name='property_state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='property_state', to='property.propertystate'),
        ),
        migrations.AddField(
            model_name='property',
            name='property_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='property_type', to='property.propertytype'),
        ),
    ]
