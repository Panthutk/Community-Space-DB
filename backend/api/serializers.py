from rest_framework import serializers
from .models import Item, User, Location, Venue, Space
from .utils.calling_codes import CALLING_CODES
from .utils.phone_format import format_phone_number, deformat_phone_number


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    """
    Handles user input/output transformation,
    including phone number normalization and country-based formatting.
    """
    # Country code from client (used to reconstruct E.164 phone number).
    country = serializers.ChoiceField(choices=list(CALLING_CODES.keys()), write_only=True)

    # Raw phone input from client.
    phone = serializers.CharField(write_only=True)

    # Normalized E.164 phone number returned to the client.
    full_phone = serializers.CharField(source='phone', read_only=True)

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password_hash",
            "is_host",
            # incoming data.
            "country",
            "phone",
            # outgoing data.
            "full_phone",
        ]

    def validate(self, data):
        """
        Combine raw phone + country input into final phone number format E.164.
        Applies different logic for create & update operations.
        """
        instance = getattr(self, 'instance', None)

        # Logic when Create the model instance.
        if instance is None:
            country = data.get("country")
            raw = data.get("phone")

            if not country or not raw:
                raise serializers.ValidationError({"phone": "Country and phone are required."})

            try:
                data["phone"] = format_phone_number(raw, country)
            except ValueError as e:
                raise serializers.ValidationError({"phone": str(e)})

            return data

        # Logic when Update the model instance.
        if "phone" in data or "country" in data:
            original = deformat_phone_number(instance)
            country = data.get("country") or original["country"]
            raw = data.get("phone") or original["phone"]

            try:
                data["phone"] = format_phone_number(raw, country)
            except ValueError as e:
                raise serializers.ValidationError({"phone": str(e)})

        return data

    def create(self, validated_data):
        #Country data only use to build final phone number.
        validated_data.pop("country", None)
        return super().create(validated_data)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "address",
            "city",
            "province",
            "country",
        ]

class VenueSerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = [
            "id", "name", "owner", "description", "venue_type", "location", "created_at", "updated_at",
            "summary"
        ]

    def get_summary(self, obj):
        spaces = obj.spaces.all()
        return {
            "total_spaces": spaces.count(),
            "published_spaces": spaces.filter(is_published=True).count(),
        }

class SpaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Space
        fields = [
            "id",
            "venue",
            "name",
            "description",
            "area_width",
            "area_height",
            "booking_step_minute",
            "minimum_booking_minute",
            "price_per_hour",
            "cleaning_fee",
            "is_published",
            "created_at",
            "updated_at"
        ]

    #Check how many space in the venue before create new one
    def validate(self, data):
        venue = data.get("venue")
        # CASE 1: Creating a new space
        if self.instance is None:
            if venue.venue_type == "WHOLE":
                # Count how many space in the venue
                existing_spaces = venue.spaces.count()
                if existing_spaces >= 1:
                    raise serializers.ValidationError({"venue": "This venue only allow one space."})
        # CASE 2: Update Existing space
        else:
            new_venue = data.get("venue", self.instance.venue)
            if new_venue.venue_type == "WHOLE":
                existing_spaces = new_venue.spaces.exclude(id=self.instance.id).count()
                if existing_spaces >= 1:
                    raise serializers.ValidationError({"venue": "This venue only allow one space."})

        return data
