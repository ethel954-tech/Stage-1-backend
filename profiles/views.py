import re
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from .models import Profile
from .serializers import (
    ProfileCreateSerializer, 
    ProfileListSerializer, 
    ProfileSerializer
)


class ProfileViewSet(ViewSet):
    def get_queryset(self):
        return Profile.objects.all()

    def list(self, request):
        """Advanced filtering, sorting, pagination"""
        queryset = self.get_queryset()
        
        # Filters
        params = request.query_params
        gender = params.get('gender')
        age_group = params.get('age_group')
        country_id = params.get('country_id')
        min_age = params.get('min_age')
        max_age = params.get('max_age')
        min_gender_prob = params.get('min_gender_probability')
        min_country_prob = params.get('min_country_probability')

        if gender:
            queryset = queryset.filter(gender__iexact=gender)
        if age_group:
            queryset = queryset.filter(age_group__iexact=age_group)
        if country_id:
            queryset = queryset.filter(country_id__iexact=country_id)
        
        try:
            if min_age:
                queryset = queryset.filter(age__gte=int(min_age))
            if max_age:
                queryset = queryset.filter(age__lte=int(max_age))
            if min_gender_prob:
                queryset = queryset.filter(gender_probability__gte=float(min_gender_prob))
            if min_country_prob:
                queryset = queryset.filter(country_probability__gte=float(min_country_prob))
        except ValueError as e:
            return Response(
                {"status": "error", "message": f"Invalid parameter type: {e}"}, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Sorting
        sort_by = params.get('sort_by', 'created_at')
        order = params.get('order', 'desc').lower()
        sort_map = {
            'age': 'age',
            'created_at': 'created_at', 
            'gender_probability': 'gender_probability'
        }
        if sort_by in sort_map:
            direction = '' if order == 'asc' else '-'
            queryset = queryset.order_by(direction + sort_map[sort_by])
        else:
            queryset = queryset.order_by('-created_at')

        # Pagination
        page_num = max(1, int(params.get('page', 1)))
        page_size = min(50, max(1, int(params.get('limit', 10))))
        
        total_count = queryset.count()
        offset = (page_num - 1) * page_size
        paginated_qs = queryset[offset:offset + page_size]

        serializer = ProfileListSerializer(paginated_qs, many=True)
        
        return Response({
            "status": "success",
            "page": page_num,
            "limit": page_size,
            "total": total_count,
            "data": serializer.data
        })

    def search(self, request):
        """Natural language search - rule-based"""
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response(
                {"status": "error", "message": "Query 'q' required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rule-based parser
        query_lower = q.lower()
        filters = {}
        
        # Gender patterns
        if re.search(r'\b(male(s?)|man|guy|men|boy(s?))\b', query_lower):
            filters['gender'] = 'male'
        elif re.search(r'\b(female(s?)|woman|girl|women|lady|ladies)\b', query_lower):
            filters['gender'] = 'female'
        
        # Age patterns
        age_match = re.search(r'(?:above|over|more than|\s>)\s*(\d+)|(?:below|under|less than|\s<)\s*(\d+)|(\d+)(?:\s*(?:-|to)\s*(\d+))?', query_lower)
        if age_match:
            groups = age_match.groups()
            if groups[0]:  # above X
                filters['age__gte'] = int(groups[0])
            elif groups[1]:  # below X
                filters['age__lte'] = int(groups[1])
            elif groups[2] and groups[3]:  # X-Y
                filters['age__range'] = (int(groups[2]), int(groups[3]))
        
        # Age groups
        if re.search(r'\b(young|kid|child|teen|adolescent)\b', query_lower):
            filters['age_group__in'] = ['child', 'teenager']
        elif re.search(r'\b(adult|grown-up)\b', query_lower):
            filters['age_group'] = 'adult'
        elif re.search(r'\b(old|senior|elderly)\b', query_lower):
            filters['age__gte'] = 60
        
        # Countries (expandable)
        country_map = {
            'nigeria': 'NG', 'nigerian': 'NG',
            'kenya': 'KE', 'kenyan': 'KE',
            'usa': 'US', 'america': 'US', 'american': 'US',
            'uk': 'GB', 'britain': 'GB', 'english': 'GB',
        }
        for country, code in country_map.items():
            if country in query_lower:
                filters['country_id'] = code
                break

        if not filters:
            return Response(
                {"status": "error", "message": "Unable to interpret query"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Apply filters
        queryset = Profile.objects.all()
        q_object = Q()
        for key, value in filters.items():
            if '__in' in key:
                q_object &= Q(**{key: value})
            elif '__range' in key:
                q_object &= Q(**{key: value})
            else:
                q_object &= Q(**{key: value})
        
        queryset = queryset.filter(q_object).order_by('-created_at')[:20]

        serializer = ProfileListSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "interpreted": filters,
            "data": serializer.data
        })

    def create(self, request):
        name = request.data.get('name')
        if not isinstance(name, str) or not name.strip():
            return Response(
                {"status": "error", "message": "Invalid or missing name"}, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        normalized_name = name.strip().lower()
        if Profile.objects.filter(name=normalized_name).exists():
            profile = Profile.objects.get(name=normalized_name)
            return Response(
                {"status": "success", "data": ProfileSerializer(profile).data},
                status=status.HTTP_200_OK
            )

        serializer = ProfileCreateSerializer(data={"name": normalized_name})
        if not serializer.is_valid():
            return Response(
                {"status": "error", "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = serializer.save()
            return Response(
                {"status": "success", "data": ProfileSerializer(profile).data},
                status=status.HTTP_201_CREATED
            )
        except Exception:
            return Response(
                {"status": "error", "message": "Server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, pk):
        try:
            profile = Profile.objects.get(pk=pk)
            return Response({"status": "success", "data": ProfileSerializer(profile).data})
        except Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk):
        try:
            profile = Profile.objects.get(pk=pk)
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

