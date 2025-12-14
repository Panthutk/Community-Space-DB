from rest_framework import viewsets, status
from .models import User, Venue, Space, Amenity
from .serializers import UserSerializer, VenueSerializer, SpaceSerializer, VenueWithSpacesSerializer
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.utils.calling_codes import CALLING_CODES


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer


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
        serializer = VenueWithSpacesSerializer(
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

    def perform_create(self, serializer):
        if not self.request.user.is_host:
            raise PermissionDenied("Only hosts account can create new venues.")
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


# @api_view(["POST"])
# @transaction.atomic
# def create_venue_with_spaces(request):
#     """
#     Expects:
#     {
#       "venue": {...},
#       "spaces": [...]
#     }
#     """
#     data = request.data
#     venue_data = data.get("venue") or {}
#     spaces_data = data.get("spaces") or []
#
#     # TEMP: pick owner as first user (since you don't have auth wired yet)
#     owner = User.objects.first()
#     if not owner:
#         return Response({"detail": "No user exists. Create a user first."}, status=400)
#
#     venue = Venue.objects.create(
#         owner=owner,
#         name=venue_data.get("name", ""),
#         description=venue_data.get("description", ""),
#         address=venue_data.get("location", ""),  # you use `address` in model
#         venue_type=venue_data.get("venue_type", "WHOLE"),
#         city="",
#         province="",
#         country="Thailand",
#     )
#
#     created_space_ids = []
#     for s in spaces_data:
#         space = Space.objects.create(
#             venue=venue,
#             name=s.get("name", ""),
#             description=s.get("description", ""),
#             space_width=s.get("space_width", "5.00"),
#             space_height=s.get("space_height", "5.00"),
#             price_per_day=s.get("price_per_day", "0.00"),
#             cleaning_fee=s.get("cleaning_fee"),
#             is_published=bool(s.get("is_published", False)),
#             amenities_enabled=bool(s.get("have_amenity", False)),
#         )
#         created_space_ids.append(space.id)
#
#         amenities = s.get("amenities") or []
#         if s.get("have_amenity") and amenities:
#             for name in amenities:
#                 name = (name or "").strip()
#                 if not name:
#                     continue
#                 amenity, _ = Amenity.objects.get_or_create(name=name)
#                 SpaceAmenity.objects.get_or_create(
#                     space=space,
#                     amenity=amenity,
#                     defaults={"amount": 1},
#                 )
#     return Response(
#         {"venue_id": venue.id, "space_ids": created_space_ids},
#         status=status.HTTP_201_CREATED,
#     )


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