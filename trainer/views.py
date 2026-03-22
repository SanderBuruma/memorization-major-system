import json
import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from trainer.generator import load_or_generate_wordlist, get_concrete_nouns, build_candidate_map
from trainer.validator import DIGIT_TO_SOUNDS, word_to_digits

from .models import QuizState

# Lazy-init singletons — never invalidated; the underlying WordNet data is
# static, so these stay valid for the lifetime of the process.
_wordlist: dict | None = None
_candidate_map: dict | None = None


def _get_wordlist():
    global _wordlist
    if _wordlist is None:
        _wordlist = load_or_generate_wordlist()
    return _wordlist


def _get_candidate_map():
    global _candidate_map
    if _candidate_map is None:
        _candidate_map = build_candidate_map(get_concrete_nouns())
    return _candidate_map


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
    return JsonResponse(_get_wordlist())


@require_GET
def mapping_view(request):
    return JsonResponse(DIGIT_TO_SOUNDS)


@require_POST
def encode_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    text = data.get('text', '')
    if not isinstance(text, str):
        return JsonResponse({'error': 'text must be a string'}, status=400)
    words = re.findall(r"[a-zA-Z]+", text)
    result = []
    for w in words:
        digits = word_to_digits(w)
        result.append({'word': w.lower(), 'digits': digits})
    return JsonResponse(result, safe=False)


_FIELD_MAP = {
    'quizScores': ('quiz_scores', dict),
    'quizHistory': ('quiz_history', list),
    'reverseScores': ('reverse_scores', dict),
    'reverseHistory': ('reverse_history', list),
    'mixedScores': ('mixed_scores', dict),
    'mixedHistory': ('mixed_history', list),
    'conScores': ('con_scores', dict),
    'conHistory': ('con_history', list),
    'customWords': ('custom_words', dict),
    'activityLog': ('activity_log', dict),
}
_STATE_KEYS = set(_FIELD_MAP) | {'score', 'theme', 'tutorialSeen', 'dyslexiaFont'}
MAX_STATE_PAYLOAD = 102_400  # 100 KB
_VALID_THEMES = {'dark', 'light', 'oled', 'high-contrast'}


def state_view(request):
    """GET returns all quiz state fields as JSON; POST accepts a partial update.

    Identifies the user by auth session (logged in) or IP address (anonymous).
    POST body is a JSON object with any subset of _STATE_KEYS; unrecognised
    keys are silently ignored.  Returns 413 if the payload exceeds
    MAX_STATE_PAYLOAD bytes.
    """
    state = get_quiz_state(request)

    if request.method == 'GET':
        response = {js_key: getattr(state, field) for js_key, (field, _) in _FIELD_MAP.items()}
        response.update({
            'score': {'correct': state.score_correct, 'total': state.score_total},
            'theme': state.theme,
            'tutorialSeen': state.tutorial_seen,
            'dyslexiaFont': state.dyslexia_font,
            'user': request.user.username if request.user.is_authenticated else None,
            'updatedAt': state.updated_at.isoformat() if state.updated_at else None,
        })
        return JsonResponse(response)

    if request.method == 'POST':
        if len(request.body) > MAX_STATE_PAYLOAD:
            return JsonResponse({'error': f'Payload too large (limit {MAX_STATE_PAYLOAD} bytes)'}, status=413)

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if not isinstance(data, dict):
            return JsonResponse({'error': 'Expected JSON object'}, status=400)

        if not data.keys() & _STATE_KEYS:
            return JsonResponse({'error': 'No recognized keys'}, status=400)

        for js_key, (model_field, expected_type) in _FIELD_MAP.items():
            if js_key in data and isinstance(data[js_key], expected_type):
                setattr(state, model_field, data[js_key])
        if 'score' in data and isinstance(data['score'], dict):
            correct = data['score'].get('correct', state.score_correct)
            total = data['score'].get('total', state.score_total)
            if isinstance(correct, int) and isinstance(total, int) and correct >= 0 and total >= 0:
                state.score_correct = correct
                state.score_total = total
        if 'theme' in data and data['theme'] in _VALID_THEMES:
            state.theme = data['theme']
        if 'tutorialSeen' in data and isinstance(data['tutorialSeen'], bool):
            state.tutorial_seen = data['tutorialSeen']
        if 'dyslexiaFont' in data and isinstance(data['dyslexiaFont'], bool):
            state.dyslexia_font = data['dyslexiaFont']

        state.save()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@require_GET
def candidates_view(request, digits):
    if not (len(digits) in (1, 2) and digits.isdigit()):
        return JsonResponse({'error': 'Invalid digits'}, status=400)
    candidates = _get_candidate_map().get(digits, [])
    return JsonResponse(sorted(candidates, key=lambda w: (len(w), w)), safe=False)


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
