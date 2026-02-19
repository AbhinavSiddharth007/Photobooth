# Photobooth Project

A Django-based photobooth web application that allows event owners to create events, upload photos, and share galleries with guests.

The project includes automated testing, linting, and CI integration for code quality and reliability.

---

## Features

* Create and manage events
* Upload event photos
* Guest gallery access via shared links
* AWS S3 integration for media storage
* Automated tests with pytest
* Code linting and formatting with Ruff
* Pre-commit hooks for consistent code quality
* CI workflow for automatic checks on push and pull request

---

## Tech Stack

* Python 3.11+
* Django 5
* AWS S3 (boto3)
* pytest and pytest-django
* Ruff for linting and formatting

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Photobooth.git
cd Photobooth
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```
SECRET_KEY=your_django_secret
DEBUG=True

AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=your_bucket
AWS_REGION=your_region
```

Do not commit `.env` to Git.

---

## Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Run Development Server

```bash
python manage.py runserver
```

Open:

```
http://127.0.0.1:8000/
```

---

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov
```

---

## Linting with Ruff

Check issues:

```bash
ruff check .
```

Auto-fix:

```bash
ruff check . --fix
```

Format code:

```bash
ruff format .
```

---

## Pre-commit Hooks

Install hooks:

```bash
pre-commit install
```

Run manually:

```bash
pre-commit run --all-files
```

Hooks run automatically before each commit.

---

## Continuous Integration

GitHub Actions automatically:

* Runs pre-commit checks
* Runs Ruff linting
* Executes pytest tests

On every push and pull request to:

```
main
develop
```

---

## Project Structure (simplified)

```
Photobooth/
│
├── photobooth_project/
│   ├── events/
│   ├── templates/
│   └── settings.py
│
├── .github/workflows/
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Contributing

1. Create a feature branch
2. Commit changes
3. Ensure tests pass
4. Open a Pull Request

---

## License

This project is for educational or demonstration purposes.
