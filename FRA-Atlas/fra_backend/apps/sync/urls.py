from django.urls import path

from apps.sync import views

urlpatterns = [
    path("sync/pull/", views.pull),
    path("sync/push/", views.push),
]
