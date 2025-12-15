from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q, Avg
from rest_framework import serializers
from datetime import timedelta, datetime
import pytz

from .models import (
    User,
    Venue,
    Space,
    Amenity,
    SpaceAmenity,
    Booking,
    Review,
)
from .utils.calling_codes import CALLING_CODES
from .utils.phone_format import format_phone_number, deformat_phone_number


# =========================================================
# USER
# =========================================================

class UserSerializer(serializers.ModelSerializer):
    country = serializers.ChoiceField(
        choices=list(CALLING_CODES.keys()), write_only=True
    )
    phone = serializers.CharField(write_only=True)
    password_hash = serializers.CharField(write_only=True)

    full_phone = serializers.CharField(source="phone", read_only=True)

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password_hash",
            "country",
            "phone",
            "full_phone",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        instance = getattr(self, "instance", None)

        if instance is None:
            country = data.get("country")
            raw = data.get("phone")

            if not country or not raw:
                raise serializers.ValidationError(
                    {"phone": "Country and phone are required."}
                )

            data["phone"] = format_phone_number(raw, country)
            return data

        if "phone" in data or "country" in data:
            original = deformat_phone_number(instance)
            country = data.get("country") or original["country"]
            raw = data.get("phone") or original["phone"]
            data["phone"] = format_phone_number(raw, country)

        return data

    def create(self, validated_data):
        validated_data.pop("country", None)
        return super().create(validated_data)


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "created_at"]


# =========================================================
# VENUE
# =========================================================

class VenueSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    summary = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

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
            "description",
            "summary",
            "average_rating",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        required_fields = [
            "name",
            "venue_type",
            "address",
            "city",
            "province",
            "country",
        ]

        errors = {}
        for field in required_fields:
            if not data.get(field):
                errors[field] = "This field is required."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def get_summary(self, obj):
        spaces = obj.spaces.all()
        published = spaces.filter(is_published=True).count()
        total = spaces.count()
        return {
            "total_spaces": total,
            "published_spaces": published,
            "unpublished_spaces": total - published,
        }

    def get_average_rating(self, obj):
        """Return the average rating for this venue or None if no reviews."""
        from .models import Review
        result = Review.objects.filter(
            booking__space__venue=obj
        ).aggregate(avg=Avg('rating'))['avg']
        # Round to one decimal place if not None
        return round(result, 1) if result is not None else None


# =========================================================
# SPACE
# =========================================================

class SpaceSerializer(serializers.ModelSerializer):
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
        errors = {}

        # ---------- REQUIRED ----------
        if not data.get("name"):
            errors["name"] = "Space name is required."

        # ---------- NUMERIC RULES ----------
        space_width = data.get("space_width")
        space_height = data.get("space_height")
        price = data.get("price_per_day")
        cleaning = data.get("cleaning_fee")

        if space_width is not None and space_width <= 0.01:
            errors["space_width"] = "Space width must be greater than 0.01."

        if space_height is not None and space_height <= 0.01:
            errors["space_height"] = "Space height must be greater than 0.01."

        if price is not None and price <= 0:
            errors["price_per_day"] = "Price per day must be greater than 0.00."

        # cleaning_fee CAN be 0.00
        if cleaning is not None and cleaning < 0:
            errors["cleaning_fee"] = "Cleaning fee cannot be negative."

        # ---------- WHOLE VENUE RULE ----------
        venue = data.get("venue", getattr(self.instance, "venue", None))
        if venue and venue.venue_type == "WHOLE":
            qs = venue.spaces
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                errors["venue"] = "WHOLE venue can only have one space."

        if errors:
            raise serializers.ValidationError(errors)

        return data


# =========================================================
# AUTH
# =========================================================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    country = serializers.ChoiceField(
        choices=list(CALLING_CODES.keys()), write_only=True
    )
    phone = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["name", "email", "phone", "country", "password"]

    def validate(self, data):
        raw_phone = data.get("phone")
        country = data.get("country")

        if not raw_phone or not country:
            raise serializers.ValidationError("Phone and country are required")

        try:
            data["phone"] = format_phone_number(raw_phone, country)
        except ValueError as e:
            raise serializers.ValidationError({"phone": str(e)})

        return data

    def create(self, validated_data):
        validated_data.pop("country")
        password = validated_data.pop("password")
        validated_data["password_hash"] = make_password(password)
        return User.objects.create(**validated_data)

# =========================================================
# CREATE VENUE + SPACES
# =========================================================


