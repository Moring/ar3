from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.template import Context, Template

User = get_user_model()


class Provider(models.Model):
    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField(blank=True)
    api_key_ref = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class ModelConfig(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="models")
    name = models.CharField(max_length=100)
    input_cost_per_1k = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    output_cost_per_1k = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    class Meta:
        unique_together = ("provider", "name")

    def __str__(self):
        return f"{self.provider.name}:{self.name}"


class PromptTemplate(models.Model):
    name = models.CharField(max_length=150, unique=True)
    body = models.TextField()
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, null=True, blank=True, related_name="templates")
    model = models.ForeignKey(ModelConfig, on_delete=models.PROTECT, null=True, blank=True, related_name="templates")
    rate_card = models.ForeignKey("billing.ProviderRateCard", on_delete=models.SET_NULL, null=True, blank=True, related_name="templates")
    retrieval_k = models.PositiveSmallIntegerField(default=3)
    retrieval_min_score = models.FloatField(default=0.0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def render(self, *, variables: Optional[Dict[str, Any]] = None, extra_context: Optional[Dict[str, Any]] = None) -> str:
        context = {}
        if variables:
            context.update(variables)
        if extra_context:
            context.update(extra_context)
        template = Template(self.body)
        return template.render(Context(context))

    def retrieval_params(self) -> Dict[str, Any]:
        return {"k": self.retrieval_k, "min_score": self.retrieval_min_score}

    def resolve_rate_card(self):
        from billing.models import ProviderRateCard

        if self.rate_card:
            return self.rate_card
        if self.model:
            try:
                return ProviderRateCard.objects.get(model=self.model)
            except ProviderRateCard.DoesNotExist:
                return None
        return None

    def log_prompt_run(
        self,
        *,
        wallet,
        rate_card=None,
        user,
        client,
        prompt_text: str,
        response_text: str,
        tokens_in: int,
        tokens_out: int,
        metadata: Optional[Dict[str, Any]] = None,
        retrieved_chunks: Optional[Iterable[dict]] = None,
    ):
        from billing.models import LLMUsageLog

        rate_card = rate_card or self.resolve_rate_card()
        if rate_card is None:
            raise ValueError("A rate card is required to log usage.")

        usage = LLMUsageLog.record_usage(
            wallet=wallet,
            rate_card=rate_card,
            template=self,
            user=user,
            client=client,
            prompt_text=prompt_text,
            response_text=response_text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            metadata=metadata,
        )
        return PromptRun.objects.create(
            template=self,
            usage_log=usage,
            retrieved_context=list(retrieved_chunks or []),
            rendered_prompt=prompt_text,
        )


class PromptRun(models.Model):
    template = models.ForeignKey(PromptTemplate, on_delete=models.CASCADE, related_name="runs")
    usage_log = models.OneToOneField("billing.LLMUsageLog", on_delete=models.CASCADE, related_name="prompt_run")
    rendered_prompt = models.TextField()
    retrieved_context = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def attach_feedback(self, rating: Optional[int] = None, feedback: str = ""):
        self.usage_log.attach_feedback(rating=rating, feedback=feedback)
