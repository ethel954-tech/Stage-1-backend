from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Profile


class ProfileAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _mock_response(self, payload, status_code=200):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = payload
        response.raise_for_status = Mock()
        return response

    @patch("profiles.serializers.requests.get")
    def test_create_profile_success(self, mock_get):
        mock_get.side_effect = [
            self._mock_response(
                {"name": "ella", "gender": "female", "probability": 0.99, "count": 1234}
            ),
            self._mock_response({"name": "ella", "age": 46, "count": 1000}),
            self._mock_response(
                {
                    "name": "ella",
                    "country": [
                        {"country_id": "US", "probability": 0.15},
                        {"country_id": "DRC", "probability": 0.85},
                    ],
                }
            ),
        ]

        response = self.client.post("/api/profiles/", {"name": "ella"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["name"], "ella")
        self.assertEqual(response.data["data"]["gender"], "female")
        self.assertEqual(response.data["data"]["gender_probability"], 0.99)
        self.assertEqual(response.data["data"]["sample_size"], 1234)
        self.assertEqual(response.data["data"]["age"], 46)
        self.assertEqual(response.data["data"]["age_group"], "adult")
        self.assertEqual(response.data["data"]["country_id"], "DRC")
        self.assertEqual(response.data["data"]["country_probability"], 0.85)
        self.assertIn("created_at", response.data["data"])

    @patch("profiles.serializers.requests.get")
    def test_create_profile_duplicate_returns_existing_profile(self, mock_get):
        profile = Profile.objects.create(
            name="ella",
            gender="female",
            gender_probability=0.99,
            sample_size=1234,
            age=46,
            age_group="adult",
            country_id="DRC",
            country_probability=0.85,
        )

        response = self.client.post("/api/profiles/", {"name": "Ella"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["message"], "Profile already exists")
        self.assertEqual(response.data["data"]["id"], str(profile.id))
        self.assertEqual(Profile.objects.count(), 1)
        mock_get.assert_not_called()

    def test_create_profile_missing_name(self):
        response = self.client.post("/api/profiles/", {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"status": "error", "message": "Missing or empty name"},
        )

    def test_create_profile_empty_name(self):
        response = self.client.post("/api/profiles/", {"name": "   "}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"status": "error", "message": "Missing or empty name"},
        )

    def test_create_profile_invalid_type(self):
        response = self.client.post("/api/profiles/", {"name": 123}, format="json")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data, {"status": "error", "message": "Invalid type"})

    @patch("profiles.serializers.requests.get")
    def test_create_profile_genderize_invalid_response(self, mock_get):
        mock_get.side_effect = [
            self._mock_response(
                {"name": "ella", "gender": None, "probability": 0, "count": 0}
            )
        ]

        response = self.client.post("/api/profiles/", {"name": "ella"}, format="json")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.data,
            {"status": "error", "message": "Genderize returned an invalid response"},
        )
        self.assertEqual(Profile.objects.count(), 0)

    @patch("profiles.serializers.requests.get")
    def test_create_profile_agify_invalid_response(self, mock_get):
        mock_get.side_effect = [
            self._mock_response(
                {"name": "ella", "gender": "female", "probability": 0.99, "count": 1234}
            ),
            self._mock_response({"name": "ella", "age": None, "count": 1000}),
        ]

        response = self.client.post("/api/profiles/", {"name": "ella"}, format="json")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.data,
            {"status": "error", "message": "Agify returned an invalid response"},
        )
        self.assertEqual(Profile.objects.count(), 0)

    @patch("profiles.serializers.requests.get")
    def test_create_profile_nationalize_invalid_response(self, mock_get):
        mock_get.side_effect = [
            self._mock_response(
                {"name": "ella", "gender": "female", "probability": 0.99, "count": 1234}
            ),
            self._mock_response({"name": "ella", "age": 46, "count": 1000}),
            self._mock_response({"name": "ella", "country": []}),
        ]

        response = self.client.post("/api/profiles/", {"name": "ella"}, format="json")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.data,
            {"status": "error", "message": "Nationalize returned an invalid response"},
        )
        self.assertEqual(Profile.objects.count(), 0)

    def test_get_single_profile(self):
        profile = Profile.objects.create(
            name="emmanuel",
            gender="male",
            gender_probability=0.99,
            sample_size=1234,
            age=25,
            age_group="adult",
            country_id="NG",
            country_probability=0.85,
        )

        response = self.client.get(f"/api/profiles/{profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["name"], "emmanuel")
        self.assertEqual(response.data["data"]["country_id"], "NG")
        self.assertIn("created_at", response.data["data"])

    def test_get_single_profile_not_found(self):
        response = self.client.get(
            "/api/profiles/00000000-0000-0000-0000-000000000000/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"status": "error", "message": "Profile not found"})

    def test_get_all_profiles_with_filters(self):
        Profile.objects.create(
            name="emmanuel",
            gender="male",
            gender_probability=0.99,
            sample_size=1234,
            age=25,
            age_group="adult",
            country_id="NG",
            country_probability=0.85,
        )
        Profile.objects.create(
            name="sarah",
            gender="female",
            gender_probability=0.98,
            sample_size=2345,
            age=28,
            age_group="adult",
            country_id="US",
            country_probability=0.90,
        )

        response = self.client.get("/api/profiles/?gender=MALE&country_id=ng")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["data"],
            [
                {
                    "id": str(Profile.objects.get(name="emmanuel").id),
                    "name": "emmanuel",
                    "gender": "male",
                    "age": 25,
                    "age_group": "adult",
                    "country_id": "NG",
                }
            ],
        )

    def test_delete_profile(self):
        profile = Profile.objects.create(
            name="ella",
            gender="female",
            gender_probability=0.99,
            sample_size=1234,
            age=46,
            age_group="adult",
            country_id="DRC",
            country_probability=0.85,
        )

        response = self.client.delete(f"/api/profiles/{profile.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(Profile.objects.filter(id=profile.id).exists())
