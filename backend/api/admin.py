from django.contrib import admin
from .models import Item, User


admin.site.register(Item)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)  # show ID on detail page (read-only)
    # didn't Show password
    list_display = (
        "id", "name", "email", "phone", "is_host", "is_renter", "created_at",
    )
    list_filter = ("is_host", "is_renter", "created_at")
    search_fields = ("name", "email", "phone")
