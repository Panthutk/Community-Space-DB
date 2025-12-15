from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import User, Venue, Space, Amenity, SpaceAmenity, Booking
from .utils.calling_codes import CALLING_CODES
from .utils.phone_format import format_phone_number, deformat_phone_number
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date, datetime
from django.db.models import Q
import pytz


class UserSerializer(serializers.ModelSerializer):
    """
    Manage CREATE and MODIFY operations.
    Handles phone number normalization and country-based formatting.
    """
    country = serializers.ChoiceField(
        choices=list(CALLING_CODES.keys()), write_only=True)
    phone = serializers.CharField(write_only=True)

    full_phone = serializers.CharField(source='phone', read_only=True)
    password_hash = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password_hash",

            "country",
            "phone",

            "full_phone",
            "created_at", "updated_at"
        ]

    def validate(self, data):
        """
        Combine raw phone + country input into final phone number format E.164.
        Applies different logic for create & update operations.
        """
        instance = getattr(self, 'instance', None)

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
        validated_data.pop("country", None)
        return super().create(validated_data)

class UserReadSerializer(serializers.ModelSerializer):
    """
    Manage GET operation.
    """
    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "created_at"]

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

        if venue is None:
            return data

        if venue.venue_type == "WHOLE":
            qs = venue.spaces
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


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new booking.
    Handles date validation and overlap checking using Thailand timezone (Asia/Bangkok).
    The space ID is assumed to be passed via context/URL.
    """
    StartDate = serializers.DateField(write_only=True)
    EndDate = serializers.DateField(write_only=True)
    totalCost = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    
    class Meta:
        model = Booking
        fields = ["StartDate", "EndDate", "totalCost"]
        read_only_fields = ["space", "renter", "total_price", "status", "payment_status"]

    def validate(self, data):
        """
        Performs date-specific validation using Thailand timezone (Asia/Bangkok):
        1. Date range validity (Start before End).
        2. Booking window (Tomorrow to 7 days ahead, based on Bangkok time).
        3. Overlap check with existing bookings.
        """
        request = self.context.get("request")
        space_id = self.context.get("space_id")
        
        start_date = data["StartDate"]
        end_date = data["EndDate"]
        
        if start_date > end_date:
            raise serializers.ValidationError({"dates": "Start date must be before or equal to the end date."})

        bangkok_tz = pytz.timezone('Asia/Bangkok')
        bangkok_now = datetime.now(bangkok_tz)
        today = bangkok_now.date()
        
        tomorrow = today + timedelta(days=1)
        max_book_date = tomorrow + timedelta(days=6)
        
        print(f"Validation: today={today}, tomorrow={tomorrow}, max={max_book_date}")
        print(f"User wants to book: {start_date} to {end_date}")
        
        if start_date < tomorrow:
            raise serializers.ValidationError(
                {"dates": f"Booking must start on or after {tomorrow.isoformat()} (tomorrow in Bangkok time)."}
            )
            
        if end_date > max_book_date:
            raise serializers.ValidationError(
                {"dates": f"Booking cannot exceed {max_book_date.isoformat()} (7 days in advance from tomorrow)."}
            )

        start_dt_bangkok = bangkok_tz.localize(datetime.combine(start_date, datetime.min.time()))
        end_dt_bangkok = bangkok_tz.localize(datetime.combine(end_date, datetime.max.time()))
        
        overlapping_bookings = Booking.objects.filter(
            space_id=space_id,
            status__in=["ACCEPTED", "PENDING"],
            payment_status__in=["PAID", "UNPAID"],
        ).filter(
            Q(start_datetime__lt=end_dt_bangkok) & Q(end_datetime__gt=start_dt_bangkok)
        )
        
        if overlapping_bookings.exists():
            print(f"Found overlapping bookings: {overlapping_bookings}")
            raise serializers.ValidationError(
                {"dates": "The selected date range is already reserved."}
            )

        print(f"Validation passed!")
        return data