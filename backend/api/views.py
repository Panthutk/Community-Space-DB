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