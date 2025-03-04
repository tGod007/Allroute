# accounts/models.py
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('personal', 'Personal'),
        ('agent', 'Agent'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='personal')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    models.BooleanField(default=False)
    accessibility_requirements = models.TextField(blank=True, null=True, help_text="e.g., wheelchair access")
    preferred_routes = models.TextField(blank = True, null = True, help_text="e.g., Lagos to Abuja")
    fare_alerts = models.BooleanField(default=False)


    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()  # Use custom manager

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.email}"
    
class TransportProvider(models.Model):
    MODE_CHOICES = (
        ('rail', 'Rail'),
        ('air', 'Air'),
        ('road', 'Road'),
        ('water', 'Water')
    )
    name=models.CharField(max_length=100, unique=True)
    mode=models.CharField(max_length=10, choices=MODE_CHOICES)
    integration_status=models.BooleanField(default=True)
    api_endpoint = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.mode})"

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    provider = models.ForeignKey(TransportProvider, on_delete=models.CASCADE)
    route = models.CharField(max_length=200)
    departure_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    qr_code = models.CharField(max_length=100, unique=True)
    nfc_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider.name} - {self.route} ({self.user.email})"

class TravelPass(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_passes')
    pass_type = models.CharField(max_length=50)  # e.g., "Monthly Multi-Modal"
    providers = models.ManyToManyField(TransportProvider)  # Multi-modal support
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    usage_count = models.PositiveIntegerField(default=0)
    auto_renew = models.BooleanField(default=False)

    def is_active(self):
        return timezone.now() < self.end_date

    def __str__(self):
        return f"{self.pass_type} - {self.user.email}"

class PurchaseHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_history')
    tickets = models.ManyToManyField(Ticket)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)  # e.g., "Visa", "Paystack"

    def __str__(self):
        return f"Purchase {self.id} - {self.user.email}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at
    
class AgentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    company_name = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50, unique=True)
    office_location = models.CharField(max_length=200)
    agency_size = models.PositiveIntegerField(default=1)
    contact_info = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.company_name} - {self.user.email}"
