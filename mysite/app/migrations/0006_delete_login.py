# Generated by Django 3.1.2 on 2020-10-25 17:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_login'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Login',
        ),
    ]