import pytest

from billing.models import LLMUsageLog, ProviderRateCard, WalletInsufficient
from domains.models import Client
from prompts.models import ModelConfig, PromptTemplate, Provider


@pytest.fixture
def rate_card(db):
    provider = Provider.objects.create(name="Anthropic")
    model = ModelConfig.objects.create(provider=provider, name="claude", input_cost_per_1k=0.0, output_cost_per_1k=0.0)
    return ProviderRateCard.objects.create(model=model, input_cost_per_1k_cents=50, output_cost_per_1k_cents=100)


@pytest.mark.story("S-019")
def test_usage_log_created(rate_card, django_user_model):
    user = django_user_model.objects.create_user(username="usage", password="pw")
    client = Client.objects.create(name="Usage Corp", owner=user)
    wallet = client.wallet
    wallet.top_up(1000)
    template = PromptTemplate.objects.create(name="usage", body="{{ prompt }}", provider=rate_card.model.provider, model=rate_card.model, rate_card=rate_card)
    usage = LLMUsageLog.record_usage(
        wallet=wallet,
        rate_card=rate_card,
        template=template,
        user=user,
        client=client,
        prompt_text="Hello",
        response_text="Hi",
        tokens_in=500,
        tokens_out=500,
    )
    assert usage.cost_cents == rate_card.cost_for_usage(500, 500)
    assert LLMUsageLog.objects.count() == 1


@pytest.mark.story("S-019")
def test_wallet_debited_by_token_count(rate_card, django_user_model):
    user = django_user_model.objects.create_user(username="insufficient", password="pw")
    client = Client.objects.create(name="Budget", owner=user)
    wallet = client.wallet
    wallet.top_up(50)
    template = PromptTemplate.objects.create(name="budget", body="{{ prompt }}", provider=rate_card.model.provider, model=rate_card.model, rate_card=rate_card)
    with pytest.raises(WalletInsufficient):
        LLMUsageLog.record_usage(
            wallet=wallet,
            rate_card=rate_card,
            template=template,
            user=user,
            client=client,
            prompt_text="Hello",
            response_text="Hi",
            tokens_in=10_000,
            tokens_out=10_000,
        )
