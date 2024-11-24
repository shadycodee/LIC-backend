from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class Student(models.Model):
    STATUS_CHOICES = [
        ('Student', 'Student'),
        ('Alumnus', 'Alumnus'),
    ]

    studentID = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{2}-\d{4}-\d{3}$',
                message='Student ID must be in the format XX-XXXX-XXX',
                code='invalid_studentID'
            )
        ]
    )
    name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    time_left = models.PositiveIntegerField()
    password = models.CharField(max_length=128)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='Student'
    )
    is_logged_in = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

class Transaction(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reference_number = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)  # Add image field
    amount = models.IntegerField(null=True, blank=True)
    year = models.CharField(max_length=10, blank=True)
    semester_name = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        # Fetch the single Semester record to set year and semester_name
        semester = Semester.objects.first()
        if semester:
            self.year = semester.year
            self.semester_name = semester.semester_name
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Transaction {self.reference_number} for {self.student.name}"

#Staff
class Staff(models.Model):
    username = models.CharField(max_length=15, unique=True) 
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=128, default=make_password('licstaffmem')) 

    def __str__(self):
        return self.name
    
    
class Session(models.Model):
    parent = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sessions_as_parent', to_field='studentID')
    course = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)
    loginTime = models.TimeField(auto_now_add=True)
    logoutTime = models.TimeField(null=True, blank=True)
    consumedTime = models.IntegerField(null=True, blank=True)
    year = models.CharField(max_length=10, blank=True)
    semester_name = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        # Fetch the single Semester record to set year and semester_name
        semester = Semester.objects.first()
        if semester:
            self.year = semester.year
            self.semester_name = semester.semester_name
        super().save(*args, **kwargs)
        
    def __str__(self):
        return str(self.parent)
    
class Semester(models.Model):
    year = models.CharField(max_length=10)  
    semester_name = models.CharField(max_length=20)  
    
    def __str__(self):
        return f"{self.year} - {self.semester_name}"

    

class StaffActivityLog(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.staff.name} - {self.action} on {self.timestamp}"
    

class ActivityLog(models.Model):
    username = models.CharField(max_length=255)
    action = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username} - {self.action} at {self.timestamp}"
    

def log_staff_activity(staff, action):
    StaffActivityLog.objects.create(staff=staff, action=action)
