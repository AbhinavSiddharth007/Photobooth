
# Photo Booth Web App

**Author:** Shafeen
**Version:** 0.1
**Date:** February 2026

---

## Project Overview

The Photo Booth Web App is a **temporary, browser-based photo sharing platform** designed for events. It allows event organizers to create events and collect photos from guests via a QR code or link. Events automatically expire after 30 days.

**Key Goals:**

* Simple event creation for owners
* Guest photo uploads without accounts
* Owner dashboard for managing photos
* Automatic event expiry and photo deletion

---

## Planned Features

**Owner Features:**

* Create event (event name, optional email)
* Receive secret dashboard link
* View, delete, download photos
* Close uploads early

**Guest Features:**

* Scan QR code / click event link
* View event gallery
* Upload photos anonymously
* Share event with others

**System Features:**

* Photo validation (type, size)
* Auto-expiry after 30 days
* Storage on local server (dev) or S3 (production)
* Mobile-friendly design

---

## Project Structure (Planned)

```
photo-booth/
├── backend/                 # Django backend
│   ├── events/              # Event creation, expiry logic
│   ├── photos/              # Photo upload, storage, deletion
│   ├── core/                # Utilities, middleware
│   ├── manage.py
│   └── requirements.txt
├── frontend/                # Templates + JS
│   ├── templates/           # HTML pages
│   └── static/              # CSS and JS files
├── media/                   # Uploaded photos (local dev)
└── README.md                # Project summary and plan
```

---

## Implementation Plan

**Step 1:** Setup Django project and models
**Step 2:** Create event creation form and owner dashboard (basic HTML templates)
**Step 3:** Implement photo upload and gallery view
**Step 4:** Generate QR codes and secret owner links
**Step 5:** Add auto-expiry logic for events and photos
**Step 6:** Polish UI for mobile-friendly experience
**Step 7:** Optional: S3 storage integration and ZIP download

---

## Technologies to Use

* **Backend:** Django (Python)
* **Frontend:** Django templates + JS
* **Database:** PostgreSQL (or SQLite for dev)
* **Storage:** Local file system (dev) / AWS S3 (prod)
* **QR Codes:** Python library (qrcode)

---
