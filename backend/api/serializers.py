from rest_framework import serializers
from .models import User, Venue, Space
from .utils.calling_codes import CALLING_CODES
from .utils.phone_format import format_phone_number, deformat_phone_number


class UserSerializer(serializers.ModelSerializer):
    """
    Handles phone number normalization and country-based formatting.
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
            "created_at", "updated_at"
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


class VenueSerializer(serializers.ModelSerializer):
    """
    Show summarize information about Venue free space.
    """
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = [
            "id",
            "name",
            "owner",
            "venue_type",
            "address",
            "city",
            "province",
            "country",
            "google_map_link",
            "description",
            "summary",
            "created_at", "updated_at"
        ]

    def get_summary(self, obj):
        """
        Count how many Space are still open for rent in current Venue.
        """
        spaces = obj.spaces
        return {
            "total_spaces": spaces.count(),
            "published_spaces": spaces.filter(is_published=True).count(),
            "unpublished_spaces": spaces["total_spaces"] - spaces["published_spaces"]
        }


class SpaceSerializer(serializers.ModelSerializer):
    """
    Enforces venue rules when creating or updating spaces.
    """

    class Meta:
        model = Space
        fields = [
            "id",
            "venue",
            "name",
            "description",
            "space_width",
            "space_height",
            "booking_step_minute",
            "minimum_booking_minute",
            "price_per_hour",
            "cleaning_fee",
            "is_published",
            "amenities_enabled",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """
        Ensures WHOLE-type venues do not contain more than one space.
        """
        venue = data.get("venue", getattr(self.instance, "venue", None))

        # Return early.
        if venue is None:
            return data

        if venue.venue_type == "WHOLE":
            qs = venue.spaces
            # If Space already exist in the Venue (When update).
            if self.instance:
                qs = qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError({
                    "venue": "This venue allows only one space."
                })

        return data
