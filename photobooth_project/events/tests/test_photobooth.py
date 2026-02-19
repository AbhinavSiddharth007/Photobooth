import json
import pytest
from unittest.mock import patch
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from events.models import Event, Photo


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def event(db):
    """A basic saved Event."""
    return Event.objects.create(name="Test Party", owner_email="host@example.com")


@pytest.fixture
def photo(db, event):
    """A Photo attached to the test event."""
    return Photo.objects.create(
        event=event,
        s3_key="events/test-photo.jpg",
        s3_url="https://s3.example.com/events/test-photo.jpg",
        original_filename="photo.jpg",
        file_size=204800,
        content_type="image/jpeg",
    )


# ──────────────────────────────────────────────
# Model tests
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestEventModel:
    def test_auto_generates_guest_code(self, event):
        assert event.guest_code
        assert len(event.guest_code) == 12

    def test_auto_generates_owner_secret(self, event):
        assert event.owner_secret
        assert len(event.owner_secret) == 32

    def test_auto_sets_expires_at(self, event):
        expected = timezone.now() + timedelta(days=30)
        diff = abs((event.expires_at - expected).total_seconds())
        assert diff < 5  # within 5 seconds

    def test_uploads_enabled_by_default(self, event):
        assert event.uploads_enabled is True

    def test_is_active_by_default(self, event):
        assert event.is_active is True

    def test_str_returns_name(self, event):
        assert str(event) == "Test Party"

    def test_owner_email_optional(self, db):
        e = Event.objects.create(name="No Email Event")
        assert e.owner_email is None

    def test_guest_codes_are_unique(self, db):
        e1 = Event.objects.create(name="Event 1")
        e2 = Event.objects.create(name="Event 2")
        assert e1.guest_code != e2.guest_code

    def test_owner_secrets_are_unique(self, db):
        e1 = Event.objects.create(name="Event 1")
        e2 = Event.objects.create(name="Event 2")
        assert e1.owner_secret != e2.owner_secret


@pytest.mark.django_db
class TestPhotoModel:
    def test_str_includes_event_name(self, photo):
        assert "Test Party" in str(photo)

    def test_photo_linked_to_event(self, photo, event):
        assert photo.event == event

    def test_photos_ordered_by_latest_first(self, db, event):
        Photo.objects.create(
            event=event,
            s3_key="key1",
            s3_url="https://s3.example.com/1.jpg",
            original_filename="1.jpg",
            file_size=100,
            content_type="image/jpeg",
        )
        p2 = Photo.objects.create(
            event=event,
            s3_key="key2",
            s3_url="https://s3.example.com/2.jpg",
            original_filename="2.jpg",
            file_size=100,
            content_type="image/jpeg",
        )
        photos = list(event.photos.all())
        assert photos[0] == p2  # newest first


