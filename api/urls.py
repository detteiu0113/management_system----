from django.urls import path
from .views.accounts import LoginView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
]
