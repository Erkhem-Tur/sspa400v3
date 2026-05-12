import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg, Sum, Count

from .forms import RegisterForm, LoginForm
from .models import Lesson, QuizResult, UserProgress, Department


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        UserProgress.objects.create(
            user=user,
            department=form.cleaned_data['department']
        )
        login(request, user)
        return redirect('dashboard')
    return render(request, 'lms/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard')
    return render(request, 'lms/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    lessons = Lesson.objects.all()
    progress, _ = UserProgress.objects.get_or_create(user=request.user)
    results = QuizResult.objects.filter(user=request.user).order_by('-taken_at')[:20]
    return render(request, 'lms/dashboard.html', {
        'lessons': lessons,
        'progress': progress,
        'results': results,
    })


@login_required
def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    return render(request, 'lms/index.html', {'lesson': lesson})


@login_required
@require_POST
def submit_quiz(request):
    try:
        data = json.loads(request.body)
        lesson = get_object_or_404(Lesson, pk=data.get('lesson_id'))
        batch_index = int(data.get('batch_index', 0))
        score = int(data.get('score', 0))
        total = int(data.get('total', 10))

        QuizResult.objects.create(
            user=request.user,
            lesson=lesson,
            batch_index=batch_index,
            score=score,
            total=total,
        )

        progress, _ = UserProgress.objects.get_or_create(user=request.user)
        progress.total_score += score
        progress.missions_completed += 1
        progress.save()

        return JsonResponse({'status': 'ok', 'score': score, 'total': total})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def profile_view(request):
    progress, _ = UserProgress.objects.get_or_create(user=request.user)
    results = QuizResult.objects.filter(user=request.user).order_by('-taken_at')
    return render(request, 'lms/profile.html', {
        'progress': progress,
        'results': results,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def department_view(request):
    departments = Department.objects.prefetch_related('members__user', 'members__user__quiz_results').all()
    dept_data = []
    for dept in departments:
        members = dept.members.select_related('user').all()
        member_list = []
        for m in members:
            results = QuizResult.objects.filter(user=m.user)
            member_list.append({
                'username': m.user.username,
                'total_score': m.total_score,
                'missions_completed': m.missions_completed,
                'avg_pct': round(results.aggregate(
                    avg=Avg('score') )['avg'] / 10 * 100) if results.exists() else 0,
                'last': m.last_accessed,
            })
        member_list.sort(key=lambda x: x['total_score'], reverse=True)
        dept_data.append({
            'name': dept.name,
            'count': len(member_list),
            'members': member_list,
            'total_score': sum(m['total_score'] for m in member_list),
            'avg_score': round(sum(m['total_score'] for m in member_list) / len(member_list)) if member_list else 0,
        })
    return render(request, 'lms/department.html', {'dept_data': dept_data})
