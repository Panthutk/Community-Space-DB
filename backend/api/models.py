from django.db import models
from .utils.phone_format import format_rule


class BaseModel(models.Model):
    """
    Abstract base model that provides automatic timestamp fields.
    Other models inherit from this class to include `created_at` and `updated_at`
    without repeating the field definitions.
    """
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


class User(BaseModel):
    """
    Represents a platform user account.
    """
    # User display name.
    name = models.CharField(max_length=255, null=False)

    # This software didn't support log-in by oauth, email only act as User contact information.
    email = models.EmailField(unique=True, null=False)

    # Phone number stored in normalized E.164 format.
    phone = models.CharField(unique=True, max_length=25, validators=[format_rule], null=False)

    # Stores the hashed password.
    # TODO: Not implement hashed password translate yet, currently directly contain raw password is contain.
    password_hash = models.CharField(max_length=255, null=False)

    # If true user can create and manage venues.
    is_host = models.BooleanField(default=False, null=False)

    def __str__(self):
        return f"name: {self.name} email: {self.email} "


class Location(BaseModel):
    """
    Represents a physical address used to identify venue location.
    """

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
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(blank=True)
    venue_type = models.CharField(max_length=10, choices=VENUE_TYPES)

    def __str__(self):
        return f"Venue: {self.name} (Owner: {self.owner.name})"


class Space(BaseModel):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="spaces")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    area_width = models.FloatField(default=1, null=False)
    area_height = models.FloatField(default=1, null=False)

    booking_step_minute = models.PositiveIntegerField(default=30, null=False)
    minimum_booking_minute = models.PositiveIntegerField(default=60, null=False)

    price_per_hour = models.FloatField(default=0, null=False)
    cleaning_fee = models.FloatField(null=True, blank=True)
    is_published = models.BooleanField(default=False, null=False)

    def __str__(self):
        return f"{self.name} ({self.venue.name})"
