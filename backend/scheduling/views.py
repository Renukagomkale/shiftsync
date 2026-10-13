from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from .models import Shift
from .permissions import IsBusinessMember, ManagerWritesMemberReads
from .serializers import ShiftSerializer
from .services.conflicts import ensure_can_work


class ShiftPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


def parse_bound(name, raw, tz):
    try:
        parsed = parse_datetime(raw)
        if parsed is None:
            day = parse_date(raw)
            parsed = None if day is None else datetime.combine(day, time.min)
    except ValueError:
        parsed = None
    if parsed is None:
        raise ValidationError({name: "Use an ISO date or datetime, for example 2026-10-12."})
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    return parsed


class ShiftViewSet(viewsets.ModelViewSet):
    serializer_class = ShiftSerializer
    pagination_class = ShiftPagination
    permission_classes = [IsBusinessMember, ManagerWritesMemberReads]

    def get_queryset(self):
        business = self.request.user.business
        queryset = Shift.objects.filter(business=business).select_related("assigned_to")
        if self.action not in ("list", "mine"):
            return queryset
        tz = ZoneInfo(business.timezone)
        params = self.request.query_params
        if params.get("from"):
            queryset = queryset.filter(end__gt=parse_bound("from", params["from"], tz))
        if params.get("to"):
            queryset = queryset.filter(start__lt=parse_bound("to", params["to"], tz))
        return queryset

    @action(detail=False, methods=["get"])
    def mine(self, request):
        queryset = self.get_queryset().filter(assigned_to=request.user)
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def check_assignment(self, serializer):
        data = serializer.validated_data
        instance = serializer.instance
        if instance is not None and not {"assigned_to", "start", "end"} & data.keys():
            return
        worker = data["assigned_to"] if "assigned_to" in data else getattr(instance, "assigned_to", None)
        if worker is None:
            return
        start = data.get("start", getattr(instance, "start", None))
        end = data.get("end", getattr(instance, "end", None))
        ensure_can_work(self.request.user.business, worker, start, end, exclude_shift=instance)

    def perform_create(self, serializer):
        with transaction.atomic():
            self.check_assignment(serializer)
            serializer.save(business=self.request.user.business, created_by=self.request.user)

    def perform_update(self, serializer):
        with transaction.atomic():
            self.check_assignment(serializer)
            serializer.save()
