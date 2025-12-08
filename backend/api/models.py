from django.db import models
from django.core.validators import RegexValidator


#Base for all tables
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


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
class User(BaseModel):
    name = models.CharField(max_length=255, null=False) #All 4 data need to exist
    email = models.EmailField(unique=True, null=False) # Need to be able to Contact
    phone = models.CharField(max_length=25, validators=[phone_format], unique=True, null=False)
    password_hash = models.CharField(max_length=255, null=False)
    is_host = models.BooleanField(default=False)
    is_renter = models.BooleanField(default=False)

    #DEVNOTE: function str is use for check info when you print in will print out these message
    def __str__(self):
        return (f"name: {self.name}, email: {self.email} "
                f"is host:{self.is_host} and is renter: {self.is_renter}")


class Location(BaseModel):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address}, {self.city}, {self.country}"


class Venue(BaseModel):
    VENUE_TYPES = [
        ("WHOLE", "Whole Area"),
        ("GRID", "Grid-based"),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE) #if owner delete all of their venue also got delete
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    venue_type = models.CharField(max_length=10, choices=VENUE_TYPES)

    def __str__(self):
        return f"Venue: {self.name} (Owner: {self.owner.name})"


class Space(BaseModel):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="spaces")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    area_width = models.FloatField(null=True, blank=True)
    area_height = models.FloatField(null=True, blank=True)

    booking_step_minute = models.PositiveIntegerField(default=30)
    minimum_booking_minute = models.PositiveIntegerField(default=60)

    price_per_hour = models.FloatField(default=0, null=False)
    cleaning_fee = models.FloatField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.venue.name})"