class VenueCreateWithSpacesSerializer(serializers.Serializer):
    venue = VenueSerializer()
    spaces = serializers.ListField()

    def create(self, validated_data):
        request = self.context["request"]
        venue_data = validated_data["venue"]
        spaces_data = self.initial_data.get("spaces", [])

        try:
            with transaction.atomic():
                venue_serializer = VenueSerializer(data=venue_data)
                venue_serializer.is_valid(raise_exception=True)

                venue = venue_serializer.save(owner=request.user)

                created_spaces = []

                for raw in spaces_data:
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
                            amenity, _ = Amenity.objects.get_or_create(
                                name=name)
                            SpaceAmenity.objects.create(
                                space=space,
                                amenity=amenity,
                                amount=1
                            )

                    created_spaces.append(space)

                return {
                    "venue": venue,
                    "spaces": created_spaces,
                }

        except IntegrityError:
            # Try to revive a soft-deleted venue
            archived = Venue.objects.filter(
                owner=request.user,
                name=venue_data.get("name"),
                is_active=False,
            ).first()

            if archived:
                archived.is_active = True
                for field, value in venue_data.items():
                    setattr(archived, field, value)
                archived.save()

                return {
                    "venue": archived,
                    "spaces": [],
                }

            raise serializers.ValidationError(
                {"venue": "You already have an active venue with this name."}
            )


# =========================================================
# UPDATE VENUE + SPACES
# =========================================================

class VenueUpdateWithSpacesSerializer(serializers.Serializer):
    venue = VenueSerializer()
    spaces = serializers.ListField()

    def update(self, instance, validated_data):
        request = self.context["request"]

        if instance.owner != request.user:
            raise PermissionDenied("You can only edit your own venue.")

        venue_data = validated_data["venue"]
        spaces_data = self.initial_data.get("spaces", [])

        with transaction.atomic():
            for field, value in venue_data.items():
                setattr(instance, field, value)
            instance.save()

            existing_spaces = {s.id: s for s in instance.spaces.all()}
            received_ids = set()

            for raw in spaces_data:
                space_id = raw.get("id")
                have_amenity = raw.pop("have_amenity", False)
                amenities = raw.pop("amenities", [])

                if space_id and space_id in existing_spaces:
                    space = existing_spaces[space_id]

                    space_serializer = SpaceSerializer(
                        instance=space,
                        data=raw,
                        partial=True
                    )
                    space_serializer.is_valid(raise_exception=True)

                    space = space_serializer.save(
                        amenities_enabled=have_amenity
                    )

                else:
                    space_serializer = SpaceSerializer(data=raw)
                    space_serializer.is_valid(raise_exception=True)

                    space = space_serializer.save(
                        venue=instance,
                        amenities_enabled=have_amenity,
                    )

                received_ids.add(space.id)

                SpaceAmenity.objects.filter(space=space).delete()
                if have_amenity:
                    for name in amenities:
                        amenity, _ = Amenity.objects.get_or_create(name=name)
                        SpaceAmenity.objects.create(
                            space=space,
                            amenity=amenity
                        )

            for sid, space in existing_spaces.items():
                if sid not in received_ids:
                    space.delete()

        return instance


# =========================================================
# BOOKING
# =========================================================

class BookingSerializer(serializers.ModelSerializer):
    StartDate = serializers.DateField(write_only=True)
    EndDate = serializers.DateField(write_only=True)
    totalCost = serializers.DecimalField(
        max_digits=10, decimal_places=2, write_only=True
    )

    class Meta:
        model = Booking
        fields = ["StartDate", "EndDate", "totalCost"]

    def validate(self, data):
        space_id = self.context["space_id"]
        start_date = data["StartDate"]
        end_date = data["EndDate"]

        if start_date > end_date:
            raise serializers.ValidationError(
                {"dates": "Start date must be before end date."}
            )

        tz = pytz.timezone("Asia/Bangkok")
        today = datetime.now(tz).date()
        tomorrow = today + timedelta(days=1)
        max_date = tomorrow + timedelta(days=6)

        if start_date < tomorrow or end_date > max_date:
            raise serializers.ValidationError(
                {"dates": "Booking must be between tomorrow and 7 days ahead."}
            )

        start_dt = tz.localize(datetime.combine(
            start_date, datetime.min.time()))
        end_dt = tz.localize(datetime.combine(end_date, datetime.max.time()))

        overlap = Booking.objects.filter(
            space_id=space_id,
            status__in=["ACCEPTED", "PENDING"],
        ).filter(
            Q(start_datetime__lt=end_dt) &
            Q(end_datetime__gt=start_dt)
        )

        if overlap.exists():
            raise serializers.ValidationError(
                {"dates": "This date range is already booked."}
            )

        return data


# =========================================================
# REVIEW
# =========================================================

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the Review model in 3rd normal form.  The reviewer and
    venue are derived through the associated booking instead of being stored
    directly on the review itself.  These derived fields are read‑only.
    """
    booking = serializers.PrimaryKeyRelatedField(read_only=True)
    venue = serializers.SerializerMethodField(read_only=True)
    reviewer = serializers.SerializerMethodField(read_only=True)

    reviewer_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "booking",
            "venue",
            "reviewer",
            "reviewer_name",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "booking",
            "venue",
            "reviewer",
            "reviewer_name",
            "created_at",
        ]

    def get_venue(self, obj):
        try:
            return obj.booking.space.venue.id
        except Exception:
            return None

    def get_reviewer(self, obj):
        try:
            return obj.booking.renter.id
        except Exception:
            return None

    def get_reviewer_name(self, obj):
        """Return the name of the reviewer (renter) derived from the booking."""
        try:
            return obj.booking.renter.name
        except Exception:
            return None
