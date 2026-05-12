from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Lesson(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_results')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quiz_results')
    batch_index = models.IntegerField()
    score = models.IntegerField()
    total = models.IntegerField(default=10)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-taken_at']

    def percentage(self):
        return round(self.score / self.total * 100) if self.total else 0

    def __str__(self):
        return f"{self.user.username} – Mission {self.batch_index + 1}: {self.score}/{self.total}"


RANK_CHOICES = [
    ('', '-- Цолоо сонгоно уу --'),
    ('Энгийн | Private',           'Энгийн | Private'),
    ('Дэд ахлагч | Corporal',      'Дэд ахлагч | Corporal'),
    ('Ахлагч | Sergeant',          'Ахлагч | Sergeant'),
    ('Ахлах ахлагч | Staff Sergeant', 'Ахлах ахлагч | Staff Sergeant'),
    ('Дэслэгч | Lieutenant',       'Дэслэгч | Lieutenant'),
    ('Ахлах дэслэгч | Senior Lieutenant', 'Ахлах дэслэгч | Senior Lieutenant'),
    ('Ахмад | Captain',            'Ахмад | Captain'),
    ('Хошууч | Major',             'Хошууч | Major'),
    ('Дэд хурандаа | Lieutenant Colonel', 'Дэд хурандаа | Lieutenant Colonel'),
    ('Хурандаа | Colonel',         'Хурандаа | Colonel'),
    ('Бригадын генерал | Brigadier General', 'Бригадын генерал | Brigadier General'),
]


class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    full_name = models.CharField(max_length=200, blank=True)
    rank = models.CharField(max_length=100, blank=True, choices=RANK_CHOICES)
    profile_complete = models.BooleanField(default=False)
    total_score = models.IntegerField(default=0)
    missions_completed = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        dept = self.department.name if self.department else 'Хэлтэсгүй'
        return f"{self.user.username} ({dept}) – {self.total_score} оноо"
