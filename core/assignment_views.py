from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .assignments import Assignment, AssignmentSubmission
from .models import Topic
from django.utils import timezone

@login_required
def assignment_list(request, topic_id):
    """
    Display list of assignments for a topic
    """
    topic = get_object_or_404(Topic, id=topic_id)
    assignments = Assignment.objects.filter(topic=topic)
    submissions = AssignmentSubmission.objects.filter(
        student=request.user,
        assignment__topic=topic
    )
    
    # Create a dictionary of assignment_id: submission for easy lookup
    submission_dict = {sub.assignment_id: sub for sub in submissions}
    
    context = {
        'topic': topic,
        'assignments': [
            {
                'assignment': assignment,
                'submission': submission_dict.get(assignment.id)
            }
            for assignment in assignments
        ]
    }
    return render(request, 'assignment_list.html', context)

@login_required
def submit_assignment(request, assignment_id):
    """
    Handle assignment submission
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if already submitted
    existing_submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()
    
    if request.method == 'POST':
        if not request.FILES.get('submission_file'):
            messages.error(request, 'Please select a file to submit.')
            return redirect('assignment_list', topic_id=assignment.topic.id)
        
        if existing_submission:
            # Update existing submission
            existing_submission.submission_file = request.FILES['submission_file']
            existing_submission.submitted_at = timezone.now()
            existing_submission.status = 'submitted'
            existing_submission.save()
            messages.success(request, 'Assignment resubmitted successfully!')
        else:
            # Create new submission
            AssignmentSubmission.objects.create(
                assignment=assignment,
                student=request.user,
                submission_file=request.FILES['submission_file']
            )
            messages.success(request, 'Assignment submitted successfully!')
        
        return redirect('assignment_list', topic_id=assignment.topic.id)
    
    context = {
        'assignment': assignment,
        'existing_submission': existing_submission
    }
    return render(request, 'submit_assignment.html', context)