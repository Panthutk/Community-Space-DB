from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
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
    phone = models.CharField(unique=True, max_length=25,validators=[format_rule])

    # Stores the hashed password.
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
    google_map_link = models.URLField(max_length=500, validators=[
                                      validate_google_maps_url], blank=True)

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

    space_width = models.DecimalField(default=Decimal("5.00"), max_digits=10, decimal_places=2,
                                      validators=[MinValueValidator(Decimal("0.01"))])
    space_height = models.DecimalField(default=Decimal("5.00"), max_digits=10, decimal_places=2,
                                       validators=[MinValueValidator(Decimal("0.01"))])

    # Data about money.
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"),
                                         validators=[MinValueValidator(Decimal("0.00"))])
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                       validators=[MinValueValidator(Decimal("0.00"))])

    # Host open this Space or not (doesn't tell about do other people rent or not)
    is_published = models.BooleanField(default=False)

    # If False Host can't add amenity.
    amenities_enabled = models.BooleanField(default=False)

    # Specific detail for that Space/Grid. EXAMPLE: near toilet.
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.venue.name})"
    

class Amenity(BaseModel):
    """
    Generic amenity that can be attached to one or more spaces.
    Example: Wi-Fi, Parking, Projector.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SpaceAmenity(BaseModel):
    """
    Join model between Space and Amenity, with optional `amount`.
    Mirrors `space_amenities` table in DBML.
    """
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="space_amenities",
    )
    amenity = models.ForeignKey(
        Amenity,
        on_delete=models.CASCADE,
        related_name="space_amenities",
    )
    amount = models.PositiveIntegerField(
        default=1,
        help_text="Quantity of this amenity in the space (e.g., 2 projectors).",
    )

    class Meta:
        unique_together = ("space", "amenity")

    def __str__(self):
        return f"{self.amenity.name} x{self.amount} @ {self.space.name}"


class Booking(BaseModel):
    """
    Booking made by a renter for a specific space and time range.
    """
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("UNPAID", "Unpaid"),
        ("PAID", "Paid"),
    ]

    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    renter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    # Keep currency simple for now; matches DBML `default 'THB'`
    currency = models.CharField(
        max_length=10,
        default="THB",
    )

    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS_CHOICES,
        default="UNPAID",
    )

    class Meta:
        indexes = [
            models.Index(fields=["space", "start_datetime", "end_datetime"]),
            models.Index(fields=["renter"]),
        ]

    def __str__(self):
        return f"Booking #{self.id} - {self.space.name} by {self.renter.name}"


class Review(BaseModel):
    """
    Review left by a renter about a venue, based on a booking.
    """
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="review",
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
        help_text="Rating from 1 to 5.",
    )
    comment = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["venue"]),
            models.Index(fields=["reviewer"]),
        ]

    def __str__(self):
        return f"Review {self.rating}/5 for {self.venue.name} by {self.reviewer.name}"
