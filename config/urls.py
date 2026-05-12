from django.contrib import admin
from django.urls import path
from lms import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('setup-profile/', views.setup_profile, name='setup_profile'),
    path('lesson/<int:lesson_id>/', views.lesson_view, name='lesson'),
    path('api/quiz/submit/', views.submit_quiz, name='submit_quiz'),
    path('profile/', views.profile_view, name='profile'),
    path('departments/', views.department_view, name='departments'),
]
