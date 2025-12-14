from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import User, Venue, Space, Amenity, SpaceAmenity
from .utils.calling_codes import CALLING_CODES
from .utils.phone_format import format_phone_number, deformat_phone_number
from django.db import transaction


class UserSerializer(serializers.ModelSerializer):
    """
    Handles phone number normalization and country-based formatting.
    """
    # Country code from client (used to reconstruct E.164 phone number).
    country = serializers.ChoiceField(
        choices=list(CALLING_CODES.keys()), write_only=True)

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
                raise serializers.ValidationError(
                    {"phone": "Country and phone are required."})

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
        # Country data only use to build final phone number.
        validated_data.pop("country", None)
        return super().create(validated_data)

class VenueSerializer(serializers.ModelSerializer):
    """
    Show summarize information about Venue free space.
    """
    summary = serializers.SerializerMethodField()
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

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
        """Count How many spaces host published for the Renter."""
        spaces = obj.spaces.all()
        published = spaces.filter(is_published=True).count()
        total = spaces.count()

        return {
            "total_spaces": total,
            "published_spaces": published,
            "unpublished_spaces": total - published
        }

class SpaceSerializer(serializers.ModelSerializer):
    """
    Enforces venue rules when creating or updating spaces.
    """
    venue = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Space
        fields = [
            "id",
            "venue",
            "name",
            "description",
            "space_width",
            "space_height",
            "price_per_day",
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


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["name", "email", "phone", "country", "password", "is_host"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if password is None:
            raise serializers.ValidationError({"password": "Required."})
        validated_data["password_hash"] = make_password(password)
        return super().create(validated_data)


class VenueWithSpacesSerializer(serializers.Serializer):
    venue = VenueSerializer()
    spaces = serializers.ListField()

    def create(self, validated_data):
        request = self.context["request"]
        venue_data = validated_data["venue"]
        raw_spaces = self.initial_data.get("spaces", [])

        with transaction.atomic():
            venue = Venue.objects.create(
                owner=request.user,
                **venue_data
            )

            created_spaces = []

            for raw in raw_spaces:
                have_amenity = raw.pop("have_amenity", False)
                amenities = raw.pop("amenities", [])

                space_serializer = SpaceSerializer(data=raw)
                space_serializer.is_valid(raise_exception=True)

                space = space_serializer.save(
                    venue=venue,
                    amenities_enabled=have_amenity,
                )

                if have_amenity:
                    for name in amenities:
                        amenity, _ = Amenity.objects.get_or_create(name=name)
                        SpaceAmenity.objects.create(
                            space=space,
                            amenity=amenity,
                            amount=1,
                        )

                created_spaces.append(space)

        return {
            "venue": venue,
            "spaces": created_spaces,
        }
