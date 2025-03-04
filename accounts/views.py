    # accounts/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import (LoginSerializer, PersonalUserRegistrationSerializer, AgentRegistrationSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, ProfileSerializer)
from .models import User, TransportProvider, Ticket, TravelPass, PurchaseHistory
from django.utils import timezone
import uuid
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    return Response({"message": f"Welcome {request.user.email} to your {request.user.user_type} dashboard!"})

class PersonalUserRegisterView(generics.CreateAPIView):
    serializer_class = PersonalUserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "Registration successful. Please check your email to verify."}, 
                        status=status.HTTP_201_CREATED)

class AgentRegisterView(generics.CreateAPIView):
    serializer_class = AgentRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "Agency registration successful. Please check your email to verify."}, 
                        status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        token, _ = Token.objects.get_or_create(user=user)
        dashboard = 'personal_dashboard' if user.user_type == 'personal' else 'agent_dashboard'
        return Response({
            "message": "Login successful",
            "token": token.key,
            "user_type": user.user_type,
            "redirect": dashboard
        }, status=status.HTTP_200_OK)
    
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({"message": "OTP sent to your email for password reset."},
                        status=status.HTTP_200_OK)
    
class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({"message": "Password reset successful. You can now log in with your new password"},
                        status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Populate sample data for testing (remove in production)
        if not TransportProvider.objects.exists():
            TransportProvider.objects.bulk_create([
                TransportProvider(name="Air Peace", mode="air", integration_status=True),
                TransportProvider(name="Amtrak", mode="rail", integration_status=True),
                TransportProvider(name="FlixBus", mode="road", integration_status=True),
                TransportProvider(name="Ferryhopper", mode="water", integration_status=True),
            ])

        if not user.tickets.exists():
            providers = TransportProvider.objects.all()
            ticket = Ticket.objects.create(
                user=user,
                provider=providers[0],  # Air Peace
                route="Lagos to Abuja",
                departure_time=timezone.now() + timezone.timedelta(hours=2),
                price=150.00,
                status="active",
                qr_code=str(uuid.uuid4()),
                nfc_code=str(uuid.uuid4())[:8]
            )
            PurchaseHistory.objects.create(
                user=user,
                total_fare=ticket.price,
                payment_method="Visa",
            ).tickets.add(ticket)

        if not user.travel_passes.exists():
            pass_obj = TravelPass.objects.create(
                user=user,
                pass_type="Monthly Multi-Modal",
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                usage_count=5,
                auto_renew=True
            )
            pass_obj.providers.set(TransportProvider.objects.all())

        serializer = ProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Profile updated successfully", "data": serializer.data}, 
                        status=status.HTTP_200_OK)

class SocialLoginCallbackView(APIView):
    def post(self, request):
        user = request.user
        token, _ = Token.objects.get_or_create(user=user)
        dashboard = 'personal_dashboard' if user.user_type == 'personal' else 'agent_dashboard'
        return Response({
            "message": "Social Login successful",
            "token": token.key,
            "user_type": user.user_type,
            "redirect": dashboard
        }, status=status.HTTP_200_OK),
        return Response({"message": "Social Login failed. Please try again."}, status=status.HTTP_400_BAD_REQUEST)