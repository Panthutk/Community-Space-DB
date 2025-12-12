from django.contrib import admin
from .models import User, Venue, Space


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "name", "email", "phone", "is_host", "created_at", "updated_at",
    )
    list_filter = ("is_host", "created_at", "updated_at")
    search_fields = ("name", "email", "phone")
    ordering = ("-created_at",)


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = ("id", "name", "owner", "venue_type", "created_at", "updated_at")

    list_filter = ("venue_type", "created_at", "updated_at")
    search_fields = ("name", "owner__name", "address", "city", "province", "country", "description")
    ordering = ("-created_at",)


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "venue", "name", "space_width", "space_height",
        "price_per_hour", "is_published", "amenities_enabled",
        "created_at", "updated_at"
    )
    list_filter = ("is_published", "venue", "created_at", "updated_at")
    search_fields = ("name", "description", "venue__name")
    ordering = ("-created_at",)

