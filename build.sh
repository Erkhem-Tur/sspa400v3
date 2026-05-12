#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py migrate
python create_departments.py
python manage.py shell -c "
from lms.models import Lesson
Lesson.objects.get_or_create(id=1, defaults={'title': 'SSPA Operation English — 400 questions', 'description': 'Vocabulary, Grammar, Flashcards, Listening', 'order': 1})
"
