# Generated by Django 4.2.5 on 2024-11-24 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0016_merge_20241107_1324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staff',
            name='password',
            field=models.CharField(default='pbkdf2_sha256$600000$h6tj4IIlHLALS5JWVlgxsJ$VjyfzMLwIk2M+cnCqWqNmu7Nzfks6sLO/D5tQwntek8=', max_length=128),
        ),
    ]
