from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Profile
from .serializers import ProfileSerializer, ProfileCreateSerializer

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return ProfileCreateSerializer
        return ProfileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        gender = params.get('gender')
        country_id = params.get('country_id')
        age_group = params.get('age_group')

        if gender:
            queryset = queryset.filter(gender__iexact=gender)
        if country_id:
            queryset = queryset.filter(country_id__iexact=country_id)
        if age_group:
            queryset = queryset.filter(age_group__iexact=age_group)

        return queryset

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')

        if not name:
            return Response({
                'status': 'error',
                'message': 'Name is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if Profile.objects.filter(name=name).exists():
            profile = Profile.objects.get(name=name)
            serializer = self.get_serializer(profile)
            return Response({
                'status': 'success',
                'message': 'Profile already exists',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'status': 'success',
            'message': 'Profile deleted successfully'
        }, status=status.HTTP_200_OK)