from rest_framework import serializers
from .models import Item, User, Location, Venue, Space
from .utils.calling_codes import CALLING_CODES
from .utils.phone_utils import format_phone_number


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    #DEVNOTE: for the data that we not exact contain inside database as same as user so we need to add more logic
    #Data get from frontend before merge and format
    country = serializers.ChoiceField(choices=list(CALLING_CODES.keys()), write_only=True)
    phone = serializers.CharField(write_only=True) #NOTE: although we want only digit we still contain in string because the first number can be 0
    #Formatted data ready to send to backend
    full_phone = serializers.CharField(source='phone', read_only=True)

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password_hash",
            "is_host",
            "is_renter",
            # incoming data
            "country",
            "phone",
            # outgoing data
            "full_phone",
        ]

    def validate(self, data):
        instance = getattr(self, 'instance', None)

        # CREATE or updating phone
        if "phone" in data or instance is None:
            country = data.get("country")
            raw_phone = data.get("phone")

            if raw_phone is None or country is None:
                raise serializers.ValidationError({
                    "phone": "Both country and phone are required when updating the phone number."
                })

            try:
                final_phone = format_phone_number(raw_phone, country)
            except ValueError as e:
                raise serializers.ValidationError({"phone": str(e)})

            data["phone"] = final_phone

        return data


    def create(self, validated_data):
        # When call create remove "country" data out
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
            "id", "name", "description", "venue_type", "location",
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
