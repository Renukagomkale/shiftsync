from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsManager
from .serializers import BusinessSerializer, JoinSerializer, MemberSerializer, RegisterSerializer, UserSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user, context={"request": request}).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)


class BusinessView(APIView):
    def get_permissions(self):
        if self.request.method in ("POST", "PATCH"):
            return [IsManager()]
        return [IsAuthenticated()]

    def current_business(self):
        business = self.request.user.business
        if business is None:
            raise NotFound("You have not joined a business yet.")
        return business

    def get(self, request):
        return Response(BusinessSerializer(self.current_business(), context={"request": request}).data)

    def post(self, request):
        if request.user.business_id:
            raise ValidationError("You already belong to a business.")
        serializer = BusinessSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            business = serializer.save()
            request.user.business = business
            request.user.save(update_fields=["business"])
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        serializer = BusinessSerializer(
            self.current_business(), data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class JoinBusinessView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "join"

    def post(self, request):
        if request.user.role != User.Role.WORKER:
            raise PermissionDenied("Managers create a business instead of joining one.")
        if request.user.business_id:
            raise ValidationError("You already belong to a business.")
        serializer = JoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.business = serializer.validated_data["join_code"]
        request.user.save(update_fields=["business"])
        return Response(BusinessSerializer(request.user.business, context={"request": request}).data)


class MembersView(APIView):
    def get(self, request):
        if request.user.business_id is None:
            raise NotFound("You have not joined a business yet.")
        members = User.objects.filter(business_id=request.user.business_id).order_by("name")
        return Response(MemberSerializer(members, many=True).data)
