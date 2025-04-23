from django.urls import path, include
from registry import views as registry_views

urlpatterns = [
    path('', registry_views.lookup_view, name='lookup'),
    path('api/lookup/', registry_views.lookup_number, name='api-lookup'),
]
