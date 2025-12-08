from django.db import models
from django.core.validators import RegexValidator


class Item(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Validation for the phone data (already undirect constraint max_length to be 10-16)
phone_format = RegexValidator(
    regex=r'^\+?[1-9]\d{9,14}$', #Rule : last result need to only be in format +6613920139
    message="Incorrect phone number"
)

#DEVNOTE: Create User Table, Primary Key: auto create django ID & email + phone
class User(models.Model):
    name = models.CharField(max_length=255, null=False) #All 4 data need to exist
    email = models.EmailField(unique=True, null=False) # Need to be able to Contact
    phone = models.CharField(max_length=25, validators=[phone_format], unique=True, null=False)
    password_hash = models.CharField(max_length=255, null=False)
    is_host = models.BooleanField(default=False)
    is_renter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #DEVNOTE: function str is use for check info when you print in will print out these message
    def __str__(self):
        return (f"name: {self.name}, email: {self.email} "
                f"is host:{self.is_host} and is renter: {self.is_renter}")



