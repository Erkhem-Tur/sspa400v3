import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg, Sum, Count
from django.utils import timezone

from .forms import RegisterForm, LoginForm, ProfileForm
from .models import Lesson, QuizResult, UserProgress, Department, Video


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        UserProgress.objects.create(user=user)
        login(request, user)
        return redirect('setup_profile')
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
def setup_profile(request):
    progress, _ = UserProgress.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=progress)
    if form.is_valid():
        p = form.save(commit=False)
        p.profile_complete = True
        p.save()
        return redirect('dashboard')
    return render(request, 'lms/setup_profile.html', {'form': form})


@login_required
def dashboard_view(request):
    progress, _ = UserProgress.objects.get_or_create(user=request.user)
    if not progress.profile_complete and not request.user.is_staff:
        return redirect('setup_profile')
    lessons = Lesson.objects.all()
    results = QuizResult.objects.filter(user=request.user).order_by('-taken_at')[:20]
    ctx = {'lessons': lessons, 'progress': progress, 'results': results}

    if request.user.is_staff:
        total_students = UserProgress.objects.filter(user__is_staff=False).count()
        total_missions = QuizResult.objects.count()
        raw_avg = QuizResult.objects.aggregate(avg=Avg('score'))['avg']
        overall_avg = round((raw_avg / 10 * 100)) if raw_avg else 0
        total_hours = round(
            (UserProgress.objects.filter(user__is_staff=False)
             .aggregate(s=Sum('study_minutes'))['s'] or 0) / 60, 1
        )
        recent = (UserProgress.objects
                  .filter(user__is_staff=False)
                  .select_related('user', 'department')
                  .order_by('-last_accessed')[:8])
        dept_summary = []
        for dept in Department.objects.all():
            members = dept.members.filter(user__is_staff=False)
            dept_summary.append({
                'name': dept.name,
                'count': members.count(),
                'avg': round(members.aggregate(a=Avg('total_score'))['a'] or 0),
            })
        ctx['admin'] = {
            'total_students': total_students,
            'total_missions': total_missions,
            'overall_avg': overall_avg,
            'total_hours': total_hours,
            'recent': recent,
            'dept_summary': dept_summary,
        }
    return render(request, 'lms/dashboard.html', ctx)


@login_required
def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if lesson.pk == 1:
        return render(request, 'lms/index.html', {'lesson': lesson})

    resource_file = ''
    if (
        'COP17' in lesson.title
        or 'SSPA_COP17_A1_English_Resource_Pack.docx' in lesson.description
    ):
        resource_file = 'lms/resources/SSPA_COP17_A1_English_Resource_Pack.docx'

    return render(request, 'lms/lesson_detail.html', {
        'lesson': lesson,
        'resource_file': resource_file,
    })


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
@require_POST
def track_study_time(request):
    try:
        data = json.loads(request.body)
        minutes = int(data.get('minutes', 0))
        if 0 < minutes <= 120:
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            progress.study_minutes += minutes
            progress.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def profile_view(request):
    progress, _ = UserProgress.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=progress)
    if form.is_valid():
        p = form.save(commit=False)
        p.profile_complete = True
        p.save()
        return redirect('profile')
    results = QuizResult.objects.filter(user=request.user).order_by('-taken_at')
    return render(request, 'lms/profile.html', {
        'progress': progress,
        'results': results,
        'form': form,
    })


@login_required
def worksheets_view(request):
    return render(request, 'lms/worksheets.html')


@login_required
def videos_view(request):
    videos = Video.objects.filter(is_published=True)
    return render(request, 'lms/videos.html', {'videos': videos})


# ── Department management (web UI, staff only) ──────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def dept_manage_view(request):
    """List departments + inline add form."""
    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            error = 'Хэлтсийн нэр хоосон байна.'
        elif Department.objects.filter(name__iexact=name).exists():
            error = f'"{name}" нэртэй хэлтэс аль хэдийн байна.'
        else:
            max_order = Department.objects.count()
            Department.objects.create(name=name, order=max_order)
            return redirect('dept_manage')
    departments = Department.objects.all()
    return render(request, 'lms/dept_manage.html', {
        'departments': departments,
        'error': error,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def dept_edit_view(request, dept_id):
    dept = get_object_or_404(Department, pk=dept_id)
    error = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            dept.delete()
            return redirect('dept_manage')
        name = request.POST.get('name', '').strip()
        if not name:
            error = 'Нэр хоосон байна.'
        elif Department.objects.filter(name__iexact=name).exclude(pk=dept_id).exists():
            error = f'"{name}" нэртэй хэлтэс аль хэдийн байна.'
        else:
            dept.name = name
            dept.order = int(request.POST.get('order', dept.order))
            dept.save()
            return redirect('dept_manage')
    return render(request, 'lms/dept_edit.html', {'dept': dept, 'error': error})


@login_required
@user_passes_test(lambda u: u.is_staff)
def department_view(request):
    dept_filter = request.GET.get('dept', '')
    search = request.GET.get('q', '').strip()

    departments = Department.objects.all()

    all_progress = UserProgress.objects.select_related('user', 'department').filter(
        user__is_staff=False
    ).order_by('-total_score')

    if dept_filter:
        all_progress = all_progress.filter(department_id=dept_filter)
    if search:
        all_progress = all_progress.filter(
            full_name__icontains=search
        ) | all_progress.filter(user__username__icontains=search)

    student_list = []
    for p in all_progress:
        results = QuizResult.objects.filter(user=p.user)
        avg = results.aggregate(avg=Avg('score'))['avg']
        days = (timezone.now() - p.user.date_joined).days
        student_list.append({
            'full_name': p.full_name or p.user.username,
            'username': p.user.username,
            'rank': p.rank,
            'department': p.department.name if p.department else '—',
            'total_score': p.total_score,
            'missions_completed': p.missions_completed,
            'avg_pct': round(avg / 10 * 100) if avg else 0,
            'last': p.last_accessed,
            'joined': p.user.date_joined,
            'study_days': days,
            'study_hours': round(p.study_minutes / 60, 1),
            'profile_complete': p.profile_complete,
        })

    total_students = UserProgress.objects.filter(user__is_staff=False).count()
    total_missions = QuizResult.objects.count()
    overall_avg = QuizResult.objects.aggregate(avg=Avg('score'))['avg']
    overall_avg_pct = round(overall_avg / 10 * 100) if overall_avg else 0
    total_study_hours = round((UserProgress.objects.filter(user__is_staff=False).aggregate(s=Sum('study_minutes'))['s'] or 0) / 60, 1)

    dept_data = []
    for dept in departments:
        members = dept.members.filter(user__is_staff=False)
        dept_data.append({
            'id': dept.id,
            'name': dept.name,
            'count': members.count(),
            'avg_score': round(members.aggregate(avg=Avg('total_score'))['avg'] or 0),
        })

    return render(request, 'lms/department.html', {
        'student_list': student_list,
        'departments': departments,
        'dept_data': dept_data,
        'dept_filter': dept_filter,
        'search': search,
        'total_students': total_students,
        'total_missions': total_missions,
        'overall_avg_pct': overall_avg_pct,
        'total_study_hours': total_study_hours,
    })
