from django.urls import path, include
from registry.views import lookup_view, lookup_number

urlpatterns = [
    path('', lookup_view, name='lookup'),
    path('api/lookup/', lookup_number, name='api-lookup'),
]
