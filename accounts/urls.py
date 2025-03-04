from django.urls import include, path
from .views import LoginView, PasswordResetConfirmView, PasswordResetRequestView, PersonalUserRegisterView, AgentRegisterView, ProfileView, dashboard, SocialLoginCallbackView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/personal/', PersonalUserRegisterView.as_view(), name='personal_register'),
    path('register/agent/', AgentRegisterView.as_view(), name='agent_register'),
    path('dashboard/', dashboard, name='dashboard'),
    path('password/reset/request/', PasswordResetRequestView.as_view(), name = 'password_reset_request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name = 'password_reset_confirm'),
    path('profile/', ProfileView.as_view(), name = 'profile'),
    path('social/callback/', SocialLoginCallbackView.as_view(), name = 'social_callback'),
    path('accounts/', include('allauth.urls')),
]