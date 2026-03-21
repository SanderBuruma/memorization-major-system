from django.db import models
from django.contrib.auth.models import User


class QuizState(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)

    score_correct = models.IntegerField(default=0)
    score_total = models.IntegerField(default=0)

    quiz_scores = models.JSONField(default=dict)
    quiz_history = models.JSONField(default=list)
    reverse_scores = models.JSONField(default=dict)
    reverse_history = models.JSONField(default=list)
    mixed_scores = models.JSONField(default=dict)
    mixed_history = models.JSONField(default=list)
    con_scores = models.JSONField(default=dict)
    con_history = models.JSONField(default=list)
    custom_words = models.JSONField(default=dict)

    activity_log = models.JSONField(default=dict)
    tutorial_seen = models.BooleanField(default=False)
    dyslexia_font = models.BooleanField(default=False)
    theme = models.CharField(max_length=20, default='dark')
    updated_at = models.DateTimeField(auto_now=True)
