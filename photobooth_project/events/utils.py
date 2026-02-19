import qrcode
from io import BytesIO
import base64
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
import uuid


def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


def upload_photo_to_s3(file, event_id):
    s3_client = get_s3_client()

    # Generate unique filename
    file_extension = file.name.split(".")[-1]
    s3_key = f"events/{event_id}/{uuid.uuid4()}.{file_extension}"

    try:
        # Upload to S3 WITHOUT ACL (new AWS buckets do not allow ACLs)
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                "ContentType": getattr(file, "content_type", "application/octet-stream")
                # 'ACL': 'public-read'  <- REMOVE this line
            },
        )

        # Generate URL
        s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"

        return {"s3_key": s3_key, "s3_url": s3_url}
    except ClientError as e:
        raise Exception(f"S3 upload failed: {str(e)}")


def validate_image_file(file):
    max_size = getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)  # fallback 10MB
    allowed_types = getattr(
        settings, "ALLOWED_IMAGE_TYPES", ["image/jpeg", "image/png", "image/jpg"]
    )

    if file.size > max_size:
        return False, f"File size exceeds {max_size / (1024 * 1024)} MB"

    content_type = getattr(file, "content_type", None)

    # Camera-captured photos constructed via JS File() can arrive as
    # 'application/octet-stream'. Fall back to sniffing the magic bytes.
    if content_type not in allowed_types:
        header = file.read(12)
        file.seek(0)  # rewind so the upload still works

        # JPEG: starts with FF D8 FF
        if header[:3] == b"\xff\xd8\xff":
            pass  # valid — let it through
        # PNG: starts with the 8-byte PNG signature
        elif header[:8] == b"\x89PNG\r\n\x1a\n":
            pass  # valid
        else:
            return False, "Invalid file type"

    return True, None


def delete_photo_from_s3(s3_key):
    s3_client = get_s3_client()
    try:
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
    except ClientError as e:
        print(f"S3 delete error: {str(e)}")
