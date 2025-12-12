from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from .utils.phone_format import format_rule
from .utils.check_map_url import validate_google_maps_url


class BaseModel(models.Model):
    """
    Abstract base model that provides automatic timestamp fields.
    Other models inherit from this class to include `created_at` and `updated_at`.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(BaseModel):
    """
    Represents a platform user account.
    """
    # User display name.
    name = models.CharField(max_length=255)

    # This software didn't support log-in by oauth, email only act as User contact information.
    email = models.EmailField(unique=True)

    # Phone number stored in normalized E.164 format.
    phone = models.CharField(unique=True, max_length=25, validators=[format_rule])

    # Stores the hashed password.
    # TODO: Not implement hashed password translate yet, currently directly contain raw password is contain.
    password_hash = models.CharField(max_length=255)

    # If true user can create and manage venues.
    is_host = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} "


class Venue(BaseModel):
    """
    Represents a physical place or building that a host lists for rental.
    A venue contains one or more bookable spaces.
    """
    VENUE_TYPES = [
        ("WHOLE", "Whole Area"),
        ("GRID", "Grid-based"),
    ]

    # What User will see when listing. EXAMPLE: Building Name.
    name = models.CharField(max_length=255)

    # || ForeignKeys ||
    # When the owner is deleted, all their venues are deleted automatically.
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    venue_type = models.CharField(max_length=10, choices=VENUE_TYPES)

    # Address isn't Unique, 2 Venues can be in the same building.
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100)

    # Accept only google map link.
    google_map_link = models.URLField(max_length=500, validators=[validate_google_maps_url], blank=True)

    # Specific location internal information like located on the floor 3, section A.
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Venue: {self.name} (Owner: {self.owner.name})"


class Space(BaseModel):
    """
    Represents a bookable subdivision within a Venue for the Renter.
    """

    # || ForeignKey ||
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="spaces")

    # EXAMPLE: Boot A1, A2.
    name = models.CharField(max_length=255, blank=True)

    space_width = models.FloatField(default=5)
    space_height = models.FloatField(default=5)

    # Data about time.
    booking_step_minute = models.PositiveIntegerField(default=30)
    minimum_booking_minute = models.PositiveIntegerField(default=60)

    # Data about money.
    price_per_hour = models.DecimalField( max_digits=10, decimal_places=2, default=Decimal("0.00"),
                      validators=[MinValueValidator(Decimal("0.00"))])
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                    validators=[MinValueValidator(Decimal("0.00"))])

    # If True other Renter can't rent.
    is_published = models.BooleanField(default=False)

    # If False Host can't add amenity.
    amenities_enabled = models.BooleanField(default=False)

    # Specific detail for that Space/Grid. EXAMPLE: near toilet.
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.venue.name})"