# ──────────────────────────────────────────────
# View tests – home
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestHomeView:
    def test_home_returns_200(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 200


# ──────────────────────────────────────────────
# View tests – create_event
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestCreateEventView:
    @patch("events.views.generate_qr_code", return_value="data:image/png;base64,abc")
    def test_create_event_success(self, mock_qr, client):
        response = client.post(reverse("create_event"), {"event_name": "Birthday Bash"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_name"] == "Birthday Bash"
        assert "guest_url" in data
        assert "owner_url" in data
        assert "qr_code" in data

    @patch("events.views.generate_qr_code", return_value="data:image/png;base64,abc")
    def test_create_event_saves_to_db(self, mock_qr, client):
        client.post(reverse("create_event"), {"event_name": "New Year Party"})
        assert Event.objects.filter(name="New Year Party").exists()

    def test_create_event_missing_name_returns_400(self, client):
        response = client.post(reverse("create_event"), {"event_name": ""})
        assert response.status_code == 400
        assert "error" in response.json()

    def test_create_event_get_not_allowed(self, client):
        response = client.get(reverse("create_event"))
        assert response.status_code == 405


# ──────────────────────────────────────────────
# View tests – guest_gallery
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestGuestGalleryView:
    def test_valid_guest_code_returns_200(self, client, event):
        response = client.get(reverse("guest_gallery", args=[event.guest_code]))
        assert response.status_code == 200

    def test_invalid_guest_code_returns_404(self, client):
        response = client.get(reverse("guest_gallery", args=["doesnotexist"]))
        assert response.status_code == 404

    def test_context_contains_event(self, client, event):
        response = client.get(reverse("guest_gallery", args=[event.guest_code]))
        assert response.context["event"] == event


# ──────────────────────────────────────────────
# View tests – owner_dashboard
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestOwnerDashboardView:
    def test_valid_owner_secret_returns_200(self, client, event):
        response = client.get(reverse("owner_dashboard", args=[event.owner_secret]))
        assert response.status_code == 200

    def test_invalid_owner_secret_returns_404(self, client):
        response = client.get(reverse("owner_dashboard", args=["badbadbad"]))
        assert response.status_code == 404

    def test_context_contains_photos_and_count(self, client, event, photo):
        response = client.get(reverse("owner_dashboard", args=[event.owner_secret]))
        assert response.context["photo_count"] == 1


# ──────────────────────────────────────────────
# View tests – toggle_uploads
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestToggleUploadsView:
    def test_toggle_disables_uploads(self, client, event):
        assert event.uploads_enabled is True
        client.post(reverse("toggle_uploads", args=[event.owner_secret]))
        event.refresh_from_db()
        assert event.uploads_enabled is False

    def test_toggle_re_enables_uploads(self, client, event):
        event.uploads_enabled = False
        event.save()
        client.post(reverse("toggle_uploads", args=[event.owner_secret]))
        event.refresh_from_db()
        assert event.uploads_enabled is True

    def test_toggle_returns_success_json(self, client, event):
        response = client.post(reverse("toggle_uploads", args=[event.owner_secret]))
        data = response.json()
        assert data["success"] is True
        assert "uploads_enabled" in data

    def test_toggle_get_not_allowed(self, client, event):
        response = client.get(reverse("toggle_uploads", args=[event.owner_secret]))
        assert response.status_code == 405


# ──────────────────────────────────────────────
# View tests – upload_photo
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestUploadPhotoView:
    def test_upload_disabled_returns_403(self, client, event):
        event.uploads_enabled = False
        event.save()
        response = client.post(reverse("upload_photo", args=[event.guest_code]))
        assert response.status_code == 403

    def test_no_file_returns_400(self, client, event):
        response = client.post(reverse("upload_photo", args=[event.guest_code]))
        assert response.status_code == 400
        assert response.json()["error"] == "No photo provided"

    @patch("events.views.validate_image_file", return_value=(False, "File too large"))
    def test_invalid_file_returns_400(self, mock_validate, client, event):
        from django.core.files.uploadedfile import SimpleUploadedFile

        f = SimpleUploadedFile(
            "bad.exe", b"data", content_type="application/octet-stream"
        )
        response = client.post(
            reverse("upload_photo", args=[event.guest_code]), {"photo": f}
        )
        assert response.status_code == 400
        assert response.json()["error"] == "File too large"

    @patch("events.views.validate_image_file", return_value=(True, None))
    @patch(
        "events.views.upload_photo_to_s3",
        return_value={
            "s3_key": "events/abc/photo.jpg",
            "s3_url": "https://s3.example.com/events/abc/photo.jpg",
        },
    )
    def test_valid_upload_creates_photo(self, mock_s3, mock_validate, client, event):
        from django.core.files.uploadedfile import SimpleUploadedFile

        f = SimpleUploadedFile("shot.jpg", b"\xff\xd8\xff", content_type="image/jpeg")
        response = client.post(
            reverse("upload_photo", args=[event.guest_code]), {"photo": f}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert Photo.objects.filter(event=event).exists()


# ──────────────────────────────────────────────
# View tests – bulk_delete_photos
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestBulkDeletePhotosView:
    @patch("events.views.delete_photo_from_s3")
    def test_bulk_delete_removes_photos(self, mock_s3_delete, client, event, photo):
        payload = json.dumps({"photo_ids": [str(photo.id)]})
        response = client.post(
            reverse("bulk_delete_photos", args=[event.owner_secret]),
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted"] == 1
        assert not Photo.objects.filter(id=photo.id).exists()

    def test_bulk_delete_empty_ids_returns_400(self, client, event):
        payload = json.dumps({"photo_ids": []})
        response = client.post(
            reverse("bulk_delete_photos", args=[event.owner_secret]),
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_bulk_delete_invalid_json_returns_400(self, client, event):
        response = client.post(
            reverse("bulk_delete_photos", args=[event.owner_secret]),
            data="not-json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_bulk_delete_wrong_owner_returns_404(self, client, photo):
        payload = json.dumps({"photo_ids": [str(photo.id)]})
        response = client.post(
            "/owner/wrongsecret/photos/bulk-delete/",
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 404

    @patch("events.views.delete_photo_from_s3")
    def test_bulk_delete_ignores_photos_from_other_events(
        self, mock_s3_delete, client, db
    ):
        event_a = Event.objects.create(name="Event A")
        event_b = Event.objects.create(name="Event B")
        photo_b = Photo.objects.create(
            event=event_b,
            s3_key="key",
            s3_url="https://s3.example.com/b.jpg",
            original_filename="b.jpg",
            file_size=100,
            content_type="image/jpeg",
        )
        # Try to delete event_b's photo using event_a's secret
        payload = json.dumps({"photo_ids": [str(photo_b.id)]})
        client.post(
            reverse("bulk_delete_photos", args=[event_a.owner_secret]),
            data=payload,
            content_type="application/json",
        )
        assert Photo.objects.filter(id=photo_b.id).exists()


# ──────────────────────────────────────────────
# View tests – delete_photo (single)
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestDeletePhotoView:
    @patch("events.views.delete_photo_from_s3")
    def test_delete_single_photo(self, mock_s3_delete, client, event, photo):
        response = client.post(
            reverse("delete_photo", args=[event.owner_secret, str(photo.id)])
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert not Photo.objects.filter(id=photo.id).exists()

    def test_delete_photo_wrong_owner_returns_404(self, client, photo):
        response = client.post(f"/owner/wrongsecret/photo/{photo.id}/delete/")
        assert response.status_code == 404

    def test_delete_photo_get_not_allowed(self, client, event, photo):
        response = client.get(
            reverse("delete_photo", args=[event.owner_secret, str(photo.id)])
        )
        assert response.status_code == 405
