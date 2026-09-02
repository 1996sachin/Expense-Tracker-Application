from django.conf import settings
from django.db import models


class Goal(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_date = models.DateField(null=True, blank=True)
    linked_account = models.ForeignKey(
        'bankaccounts.BankAccount',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='goals'
    )
    icon = models.CharField(max_length=50, blank=True, default='🎯')
    color = models.CharField(max_length=20, blank=True, default='#6d5dfc')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.current_amount}/{self.target_amount})"
