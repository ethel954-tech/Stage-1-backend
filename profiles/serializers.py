import requests
from rest_framework import serializers

from .models import Profile


class ExternalAPIError(Exception):
    def __init__(self, external_api):
        self.external_api = external_api
        super().__init__(f"{external_api} returned an invalid response")


def get_age_group(age):
    if age <= 12:
        return "child"
    if age <= 19:
        return "teenager"
    if age <= 59:
        return "adult"
    return "senior"


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "gender",
            "gender_probability",
            "sample_size",
            "age",
            "age_group",
            "country_id",
            "country_probability",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "gender",
            "age",
            "age_group",
            "country_id",
        ]


class ProfileCreateSerializer(serializers.Serializer):
    name = serializers.CharField()

    def validate_name(self, value):
        if not isinstance(value, str):
            raise serializers.ValidationError("Invalid type")

        cleaned_value = value.strip()
        if not cleaned_value:
            raise serializers.ValidationError("Missing or empty name")

        return cleaned_value.lower()

    def _get_json(self, url):
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    
    def create(self, validated_data):
        name = validated_data["name"]

        def safe_get(url):
            try:
                res = requests.get(url, timeout=5)
                res.raise_for_status()
                return res.json()
            except:
                return {}

    # ✅ Safe API calls (no crashing)
        gender_data = safe_get(f"https://api.genderize.io?name={name}")
        age_data = safe_get(f"https://api.agify.io?name={name}")
        country_data = safe_get(f"https://api.nationalize.io?name={name}")

    # ✅ Safe extraction with fallbacks
        gender = gender_data.get("gender")
        gender_probability = gender_data.get("probability", 0)
        sample_size = gender_data.get("count", 0)

        age = age_data.get("age")
        age_group = get_age_group(age) if age else None

        countries = country_data.get("country", [])
        if countries:
            top_country = max(countries, key=lambda item: item["probability"])
            country_id = top_country.get("country_id")
            country_probability = top_country.get("probability", 0)
        else:
            country_id = None
            country_probability = 0

        return Profile.objects.create(
            name=name,
            gender=gender,
            gender_probability=gender_probability,
            sample_size=sample_size,
            age=age,
            age_group=age_group,
            country_id=country_id,
            country_probability=country_probability,
        )