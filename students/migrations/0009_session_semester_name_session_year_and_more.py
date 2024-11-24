# Generated by Django 4.2.5 on 2024-10-26 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0008_semester_alter_staff_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='semester_name',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='session',
            name='year',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='staff',
            name='password',
            field=models.CharField(default='pbkdf2_sha256$600000$mS5mA38sM47GVe9cdVqfK4$lIbxnPr07VLt7UuabZcXDyuaT3VKRiKmMpAr8+RY34I=', max_length=128),
        ),
    ]
