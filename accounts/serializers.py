# accounts/serializers.py
from rest_framework import serializers
from django.core.validators import MinLengthValidator
from .models import User, AgentProfile
from django.contrib.auth import authenticate
from .models import User, PasswordResetOTP, TransportProvider, Ticket, TravelPass, PurchaseHistory
from django.utils import timezone
import pyotp

class PersonalUserRegistrationSerializer(serializers.ModelSerializer):
    create_password = serializers.CharField(
        write_only=True,
        validators=[MinLengthValidator(8, "Password must be at least 8 characters.")],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    email_address = serializers.EmailField(source='email')  # Map to model's email field

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email_address', 'create_password', 'confirm_password']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email_address': {'required': True},
        }

    def validate(self, data):
        if data['create_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def validate_create_password(self, value):
        if not any(char.isupper() for char in value) or not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter and one number.")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')  # Remove confirm_password before creating user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['create_password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],

            user_type='personal'
        )
        user.email_user("Welcome to Allroute!", "Please verify your email: [link]")
        return user

class TransportProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportProvider
        fields = ['name', 'mode', 'integration_status']

class TicketSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    mode = serializers.CharField(source='provider.mode', read_only=True)

    class Meta:
        model = Ticket
        fields = ['provider_name', 'mode', 'route', 'departure_time', 'price', 'status', 'qr_code', 'nfc_code']

class TravelPassSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    providers = TransportProviderSerializer(many=True, read_only=True)

    class Meta:
        model = TravelPass
        fields = ['pass_type', 'start_date', 'end_date', 'usage_count', 'auto_renew', 'is_active', 'providers']

class PurchaseHistorySerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseHistory
        fields = ['total_fare', 'purchase_date', 'payment_method', 'tickets']

class ProfileSerializer(serializers.ModelSerializer):
    email_address = serializers.EmailField(source='email', read_only=True)
    tickets = TicketSerializer(many=True, read_only=True, source='tickets.filter(status="active")')  # Active tickets only
    travel_passes = TravelPassSerializer(many=True, read_only=True)
    purchase_history = PurchaseHistorySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email_address', 'user_type', 'accessibility_requirements', 'preferred_routes', 'fare_alerts', 'tickets', 'travel_passes', 'purchase_history']
        read_only_fields = ['email_address', 'user_type', 'tickets', 'travel_passes', 'purchase_history']
    def validate_accessibility_requirements(self, value):
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("Accessibility requirements must be at least 5 characters if provided.")
        return value
    def validate_preferred_routes(self, value):
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("Preferred routes must be at least 5 characters if provided.")
        return value
            
class AgentRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[MinLengthValidator(12, "Password must be at least 12 characters.")],
        style={'input_type': 'password'}
    )
    company_name = serializers.CharField()
    registration_number = serializers.CharField()
    office_location = serializers.CharField()
    agency_size = serializers.IntegerField()
    contact_info = serializers.CharField()

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'company_name', 
                  'registration_number', 'office_location', 'agency_size', 'contact_info']

    def validate_password(self, value):
        if not any(c.isupper() for c in value) or not any(c.isdigit() for c in value) or not any(c in "!@#$%^&*" for c in value):
            raise serializers.ValidationError("Password must include uppercase, number, and special character.")
        return value

    def create(self, validated_data):
        agent_data = {
            'company_name': validated_data.pop('company_name'),
            'registration_number': validated_data.pop('registration_number'),
            'office_location': validated_data.pop('office_location'),
            'agency_size': validated_data.pop('agency_size'),
            'contact_info': validated_data.pop('contact_info'),
        }
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type='agent'
        )
        AgentProfile.objects.create(user=user, **agent_data)
        user.email_user("Verify Your Agency Account", "Click to verify: [link]")
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        request = self.context.get('request')
        user = authenticate(request=request, email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid email or password.")
    

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        totp = pyotp.TOTP('base32secret3232', interval=120)  # 15-minute validity, adjust secret per user in production
        otp = totp.now()
        expires_at = timezone.now() + timezone.timedelta(minutes=2)
        PasswordResetOTP.objects.create(user=user, otp=otp, expires_at=expires_at)
        user.email_user("Password Reset OTP", f"Your OTP for password reset is: {otp}")
        return user

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(
        write_only=True,
        validators=[MinLengthValidator(8, "Password must be at least 8 characters.")],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        try:
            user = User.objects.get(email=data['email'])
            reset_entry = PasswordResetOTP.objects.filter(user=user, otp=data['otp']).latest('created_at')
            if not reset_entry.is_valid():
                raise serializers.ValidationError("OTP has expired.")
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            raise serializers.ValidationError("Invalid email or OTP.")
        
        return data

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        reset_entry = PasswordResetOTP.objects.filter(user=user, otp=self.validated_data['otp']).latest('created_at')
        user.set_password(self.validated_data['new_password'])
        user.save()
        reset_entry.delete()  # OTP used, remove it
        return user
