# Generated by Django 3.1.2 on 2020-10-25 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_temp_and_hum_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='Login',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.TextField()),
                ('login', models.TextField()),
                ('password', models.TextField()),
            ],
        ),
    ]
