from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from academy.models import StudentProfile, Course, TrainerProfile


def public_home(request):
    """
    Public Home Page:
    - Heading: Welcome to DeviX Academy by Ram Sir
    - Hero section with institute metrics
    - Responsive grid of ALL active students showing ONLY photo, name, course name.
    - Security: No phone/email/other data exposed.
    - Search by student name or course + pagination.
    """
    search_query = request.GET.get('q', '').strip()
    course_filter = request.GET.get('course', '').strip()

    students_qs = StudentProfile.objects.filter(is_active=True).select_related('course')

    if search_query:
        students_qs = students_qs.filter(
            Q(name__icontains=search_query) |
            Q(course__name__icontains=search_query)
        )

    if course_filter:
        students_qs = students_qs.filter(course_id=course_filter)

    # Ordering
    students_qs = students_qs.order_by('name')

    # Pagination: 12 students per page
    paginator = Paginator(students_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Metrics for hero section
    total_students_count = StudentProfile.objects.filter(is_active=True).count()
    total_trainers_count = TrainerProfile.objects.count()
    total_courses_count = Course.objects.filter(is_active=True).count()
    all_courses = Course.objects.filter(is_active=True).order_by('name')

    # All faculty trainers to be listed at the top
    trainers = TrainerProfile.objects.select_related('user', 'department').order_by('trainer_id')

    context = {
        'trainers': trainers,
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_course': course_filter,
        'courses': all_courses,
        'total_students': total_students_count,
        'total_trainers': total_trainers_count,
        'total_courses': total_courses_count,
    }
    return render(request, 'public/home.html', context)
