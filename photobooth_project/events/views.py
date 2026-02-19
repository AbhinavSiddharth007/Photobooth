import logging
import json
import zipfile
import requests
from io import BytesIO

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from .models import Event, Photo
from .utils import generate_qr_code, upload_photo_to_s3, validate_image_file, delete_photo_from_s3

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'events/home.html')


@require_POST
def create_event(request):
    event_name = request.POST.get('event_name', '').strip()
    owner_email = request.POST.get('owner_email', '').strip()

    if not event_name:
        return JsonResponse({'error': 'Event name is required'}, status=400)

    event = Event.objects.create(
        name=event_name,
        owner_email=owner_email if owner_email else None
    )

    guest_url = request.build_absolute_uri(reverse('guest_gallery', args=[event.guest_code]))
    owner_url = request.build_absolute_uri(reverse('owner_dashboard', args=[event.owner_secret]))
    event.save()
    qr_code = generate_qr_code(guest_url)

    return JsonResponse({
        'success': True,
        'guest_url': guest_url,
        'owner_url': owner_url,
        'qr_code': qr_code,
        'event_name': event.name,
        'guest_code': event.guest_code
    })


def guest_gallery(request, guest_code):
    event = get_object_or_404(Event, guest_code=guest_code)
    return render(request, 'events/guest_gallery.html', {'event': event})


def owner_dashboard(request, owner_secret):
    event = get_object_or_404(Event, owner_secret=owner_secret)
    photos = event.photos.all()
    return render(request, 'events/owner_dashboard.html', {
        'event': event,
        'photos': photos,
        'photo_count': photos.count(),
    })


@require_POST
def download_photos_zip(request, owner_secret):
    event = get_object_or_404(Event, owner_secret=owner_secret)

    try:
        body = json.loads(request.body)
        photo_ids = body.get('photo_ids', [])
    except (json.JSONDecodeError, AttributeError):
        photo_ids = []

    if photo_ids:
        photos = event.photos.filter(id__in=photo_ids)
    else:
        photos = event.photos.all()

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for photo in photos:
            try:
                r = requests.get(photo.s3_url, timeout=10)
                if r.status_code == 200:
                    filename = photo.s3_url.split("/")[-1]
                    zip_file.writestr(filename, r.content)
            except Exception:
                pass

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response['Content-Disposition'] = f'attachment; filename="{event.name}_photos.zip"'
    return response


@require_POST
@csrf_exempt
def upload_photo(request, guest_code):
    event = get_object_or_404(Event, guest_code=guest_code)

    if not event.uploads_enabled:
        return JsonResponse({'error': 'Uploads disabled'}, status=403)

    photo_file = request.FILES.get('photo')
    if not photo_file:
        return JsonResponse({'error': 'No photo provided'}, status=400)

    # Log what we actually received so we can debug in the terminal
    logger.warning(
        "[upload] file received: name=%r  size=%d  content_type=%r",
        photo_file.name, photo_file.size, photo_file.content_type,
    )

    is_valid, error = validate_image_file(photo_file)
    if not is_valid:
        logger.warning("[upload] validation failed: %s", error)
        return JsonResponse({'error': error}, status=400)

    try:
        s3_data = upload_photo_to_s3(photo_file, event.id)
        logger.warning("[upload] s3_data=%r", s3_data)

        if not s3_data or not s3_data.get('s3_url'):
            return JsonResponse({'error': 'S3 upload returned no URL'}, status=500)

        photo = Photo.objects.create(
            event=event,
            s3_key=s3_data['s3_key'],
            s3_url=s3_data['s3_url'],
            original_filename=photo_file.name,
            file_size=photo_file.size,
            content_type=photo_file.content_type,
        )

        logger.warning("[upload] saved photo id=%s  url=%r", photo.id, photo.s3_url)

        return JsonResponse({
            'success': True,
            'photo_id': str(photo.id),
            'photo_url': photo.s3_url,
        })

    except Exception as e:
        logger.exception("[upload] unhandled exception: %s", e)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def delete_photo(request, owner_secret, photo_id):
    event = get_object_or_404(Event, owner_secret=owner_secret)
    photo = get_object_or_404(Photo, id=photo_id, event=event)

    try:
        delete_photo_from_s3(photo.s3_key)
        photo.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def bulk_delete_photos(request, owner_secret):
    event = get_object_or_404(Event, owner_secret=owner_secret)

    try:
        body = json.loads(request.body)
        photo_ids = body.get('photo_ids', [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    if not photo_ids:
        return JsonResponse({'error': 'No photo IDs provided'}, status=400)

    photos = Photo.objects.filter(id__in=photo_ids, event=event)

    deleted_count = 0
    for photo in photos:
        try:
            delete_photo_from_s3(photo.s3_key)
            photo.delete()
            deleted_count += 1
        except Exception as e:
            logger.error("Error deleting photo %s: %s", photo.id, e)

    return JsonResponse({'success': True, 'deleted': deleted_count})


@require_POST
def toggle_uploads(request, owner_secret):
    event = get_object_or_404(Event, owner_secret=owner_secret)
    event.uploads_enabled = not event.uploads_enabled
    event.save()
    return JsonResponse({
        'success': True,
        'uploads_enabled': event.uploads_enabled
    })
