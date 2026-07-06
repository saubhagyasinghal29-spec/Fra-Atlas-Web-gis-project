from django.urls import path

from apps.privacy import views

urlpatterns = [
    path("privacy/my-data/", views.my_data),
    path("privacy/erase/", views.erase),
]
