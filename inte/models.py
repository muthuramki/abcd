from django.db import models
 
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    organization = models.CharField(max_length=100)
    password = models.CharField(max_length=100)  # You might want to use Django's built-in password management later
 
    def __str__(self):
        return self.name