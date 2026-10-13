from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsManager

from .permissions import IsBusinessMember
from .serializers import ShiftSerializer
from .services.summary import build_summary


class DashboardSummaryView(APIView):
    permission_classes = [IsBusinessMember, IsManager]

    def get(self, request):
        day = None
        raw = request.query_params.get("week")
        if raw:
            try:
                day = parse_date(raw)
            except ValueError:
                day = None
            if day is None:
                raise ValidationError({"week": "Use a date inside the week you want, for example 2026-10-12."})
        summary = build_summary(request.user.business, day)
        summary["unassigned_shifts"] = ShiftSerializer(
            summary["unassigned_shifts"], many=True, context={"request": request}
        ).data
        return Response(summary)
