from rest_framework import viewsets
from .models import User, Venue, Space
from .serializers import  UserSerializer, VenueSerializer, SpaceSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer

class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all().order_by('-created_at')
    serializer_class = VenueSerializer

class SpaceViewSet(viewsets.ModelViewSet):
    queryset = Space.objects.all().order_by('-created_at')
    serializer_class = SpaceSerializer
