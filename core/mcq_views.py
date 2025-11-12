from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .mcq import MCQQuestion, MCQTest, MCQTestQuestion
from .models import Topic
from django.db import transaction

@login_required
def start_mcq_test(request, topic_id):
    """
    Start a new MCQ test for the student
    """
    topic = get_object_or_404(Topic, id=topic_id)
    
    # Check if there's an incomplete test
    existing_test = MCQTest.objects.filter(
        student=request.user,
        topic=topic,
        is_completed=False
    ).first()
    
    if existing_test:
        return redirect('take_mcq_test', test_id=existing_test.id)
    
    # Create new test
    try:
        with transaction.atomic():
            test = MCQTest.objects.create(
                student=request.user,
                topic=topic
            )
            test.generate_test(num_questions=15)
        return redirect('take_mcq_test', test_id=test.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('topic_detail', topic_id=topic_id)

@login_required
def take_mcq_test(request, test_id):
    """
    Display and handle MCQ test
    """
    test = get_object_or_404(MCQTest, id=test_id, student=request.user)
    
    if test.is_completed:
        return redirect('mcq_test_result', test_id=test.id)
    
    if request.method == 'POST':
        for question in test.mcqtestquestion_set.all():
            answer = request.POST.get(f'question_{question.id}')
            if answer:
                question.selected_option = int(answer)
                question.check_answer()
        
        test.calculate_score()
        return redirect('mcq_test_result', test_id=test.id)
    
    context = {
        'test': test,
        'questions': test.mcqtestquestion_set.all()
    }
    return render(request, 'mcq_test.html', context)

@login_required
def mcq_test_result(request, test_id):
    """
    Display MCQ test results
    """
    test = get_object_or_404(MCQTest, id=test_id, student=request.user)
    if not test.is_completed:
        return redirect('take_mcq_test', test_id=test.id)
    
    context = {
        'test': test,
        'questions': test.mcqtestquestion_set.all()
    }
    return render(request, 'mcq_result.html', context)