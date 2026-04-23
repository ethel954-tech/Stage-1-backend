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
        params = request.query_params

        # Validation & Pagination
        try:
            page = int(params.get('page', 1))
            limit = int(params.get('limit', 10))
            if page <= 0 or limit <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"status": "error", "message": "Invalid query parameters"}, status=422)

        limit = min(limit, 50)

        # Sorting validation
        sort_by = params.get('sort_by', 'created_at')
        order = params.get('order', 'desc').lower()

        allowed_sort = ['age', 'created_at', 'gender_probability']

        if sort_by not in allowed_sort or order not in ['asc', 'desc']:
            return Response({"status": "error", "message": "Invalid query parameters"}, status=422)

        queryset = self.get_queryset()

        # Filtering
        filters = {}
        try:
            if params.get('gender'):
                filters['gender__iexact'] = params.get('gender')

            if params.get('age_group'):
                filters['age_group__iexact'] = params.get('age_group')

            if params.get('country_id'):
                filters['country_id__iexact'] = params.get('country_id')

            if params.get('min_age'):
                filters['age__gte'] = int(params.get('min_age'))

            if params.get('max_age'):
                filters['age__lte'] = int(params.get('max_age'))

            if params.get('min_gender_probability'):
                filters['gender_probability__gte'] = float(params.get('min_gender_probability'))

            if params.get('min_country_probability'):
                filters['country_probability__gte'] = float(params.get('min_country_probability'))

        except (ValueError, TypeError):
            return Response({"status": "error", "message": "Invalid query parameters"}, status=422)

        queryset = queryset.filter(**filters)

        # Sorting
        prefix = '-' if order == 'desc' else ''
        queryset = queryset.order_by(f"{prefix}{sort_by}")

        total = queryset.count()
        offset = (page - 1) * limit
        data = queryset[offset:offset + limit]

        serializer = ProfileListSerializer(data, many=True)

        return Response({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": serializer.data
        })

    def search(self, request):
        params = request.query_params
        q = params.get('q', '').strip()

        if not q:
            return Response({"status": "error", "message": "Missing or empty parameter"}, status=400)

        parsed = self._parse_query(q)

        if parsed is None:
            return Response({"status": "error", "message": "Unable to interpret query"}, status=400)

        # Pagination
        try:
            page = int(params.get('page', 1))
            limit = int(params.get('limit', 10))
            if page <= 0 or limit <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"status": "error", "message": "Invalid query parameters"}, status=422)

        limit = min(limit, 50)

        queryset = self.get_queryset()
        filters = {}

        if 'gender' in parsed:
            filters['gender'] = parsed['gender']
        if 'age_group' in parsed:
            filters['age_group'] = parsed['age_group']
        if 'country_id' in parsed:
            filters['country_id'] = parsed['country_id']
        if 'min_age' in parsed:
            filters['age__gte'] = parsed['min_age']
        if 'max_age' in parsed:
            filters['age__lte'] = parsed['max_age']

        queryset = queryset.filter(**filters).order_by('-created_at')

        total = queryset.count()
        offset = (page - 1) * limit
        data = queryset[offset:offset + limit]

        serializer = ProfileListSerializer(data, many=True)

        return Response({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": serializer.data
        })

    def _parse_query(self, query):
        query = query.lower()
        filters = {}

        # 1. Gender (robust)
        males = re.search(r'\b(male|males|man|men|boy|boys)\b', query)
        females = re.search(r'\b(female|females|woman|women|girl|girls|lady|ladies)\b', query)

        if males and females:
            pass
        elif males:
            filters['gender'] = 'male'
        elif females:
            filters['gender'] = 'female'

        # 2. "young" = 16–24
        if re.search(r'\byoung\b', query):
            filters['min_age'] = 16
            filters['max_age'] = 24

        # 3. numeric overrides
        above = re.search(r'\b(above|over)\s+(\d+)\b', query)
        if above:
            filters['min_age'] = int(above.group(2))

        below = re.search(r'\b(below|under)\s+(\d+)\b', query)
        if below:
            filters['max_age'] = int(below.group(2))

        # 4. age groups
        if re.search(r'\b(adult|adults)\b', query):
            filters['age_group'] = 'adult'

        if re.search(r'\b(teen|teens|teenager|teenagers)\b', query):
            filters['age_group'] = 'teenager'

        # 5. country (STRICT match)
        country_map = {
            'nigeria': 'NG',
            'kenya': 'KE',
            'angola': 'AO'
        }

        for name, code in country_map.items():
            if re.search(rf'\b{name}\b', query):
                filters['country_id'] = code
                break

        # 6. allow "people" queries
        if not filters:
            if re.search(r'\b(people|nigeria|kenya|angola)\b', query):
                return filters

        return filters if filters else None

    def create(self, request):
        name = request.data.get('name')

        if not isinstance(name, str) or not name.strip():
            return Response(
                {"status": "error", "message": "Invalid or missing name"},
                status=422
            )

        name = name.strip().lower()

        if Profile.objects.filter(name=name).exists():
            profile = Profile.objects.get(name=name)
            return Response(
                {"status": "success", "data": ProfileSerializer(profile).data},
                status=200
            )

        serializer = ProfileCreateSerializer(data={"name": name})

        if not serializer.is_valid():
            return Response(
                {"status": "error", "message": serializer.errors},
                status=400
            )

        try:
            profile = serializer.save()
            return Response(
                {"status": "success", "data": ProfileSerializer(profile).data},
                status=201
            )
        except Exception:
            return Response(
                {"status": "error", "message": "Server error"},
                status=500
            )

    def retrieve(self, request, pk):
        try:
            profile = Profile.objects.get(pk=pk)
            return Response({"status": "success", "data": ProfileSerializer(profile).data})
        except Profile.DoesNotExist:
            return Response({"status": "error", "message": "Profile not found"}, status=404)

    def destroy(self, request, pk):
        try:
            profile = Profile.objects.get(pk=pk)
            profile.delete()
            return Response(status=204)
        except Profile.DoesNotExist:
            return Response(status=404)