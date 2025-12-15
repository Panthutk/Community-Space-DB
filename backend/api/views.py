from rest_framework import viewsets, status
from .models import User, Venue, Space, Amenity, Booking
from .serializers import (
    UserSerializer,
    UserReadSerializer,
    VenueSerializer,
    SpaceSerializer,
    BookingSerializer,
    VenueCreateWithSpacesSerializer,
    VenueUpdateWithSpacesSerializer,
)

from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.utils.calling_codes import CALLING_CODES
from datetime import datetime, time, timedelta
import pytz
from rest_framework.permissions import BasePermission

class IsSelf(BasePermission):
    """ Check User Want to CRUD on their own recode or not. """
    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return UserReadSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsSelf()]
        return []


class VenueViewSet(viewsets.ModelViewSet):
    """
    In API Layer (Normal User, Host, Renter, Frontend requests):
        - Account that isn't Host unable to create new Venues.
        - Only Account that id = Owner.id is able to their exist Venues.
    """
    queryset = Venue.objects.all().order_by('-created_at')
    serializer_class = VenueSerializer

    @action(detail=False, methods=["post"], url_path="create-with-spaces", permission_classes=[IsAuthenticated],)
    def create_with_spaces(self, request):

        serializer = VenueCreateWithSpacesSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(
            {
                "venue_id": result["venue"].id,
                "space_ids": [s.id for s in result["spaces"]],
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="spaces")
    def list_spaces(self, request, pk=None):
        venue = self.get_object()

        spaces = venue.spaces.all().order_by("-created_at")
        serializer = SpaceSerializer(spaces, many=True)

        return Response(
            {
                "venue": VenueSerializer(venue).data,
                "spaces": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=["patch"],
        url_path="update-with-spaces",
        permission_classes=[IsAuthenticated],
    )
    def update_with_spaces(self, request, pk=None):
        venue = self.get_object()

        serializer = VenueUpdateWithSpacesSerializer(
            instance=venue,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Venue updated successfully"})

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        venue = self.get_object()
        if venue.owner != self.request.user:
            raise PermissionDenied("You can only edit your own venue.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("You can only delete your own venue.")
        instance.delete()


class SpaceViewSet(viewsets.ModelViewSet):
    queryset = Space.objects.all().order_by('-created_at')
    serializer_class = SpaceSerializer

    def perform_create(self, serializer):
        venue = serializer.validated_data["venue"]

        if venue.owner != self.request.user:
            raise PermissionDenied("Only venue owner can create spaces.")
        serializer.save()

    def perform_update(self, serializer):
        space = self.get_object()
        venue = serializer.validated_data.get("venue", space.venue)

        if venue.owner != self.request.user:
            raise PermissionDenied("Only venue owner can update spaces.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.venue.owner != self.request.user:
            raise PermissionDenied("Only venue owner can delete spaces.")
        instance.delete()


class BookingViewSet(viewsets.ViewSet):
    """
    Handles booking creation and fetching existing reservations for a space.
    All datetime handling uses Thailand timezone (Asia/Bangkok).
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path=r"(?P<space_pk>\d+)/reservations")
    def list_reservations(self, request, space_pk=None):
        """
        Returns a list of reserved date ranges (start_date, end_date) for the given space.
        GET /api/bookings/<space_pk>/reservations/

        IMPORTANT: Returns dates in YYYY-MM-DD format (Thailand timezone)
        """
        space = get_object_or_404(Space, pk=space_pk)

        # Get Bangkok timezone
        bangkok_tz = pytz.timezone('Asia/Bangkok')

        bookings = Booking.objects.filter(
            space=space,
            status__in=["PENDING", "ACCEPTED"],
        ).order_by('start_datetime')

        reservations = []
        for b in bookings:
            # Convert UTC datetime to Bangkok timezone, then extract date
            start_bangkok = b.start_datetime.astimezone(bangkok_tz)
            end_bangkok = b.end_datetime.astimezone(bangkok_tz)

            reservations.append({
                'start': start_bangkok.date().isoformat(),
                'end': end_bangkok.date().isoformat(),
            })

        # Debug log
        print(f"Returning reservations for space {space_pk}:", reservations)
        return Response(reservations, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path=r"(?P<space_pk>\d+)/confirm")
    def confirm_booking(self, request, space_pk=None):
        """
        Creates a new booking for the specified space.
        POST /api/bookings/<space_pk>/confirm/

        Expects: StartDate (YYYY-MM-DD), EndDate (YYYY-MM-DD), totalCost
        All dates are interpreted as Bangkok timezone dates.
        """
        space = get_object_or_404(Space, pk=space_pk)

        serializer = BookingSerializer(
            data=request.data,
            context={"request": request, "space_id": space.id}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        start_date = validated_data["StartDate"]
        end_date = validated_data["EndDate"]

        # Get Bangkok timezone
        bangkok_tz = pytz.timezone('Asia/Bangkok')

        # Create timezone-aware datetimes in Bangkok timezone
        # Start at 00:00:00 Bangkok time
        start_dt = bangkok_tz.localize(datetime.combine(start_date, time.min))
        # End at 23:59:59 Bangkok time
        end_dt = bangkok_tz.localize(
            datetime.combine(end_date, time(23, 59, 59)))

        print(f"Creating booking: {start_dt} to {end_dt}")  # Debug log

        # Django will automatically convert these to UTC for storage
        booking = Booking.objects.create(
            space=space,
            renter=request.user,
            start_datetime=start_dt,
            end_datetime=end_dt,
            total_price=validated_data["totalCost"],
            status="ACCEPTED",
            payment_status="PAID",
        )

        return Response(
            {
                "message": f"Booking confirmed for Space ID {space_pk}.",
                "booking_id": booking.id,
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET"])
def amenity_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Amenity.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    qs = qs.order_by("name")[:10]
    return Response([a.name for a in qs])


@api_view(["GET"])
def calling_codes(request):
    return Response(CALLING_CODES)
