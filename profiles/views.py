import requests
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import Profile
from .serializers import (
    ExternalAPIError,
    ProfileCreateSerializer,
    ProfileListSerializer,
    ProfileSerializer,
)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all().order_by("-created_at")
    serializer_class = ProfileSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return ProfileCreateSerializer
        if self.action == "list":
            return ProfileListSerializer
        return ProfileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        gender = params.get("gender")
        country_id = params.get("country_id")
        age_group = params.get("age_group")

        if gender:
            queryset = queryset.filter(gender__iexact=gender)
        if country_id:
            queryset = queryset.filter(country_id__iexact=country_id)
        if age_group:
            queryset = queryset.filter(age_group__iexact=age_group)

        return queryset

    def create(self, request, *args, **kwargs):
        if "name" not in request.data:
            return Response(
                {"status": "error", "message": "Missing or empty name"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = request.data.get("name")

        if not isinstance(name, str):
            return Response(
                {"status": "error", "message": "Invalid type"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if not name.strip():
            return Response(
                {"status": "error", "message": "Missing or empty name"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        normalized_name = name.strip().lower()
        existing_profile = Profile.objects.filter(name__iexact=normalized_name).first()

        if existing_profile:
            return Response(
                {
                    "status": "success",
                    "message": "Profile already exists",
                    "data": ProfileSerializer(existing_profile).data,
                },
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(data={"name": normalized_name})

        if not serializer.is_valid():
            error_message = self._extract_error_message(serializer.errors)
            status_code = (
                status.HTTP_422_UNPROCESSABLE_ENTITY
                if error_message == "Invalid type"
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(
                {"status": "error", "message": error_message},
                status=status_code,
            )

        try:
            profile = serializer.save()
        except ExternalAPIError as exc:
            return Response(
                {"status": "error", "message": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except requests.RequestException:
            return Response(
                {"status": "error", "message": "Upstream service failure"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"status": "error", "message": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "status": "success",
                "data": ProfileSerializer(profile).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "status": "success",
                "count": queryset.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ProfileSerializer(instance)
        return Response(
            {
                "status": "success",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if response is None:
            return response

        if response.status_code == status.HTTP_404_NOT_FOUND:
            return Response(
                {"status": "error", "message": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return response

    @staticmethod
    def _extract_error_message(errors):
        if isinstance(errors, dict):
            first_value = next(iter(errors.values()), None)
            if isinstance(first_value, list) and first_value:
                return str(first_value[0])
            if isinstance(first_value, dict):
                return ProfileViewSet._extract_error_message(first_value)
            if first_value:
                return str(first_value)

        if isinstance(errors, list) and errors:
            return str(errors[0])

        return "Invalid request"
