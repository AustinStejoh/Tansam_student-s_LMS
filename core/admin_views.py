from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Avg

from .models import Submission, Assignment, Course


@staff_member_required
def grading_dashboard_view(request):
    assignments = Assignment.objects.select_related('course').order_by('-created_at')
    submissions = (
        Submission.objects.select_related('assignment', 'student')
        .order_by('-submitted_at')
    )

    metrics = {
        'total_assignments': assignments.count(),
        'total_submissions': submissions.count(),
        'avg_grade': submissions.aggregate(avg=Avg('grade'))['avg'],
    }

    context = {
        'assignments': assignments,
        'submissions': submissions[:50],
        'metrics': metrics,
    }
    return render(request, 'admin/grading_dashboard.html', context)


