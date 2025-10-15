from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from domains.models import Client


CENTS = Decimal("0.01")


class Subscription(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="subscriptions")
    stripe_customer_id = models.CharField(max_length=120)
    stripe_subscription_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=40, default="incomplete")
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("client", "stripe_subscription_id")

    def mark_active(self, current_period_end: Optional[timezone.datetime] = None):
        self.status = "active"
        if current_period_end:
            self.current_period_end = current_period_end
        self.save(update_fields=["status", "current_period_end", "updated_at"])

    def cancel(self):
        self.status = "canceled"
        self.save(update_fields=["status", "updated_at"])


class Wallet(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="wallet")
    balance_cents = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} wallet ({self.balance_cents}¢)"

    @transaction.atomic
    def _record_entry(self, delta_cents: int, reason: str, reference: Optional[str] = None, metadata: Optional[dict] = None):
        if delta_cents == 0:
            raise ValidationError("Wallet entry delta cannot be zero.")

        wallet = Wallet.objects.select_for_update().get(pk=self.pk)
        new_balance = wallet.balance_cents + delta_cents
        if new_balance < 0:
            raise ValidationError("Insufficient wallet balance.")
        wallet.balance_cents = new_balance
        wallet.save(update_fields=["balance_cents", "updated_at"])
        self.refresh_from_db(fields=["balance_cents", "updated_at"])
        return WalletLedger.objects.create(wallet=self, delta_cents=delta_cents, balance_after=new_balance, reason=reason or "", reference=reference or "", metadata=metadata or {})

    def top_up(self, amount_cents: int, reference: Optional[str] = None, metadata: Optional[dict] = None):
        if amount_cents <= 0:
            raise ValidationError("Top up amount must be positive.")
        return self._record_entry(amount_cents, "top_up", reference, metadata)

    def debit(self, amount_cents: int, reference: Optional[str] = None, metadata: Optional[dict] = None):
        if amount_cents <= 0:
            raise ValidationError("Debit amount must be positive.")
        return self._record_entry(-amount_cents, "debit", reference, metadata)


class WalletLedger(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="entries")
    delta_cents = models.BigIntegerField()
    balance_after = models.BigIntegerField()
    reason = models.CharField(max_length=200)
    reference = models.CharField(max_length=120, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reason} ({self.delta_cents:+}¢)"


class ProviderRateCard(models.Model):
    model = models.ForeignKey("prompts.ModelConfig", on_delete=models.CASCADE, related_name="rate_cards")
    currency = models.CharField(max_length=3, default="USD")
    input_cost_per_1k_cents = models.PositiveIntegerField()
    output_cost_per_1k_cents = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("model", "currency")

    def cost_for_usage(self, tokens_in: int, tokens_out: int) -> int:
        """Return total cost in cents for token usage."""
        input_blocks = Decimal(tokens_in) / Decimal(1000)
        output_blocks = Decimal(tokens_out) / Decimal(1000)
        cost = (input_blocks * Decimal(self.input_cost_per_1k_cents) + output_blocks * Decimal(self.output_cost_per_1k_cents)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(cost)


class WalletInsufficient(Exception):
    """Raised when a wallet does not have enough balance for a debit."""


class LLMUsageLog(models.Model):
    STATUS_CHOICES = [
        ("success", "Success"),
        ("blocked", "Blocked"),
        ("error", "Error"),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="usage_logs")
    rate_card = models.ForeignKey(ProviderRateCard, on_delete=models.PROTECT, related_name="usage_logs")
    template = models.ForeignKey("prompts.PromptTemplate", on_delete=models.SET_NULL, null=True, blank=True, related_name="usage_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="usage_logs")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="usage_logs")
    prompt_text = models.TextField()
    response_text = models.TextField(blank=True)
    tokens_in = models.PositiveIntegerField(default=0)
    tokens_out = models.PositiveIntegerField(default=0)
    cost_cents = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="success")
    blocked_reason = models.CharField(max_length=255, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def record_usage(
        cls,
        *,
        wallet: Wallet,
        rate_card: ProviderRateCard,
        template,
        user,
        client: Client,
        prompt_text: str,
        response_text: str,
        tokens_in: int,
        tokens_out: int,
        metadata: Optional[dict] = None,
    ):
        amount_cents = rate_card.cost_for_usage(tokens_in, tokens_out)
        try:
            wallet.debit(amount_cents, reference="llm_usage", metadata={"template_id": getattr(template, "id", None)})
        except ValidationError as exc:
            raise WalletInsufficient(str(exc)) from exc

        return cls.objects.create(
            wallet=wallet,
            rate_card=rate_card,
            template=template,
            user=user,
            client=client,
            prompt_text=prompt_text,
            response_text=response_text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_cents=amount_cents,
            status="success",
            metadata=metadata or {},
        )

    def attach_feedback(self, rating: Optional[int] = None, feedback: str = ""):
        if rating is not None and not (1 <= rating <= 5):
            raise ValidationError("Rating must be between 1 and 5.")
        self.rating = rating
        self.feedback = feedback
        self.save(update_fields=["rating", "feedback"])
