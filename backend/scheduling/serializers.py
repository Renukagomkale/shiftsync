from rest_framework import serializers

from accounts.models import User

from .models import Notification, Shift, SwapRequest


class ShiftSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = ["id", "position", "start", "end", "assigned_to", "assigned_to_name", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            fields["assigned_to"].queryset = User.objects.filter(business_id=request.user.business_id)
        return fields

    def get_assigned_to_name(self, shift):
        return shift.assigned_to.name if shift.assigned_to else None

    def validate(self, attrs):
        start = attrs.get("start", getattr(self.instance, "start", None))
        end = attrs.get("end", getattr(self.instance, "end", None))
        if start and end and end <= start:
            raise serializers.ValidationError({"end": "End time must be after the start time."})
        return attrs


class SwapSerializer(serializers.ModelSerializer):
    shift = ShiftSerializer(read_only=True)
    requested_by_name = serializers.CharField(source="requested_by.name", read_only=True)
    target_worker_name = serializers.SerializerMethodField()

    class Meta:
        model = SwapRequest
        fields = [
            "id",
            "status",
            "shift",
            "requested_by",
            "requested_by_name",
            "target_worker",
            "target_worker_name",
            "created_at",
            "resolved_at",
        ]

    def get_target_worker_name(self, swap):
        return swap.target_worker.name if swap.target_worker else None


class SwapCreateSerializer(serializers.Serializer):
    shift = serializers.PrimaryKeyRelatedField(queryset=Shift.objects.none())
    target_worker = serializers.PrimaryKeyRelatedField(queryset=User.objects.none(), allow_null=True, required=False)

    def get_fields(self):
        fields = super().get_fields()
        business_id = self.context["request"].user.business_id
        fields["shift"].queryset = Shift.objects.filter(business_id=business_id)
        fields["target_worker"].queryset = User.objects.filter(business_id=business_id)
        return fields


class SwapActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["accept", "decline", "approve", "reject", "cancel"])


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "swap", "is_read", "created_at"]
        read_only_fields = ["id", "message", "swap", "created_at"]
