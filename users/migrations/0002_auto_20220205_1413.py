# Generated by Django 3.2 on 2022-02-05 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='last_name',
        ),
        migrations.AddField(
            model_name='user',
            name='second_name',
            field=models.CharField(default='empty', max_length=150, verbose_name='Second name'),
            preserve_default=False,
        ),
    ]
