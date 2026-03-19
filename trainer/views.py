import json
from pathlib import Path

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from generator import load_or_generate_wordlist
from validator import DIGIT_TO_SOUNDS

from .models import QuizState

_wordlist = load_or_generate_wordlist()
_mapping = DIGIT_TO_SOUNDS


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_quiz_state(request):
    if request.user.is_authenticated:
        state, _ = QuizState.objects.get_or_create(user=request.user)
    else:
        ip = get_client_ip(request)
        state, _ = QuizState.objects.get_or_create(ip_address=ip, user__isnull=True)
    return state


@ensure_csrf_cookie
def index_view(request):
    return render(request, 'index.html')


@require_GET
def wordlist_view(request):
    return JsonResponse(_wordlist)


@require_GET
def mapping_view(request):
    return JsonResponse(_mapping)


_STATE_KEYS = {
    'score', 'quizScores', 'quizHistory', 'reverseScores', 'reverseHistory',
    'mixedScores', 'mixedHistory', 'conScores', 'conHistory', 'theme',
}


def state_view(request):
    state = get_quiz_state(request)

    if request.method == 'GET':
        return JsonResponse({
            'score': {'correct': state.score_correct, 'total': state.score_total},
            'quizScores': state.quiz_scores,
            'quizHistory': state.quiz_history,
            'reverseScores': state.reverse_scores,
            'reverseHistory': state.reverse_history,
            'mixedScores': state.mixed_scores,
            'mixedHistory': state.mixed_history,
            'conScores': state.con_scores,
            'conHistory': state.con_history,
            'theme': state.theme,
            'user': request.user.username if request.user.is_authenticated else None,
            'updatedAt': state.updated_at.isoformat() if state.updated_at else None,
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if not isinstance(data, dict):
            return JsonResponse({'error': 'Expected JSON object'}, status=400)

        if not data.keys() & _STATE_KEYS:
            return JsonResponse({'error': 'No recognized keys'}, status=400)

        if 'score' in data and isinstance(data['score'], dict):
            state.score_correct = data['score'].get('correct', state.score_correct)
            state.score_total = data['score'].get('total', state.score_total)
        if 'quizScores' in data:
            state.quiz_scores = data['quizScores']
        if 'quizHistory' in data:
            state.quiz_history = data['quizHistory']
        if 'reverseScores' in data:
            state.reverse_scores = data['reverseScores']
        if 'reverseHistory' in data:
            state.reverse_history = data['reverseHistory']
        if 'mixedScores' in data:
            state.mixed_scores = data['mixedScores']
        if 'mixedHistory' in data:
            state.mixed_history = data['mixedHistory']
        if 'conScores' in data:
            state.con_scores = data['conScores']
        if 'conHistory' in data:
            state.con_history = data['conHistory']
        if 'theme' in data:
            state.theme = data['theme']

        state.save()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    username = request.POST.get('username', '').strip().lower()
    password = request.POST.get('password', '')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('/')
    return render(request, 'login.html', {'error': 'Invalid username or password.'})


@require_POST
def register_view(request):
    username = request.POST.get('username', '').strip().lower()
    password = request.POST.get('password', '')
    password2 = request.POST.get('password2', '')

    if not username or not password:
        return render(request, 'login.html', {'reg_error': 'Username and password are required.'})
    if password != password2:
        return render(request, 'login.html', {'reg_error': 'Passwords do not match.'})
    if User.objects.filter(username__iexact=username).exists():
        return render(request, 'login.html', {'reg_error': 'Username already taken.'})

    user = User.objects.create_user(username=username, password=password)
    login(request, user)

    # Merge IP-based state into the new user account
    ip = get_client_ip(request)
    ip_state = QuizState.objects.filter(ip_address=ip, user__isnull=True).first()
    if ip_state:
        ip_state.user = user
        ip_state.ip_address = None
        ip_state.save()

    return redirect('/')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('/')
