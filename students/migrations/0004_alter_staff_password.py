# Generated by Django 4.2.5 on 2024-10-12 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_remove_staff_user_alter_staff_password'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staff',
            name='password',
            field=models.CharField(default='pbkdf2_sha256$600000$iA6CwFCv6Jf6uhE1SCKome$HYGywIBnozwF6BZUAmCBAwarNFn7S5LKWeVnNb7DvJs=', max_length=128),
        ),
    ]
