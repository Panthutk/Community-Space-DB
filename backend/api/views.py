from rest_framework import viewsets
from .models import Item, User, Location, Venue, Space
from .serializers import ItemSerializer, UserSerializer, LocationSerializer, VenueSerializer, SpaceSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all().order_by("-created_at")
    serializer_class = ItemSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('-created_at')
    serializer_class = LocationSerializer

class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all().order_by('-created_at')
    serializer_class = VenueSerializer

class SpaceViewSet(viewsets.ModelViewSet):
    queryset = Space.objects.all().order_by('-created_at')
    serializer_class = SpaceSerializer
