from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("create/", views.create_event, name="create_event"),
    path("event/<str:guest_code>/", views.guest_gallery, name="guest_gallery"),
    path("owner/<str:owner_secret>/", views.owner_dashboard, name="owner_dashboard"),
    path("event/<str:guest_code>/upload/", views.upload_photo, name="upload_photo"),
    path(
        "owner/<str:owner_secret>/photo/<uuid:photo_id>/delete/",
        views.delete_photo,
        name="delete_photo",
    ),
    path(
        "owner/<str:owner_secret>/toggle-uploads/",
        views.toggle_uploads,
        name="toggle_uploads",
    ),
    path(
        "owner/<str:owner_secret>/download/",
        views.download_photos_zip,
        name="download_photos_zip",
    ),
    path(
        "owner/<str:owner_secret>/photos/bulk-delete/",
        views.bulk_delete_photos,
        name="bulk_delete_photos",
    ),
]
