from django.contrib import admin
from .models import Item, User, Location, Venue, Space


admin.site.register(Item)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "name", "email", "phone", "is_host", "created_at", "updated_at",
    )
    list_filter = ("is_host", "created_at", "updated_at")
    search_fields = ("name", "email", "phone")

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "address", "city", "province", "country", "updated_at", "created_at", "updated_at",
    )

    list_filter = ("country", "province", "created_at", "updated_at")
    search_fields = ("address", "city", "province", "country")

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "name", "owner", "venue_type", "location", "created_at", "updated_at",
    )

    list_filter = ("venue_type", "created_at", "updated_at")
    search_fields = ("name", "owner__name", "location__address")

@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "created_at", "updated_at")
    list_display = (
        "id", "name", "venue", "price_per_hour", "is_published", "created_at", "updated_at",
    )

    list_filter = ("is_published", "venue", "created_at")
    search_fields = ("name", "description", "venue__name",)
