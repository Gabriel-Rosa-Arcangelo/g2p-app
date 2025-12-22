from django.db import models
from django.contrib.auth.models import User
#from django.utils.translation import gettext as _


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=100)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp'] 
        
class Sample(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fasta_file_name = models.CharField(max_length=255)
    fasta_file_size = models.PositiveIntegerField()
    pdf_file_name = models.CharField(max_length=255)
    csv_file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    zipcode = models.CharField(max_length=20)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=50)
    department = models.CharField(max_length=255)
    jobtitle = models.CharField(max_length=255)