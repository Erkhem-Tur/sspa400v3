from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Lesson


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class LessonViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='learner',
            password='pass12345',
        )

    def test_first_lesson_uses_interactive_template(self):
        Lesson.objects.create(
            id=1,
            title='SSPA Operation English - 400 questions',
            description='Vocabulary, Grammar, Flashcards, Listening',
            order=1,
        )
        self.client.login(username='learner', password='pass12345')

        response = self.client.get(reverse('lesson', args=[1]))

        self.assertContains(response, 'SSPA Operation English')
        self.assertContains(response, '400 Questions')

    def test_additional_lessons_show_database_content(self):
        lesson = Lesson.objects.create(
            id=2,
            title='COP17 Registration & Access Control English - A1 Resource Pack',
            description='Teacher guide\nLearner handouts\nHomework',
            order=2,
        )
        self.client.login(username='learner', password='pass12345')

        response = self.client.get(reverse('lesson', args=[lesson.id]))

        self.assertContains(response, 'COP17 Registration')
        self.assertContains(response, 'Teacher guide')
        self.assertContains(response, 'Learner handouts')
        self.assertNotContains(response, '400 Questions')
