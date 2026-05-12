#!/usr/bin/env bash
set -e
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python create_departments.py
python manage.py shell -c "
from lms.models import Lesson
Lesson.objects.get_or_create(id=1, defaults={'title': 'SSPA Operation English — 400 questions', 'description': 'Vocabulary, Grammar, Flashcards, Listening', 'order': 1})
"
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '2b32oh@gmail.com', 'admin1234')
"
