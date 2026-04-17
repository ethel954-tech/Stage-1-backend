from rest_framework import serializers
from .models import Profile
import requests


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'gender', 'gender_probability', 'sample_size',
            'age', 'age_group', 'country_id', 'country_probability', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProfileCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required and cannot be empty.")
        if Profile.objects.filter(name=value).exists():
            raise serializers.ValidationError("Profile already exists.")
        return value

    def create(self, validated_data):
        name = validated_data['name']

        # External API calls
        try:
            # Genderize
            gender_resp = requests.get(f"https://api.genderize.io?name={name}", timeout=5)
            gender_data = gender_resp.json()
            if gender_data.get('gender') is None or gender_data.get('count', 0) == 0:
                raise Exception("Gender API failure")

            # Agify
            age_resp = requests.get(f"https://api.agify.io?name={name}", timeout=5)
            age_data = age_resp.json()
            if age_data.get('age') is None:
                raise Exception("Age API failure")

            # Nationalize
            country_resp = requests.get(f"https://api.nationalize.io?name={name}", timeout=5)
            country_data = country_resp.json()
            countries = country_data.get('country', [])
            if not countries:
                raise Exception("Country API failure")
            top_country = max(countries, key=lambda c: c['probability'])

        except Exception as e:
            print("API ERROR:", e)

            # fallback values instead of crashing
            gender_data = {'gender': None, 'probability': 0, 'count': 0}
            age_data = {'age': 0}
            top_country = {'country_id': None, 'probability': 0}

        # Process age group
        age = age_data['age']
        if age <= 12:
            age_group = 'child'
        elif age <= 19:
            age_group = 'teenager'
        elif age <= 59:
            age_group = 'adult'
        else:
            age_group = 'senior'

        # Create profile
        profile = Profile.objects.create(
            name=name,
            gender=gender_data['gender'],
            gender_probability=gender_data['probability'],
            sample_size=gender_data['count'],
            age=age,
            age_group=age_group,
            country_id=top_country['country_id'],
            country_probability=top_country['probability']
        )
        return profile

