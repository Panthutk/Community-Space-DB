from django.contrib import admin
from .models import (
    User,
    Venue,
    Space,
    Amenity,
    SpaceAmenity,
    Booking,
    Review,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "name", "email", "phone",
        "created_at", "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "email", "phone")
    ordering = ("-created_at",)


class SpaceInline(admin.TabularInline):
    model = Space
    extra = 0
    fields = ("name", "price_per_hour", "is_published")
    show_change_link = True


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "name", "owner", "venue_type",
        "city", "province", "country",
        "created_at", "updated_at",
    )
    list_filter = ("venue_type", "city", "province", "country", "created_at")
    search_fields = ("name", "owner__name", "address", "city", "province", "country", "description")
    ordering = ("-created_at",)
    inlines = [SpaceInline]


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")

    # If your model fields are `width`/`height` instead of `space_width`/`space_height`,
    # change these accordingly.
    list_display = (
        "id", "venue", "name",
        "space_width", "space_height",  # or: "width", "height"
        "price_per_hour", "is_published", "amenities_enabled",
        "created_at", "updated_at",
    )
    list_filter = ("is_published", "venue", "created_at", "updated_at")
    search_fields = ("name", "description", "venue__name")
    ordering = ("-created_at",)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(SpaceAmenity)
class SpaceAmenityAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = ("id", "space", "amenity", "amount", "created_at")
    list_filter = ("amenity", "space__venue")
    search_fields = ("space__name", "amenity__name", "space__venue__name")
    ordering = ("-created_at",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "space", "renter",
        "start_datetime", "end_datetime",
        "status", "total_price", "currency", "payment_status",
        "created_at",
    )
    list_filter = ("status", "payment_status", "currency", "space__venue")
    search_fields = ("space__name", "space__venue__name", "renter__name", "renter__email")
    ordering = ("-created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = ("id", "venue", "reviewer", "rating", "created_at")
    list_filter = ("rating", "venue")
    search_fields = ("venue__name", "reviewer__name", "comment")
    ordering = ("-created_at",)
