from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import User

from .models import SwapRequest
from .permissions import IsBusinessMember
from .serializers import SwapActionSerializer, SwapCreateSerializer, SwapSerializer
from .services import swaps

ACTIONS = {
    "accept": swaps.accept_as_peer,
    "decline": swaps.decline_as_peer,
    "approve": swaps.approve,
    "reject": swaps.reject,
    "cancel": swaps.cancel,
}


class SwapViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SwapSerializer
    permission_classes = [IsBusinessMember]

    def get_queryset(self):
        user = self.request.user
        queryset = SwapRequest.objects.filter(shift__business=user.business).select_related(
            "shift__assigned_to", "requested_by", "target_worker"
        )
        if user.role != User.Role.MANAGER:
            open_for_everyone = Q(target_worker__isnull=True, status=SwapRequest.Status.PENDING_PEER)
            queryset = queryset.filter(Q(requested_by=user) | Q(target_worker=user) | open_for_everyone)
        status = self.request.query_params.get("status")
        if status and self.action == "list":
            if status not in SwapRequest.Status.values:
                raise ValidationError({"status": "Choose one of: " + ", ".join(SwapRequest.Status.values) + "."})
            queryset = queryset.filter(status=status)
        return queryset

    def create(self, request):
        serializer = SwapCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        swap = swaps.create_swap(
            request.user, serializer.validated_data["shift"], serializer.validated_data.get("target_worker")
        )
        return Response(self.get_serializer(swap).data, status=201)

    def partial_update(self, request, pk=None):
        swap = self.get_object()
        serializer = SwapActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = ACTIONS[serializer.validated_data["action"]](swap, request.user)
        return Response(self.get_serializer(updated).data)
