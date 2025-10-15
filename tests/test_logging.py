import pytest

from billing.models import ProviderRateCard
from domains.models import Client
from prompts.models import ModelConfig, PromptTemplate, Provider


@pytest.mark.story("S-020")
def test_prompt_run_logged_with_feedback(django_user_model):
    user = django_user_model.objects.create_user(username="logger", password="pw")
    client = Client.objects.create(name="Loggers", owner=user)
    wallet = client.wallet
    wallet.top_up(500)

    provider = Provider.objects.create(name="Anthropic")
    model = ModelConfig.objects.create(provider=provider, name="claude-3", input_cost_per_1k=0.0, output_cost_per_1k=0.0)
    rate_card = ProviderRateCard.objects.create(model=model, input_cost_per_1k_cents=100, output_cost_per_1k_cents=100)
    template = PromptTemplate.objects.create(name="logger", body="Hello {{ name }}", provider=provider, model=model, rate_card=rate_card)

    run = template.log_prompt_run(
        wallet=wallet,
        rate_card=rate_card,
        user=user,
        client=client,
        prompt_text="Hello Alice",
        response_text="Hi Alice",
        tokens_in=500,
        tokens_out=500,
    )

    run.attach_feedback(rating=5, feedback="Great response")
    usage = run.usage_log
    usage.refresh_from_db()
    assert usage.rating == 5
    assert "Great" in usage.feedback
