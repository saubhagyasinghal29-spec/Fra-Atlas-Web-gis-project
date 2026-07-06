from django.urls import path

from apps.documents import views

urlpatterns = [
    path("fra-claims/<uuid:claim_id>/documents/", views.ClaimDocumentsView.as_view()),
    path("documents/<uuid:attachment_id>/", views.download_attachment),
]
