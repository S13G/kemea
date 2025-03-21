# Generated by Django 4.2.5 on 2024-05-19 16:48

import apps.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('property', '0004_alter_property_reachable_phone_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromoteAdRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('location', models.CharField(max_length=255)),
                ('property_type', models.CharField(max_length=255)),
                ('surface', models.PositiveIntegerField(default=0)),
                ('rooms', models.PositiveIntegerField(default=0)),
                ('desired_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('email_address', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(max_length=255, validators=[apps.core.validators.validate_phone_number])),
                ('buy_or_rent', models.BooleanField(default=False)),
                ('sell', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
    ]
