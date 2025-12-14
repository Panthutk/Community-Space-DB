from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import User, Venue, Space

# Create your tests here.
# class UserAPITests(APITestCase):
#
#     def test_create_user_valid_phone(self):
#         """
#         User creation should succeed and return correctly formatted phone number.
#         """
#         url = reverse("user-list")  # router name from `router.register("users", ...)`
#
#         data = {
#             "name": "Alice",
#             "email": "alice@test.com",
#             "password_hash": "abcd",
#             "is_host": True,
#             "country": "TH",
#             "phone": "0812345678"
#         }
#
#         response = self.client.post(url, data, format="json")
#
#         # expected: 201 Created
#         self.assertEqual(response.status_code, 201)
#
#         # Check the formatted phone
#         self.assertEqual(response.data["full_phone"], "+66812345678")
#
#         # Check that the user exists in DB
#         user = User.objects.get(email="alice@test.com")
#         self.assertEqual(user.phone, "+66812345678")
#
#
#     def test_create_user_invalid_phone(self):
#         """
#         Should reject phone numbers with invalid characters.
#         """
#         url = reverse("user-list")
#
#         data = {
#             "name": "Bob",
#             "email": "bob@test.com",
#             "password_hash": "abcd",
#             "is_host": False,
#             "country": "TH",
#             "phone": "08-1234"   # invalid input
#         }
#
#         response = self.client.post(url, data, format="json")
#
#         # expected: 400 Bad Request
#         self.assertEqual(response.status_code, 400)
#
#         # Check error message
#         self.assertIn("phone", response.data)
#
#
#     def test_patch_user_update_phone(self):
#         """
#         Ensure updating phone number also triggers formatting logic.
#         """
#         user = User.objects.create(
#             name="Charlie",
#             email="charlie@test.com",
#             phone="+66811223344",
#             password_hash="xyz"
#         )
#
#         url = reverse("user-detail", args=[user.id])
#
#         data = {
#             "country": "TH",
#             "phone": "0998887777"
#         }
#
#         response = self.client.patch(url, data, format="json")
#
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["full_phone"], "+66998887777")
#
#         # Check DB updated
#         user.refresh_from_db()
#         self.assertEqual(user.phone, "+66998887777")

from api.models import Space

class SpacePermissionTests(APITestCase):

    def setUp(self):
        self.owner = User.objects.create(
            name="Owner",
            email="owner2@test.com",
            phone="+66833333333",
            password_hash="x",
            is_host=True,
        )

        self.other_user = User.objects.create(
            name="Other",
            email="other2@test.com",
            phone="+66844444444",
            password_hash="x",
            is_host=True,
        )

        self.venue = Venue.objects.create(
            name="Owner Venue",
            owner=self.owner,
            venue_type="GRID",
            address="456 Road",
            city="Bangkok",
            country="Thailand",
        )

    def test_owner_can_create_space(self):
        self.client.force_authenticate(user=self.owner)

        url = reverse("space-list")
        data = {
            "venue": self.venue.id,
            "name": "Booth A1",
            "space_width": "5.00",
            "space_height": "5.00",
            "price_per_day": "100.00",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_other_user_cannot_create_space(self):
        self.client.force_authenticate(user=self.other_user)

        url = reverse("space-list")
        data = {
            "venue": self.venue.id,
            "name": "Illegal Booth",
            "space_width": "5.00",
            "space_height": "5.00",
            "price_per_day": "100.00",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 403)

