# Generated by Django 3.1.2 on 2020-12-16 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_motion_detector_send'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sockets',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('turn_on', models.BooleanField()),
            ],
        ),
    ]
