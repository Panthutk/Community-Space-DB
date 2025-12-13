from rest_framework import viewsets, status
from .models import User, Venue, Space, Amenity, SpaceAmenity
from .serializers import  UserSerializer, VenueSerializer, SpaceSerializer
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer

class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all().order_by('-created_at')
    serializer_class = VenueSerializer

class SpaceViewSet(viewsets.ModelViewSet):
    queryset = Space.objects.all().order_by('-created_at')
    serializer_class = SpaceSerializer

@api_view(["POST"])
@transaction.atomic
def create_venue_with_spaces(request):
    """
    Expects:
    {
      "venue": {...},
      "spaces": [...]
    }
    """
    data = request.data
    venue_data = data.get("venue") or {}
    spaces_data = data.get("spaces") or []

    # TEMP: pick owner as first user (since you don't have auth wired yet)
    owner = User.objects.first()
    if not owner:
        return Response({"detail": "No user exists. Create a user first."}, status=400)

    venue = Venue.objects.create(
        owner=owner,
        name=venue_data.get("name", ""),
        description=venue_data.get("description", ""),
        address=venue_data.get("location", ""),  # you use `address` in model
        venue_type=venue_data.get("venue_type", "WHOLE"),
        city="",
        province="",
        country="Thailand",
    )

    created_space_ids = []
    for s in spaces_data:
        space = Space.objects.create(
            venue=venue,
            name=s.get("name", ""),
            description=s.get("description", ""),
            space_width=s.get("space_width", "5.00"),
            space_height=s.get("space_height", "5.00"),
            price_per_day=s.get("price_per_day", "0.00"),
            cleaning_fee=s.get("cleaning_fee"),
            is_published=bool(s.get("is_published", False)),
            amenities_enabled=bool(s.get("have_amenity", False)),
        )
        created_space_ids.append(space.id)

        amenities = s.get("amenities") or []
        if s.get("have_amenity") and amenities:
            for name in amenities:
                name = (name or "").strip()
                if not name:
                    continue
                amenity, _ = Amenity.objects.get_or_create(name=name)
                SpaceAmenity.objects.get_or_create(
                    space=space,
                    amenity=amenity,
                    defaults={"amount": 1},
                )
    return Response(
        {"venue_id": venue.id, "space_ids": created_space_ids},
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
