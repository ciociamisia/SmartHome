# Generated by Django 3.1.2 on 2020-12-12 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_motion_detector'),
    ]

    operations = [
        migrations.AddField(
            model_name='motion_detector',
            name='send',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]