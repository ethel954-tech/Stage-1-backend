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

        if params.get("gender"):
            queryset = queryset.filter(gender__iexact=params.get("gender"))
        if params.get("age_group"):
            queryset = queryset.filter(age_group__iexact=params.get("age_group"))
        if params.get("country_id"):
            queryset = queryset.filter(country_id__iexact=params.get("country_id"))

        return queryset

    def create(self, request, *args, **kwargs):
        name = request.data.get("name")

        # ✅ Missing or empty
        if name is None or name == "":
            return Response(
                {"status": "error", "message": "Name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Invalid type
        if not isinstance(name, str):
            return Response(
                {"status": "error", "message": "Invalid name"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        normalized_name = name.strip()

        if not normalized_name:
            return Response(
                {"status": "error", "message": "Name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Duplicate
        if Profile.objects.filter(name__iexact=normalized_name).exists():
            profile = Profile.objects.get(name__iexact=normalized_name)

            return Response(
                {
                    "status": "success",
                    "message": "Profile already exists",
                    "data": ProfileSerializer(profile).data,
                },
                status=status.HTTP_200_OK,
            )
        
        # ✅ ONLY pass clean data to serializer
        serializer = self.get_serializer(data={"name": normalized_name})

        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "message": self._extract_error_message(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = serializer.save()
        except ExternalAPIError:
            # ✅ FIX: don't return 502 for bad input
            return Response(
                {"status": "error", "message": "Invalid name"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
            {"status": "success", "data": ProfileSerializer(profile).data},
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
        profile = self.get_object()
        serializer = ProfileSerializer(profile)

        return Response(
            {"status": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        profile = self.get_object()
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_exception(self, exc):
        response = super().handle_exception(exc)

        if response and response.status_code == status.HTTP_404_NOT_FOUND:
            return Response(
                {"status": "error", "message": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return response

    @staticmethod
    def _extract_error_message(errors):
        if isinstance(errors, dict):
            first = next(iter(errors.values()), None)
            if isinstance(first, list) and first:
                return str(first[0])
            if isinstance(first, dict):
                return ProfileViewSet._extract_error_message(first)
            if first:
                return str(first)

        if isinstance(errors, list) and errors:
            return str(errors[0])

        return "Invalid request"