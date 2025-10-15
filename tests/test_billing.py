import pytest
from django.utils import timezone

from billing.models import ProviderRateCard, Subscription
from domains.models import Client
from prompts.models import ModelConfig, PromptTemplate, Provider


@pytest.fixture
def client_wallet(db, django_user_model):
    owner = django_user_model.objects.create_user(username="owner", password="pw")
    client = Client.objects.create(name="Acme", owner=owner)
    wallet = client.wallet
    wallet.top_up(10_00)  # $10 -> 1000 cents
    return client, wallet, owner


@pytest.fixture
def rate_card(db):
    provider = Provider.objects.create(name="OpenAI")
    model = ModelConfig.objects.create(provider=provider, name="gpt-4o", input_cost_per_1k=0.0, output_cost_per_1k=0.0)
    return ProviderRateCard.objects.create(model=model, input_cost_per_1k_cents=100, output_cost_per_1k_cents=200)


@pytest.mark.story("S-005")
def test_subscription_active_on_webhook(db, client_wallet):
    client, _, _ = client_wallet
    sub = Subscription.objects.create(client=client, stripe_customer_id="cus_123", stripe_subscription_id="sub_123")
    future = timezone.now() + timezone.timedelta(days=30)
    sub.mark_active(future)
    sub.refresh_from_db()
    assert sub.status == "active"
    assert sub.current_period_end == future


@pytest.mark.story("S-005")
def test_wallet_topup_flow(client_wallet):
    client, wallet, _ = client_wallet
    starting = wallet.balance_cents
    wallet.top_up(5_00, reference="invoice_1")
    wallet.refresh_from_db()
    assert wallet.balance_cents == starting + 500
    entry = wallet.entries.first()
    assert entry.reference == "invoice_1"


@pytest.mark.story("S-005")
def test_wallet_debit_on_ai_call(client_wallet, rate_card):
    client, wallet, owner = client_wallet
    template = PromptTemplate.objects.create(name="welcome", body="Hello {{ name }}", provider=rate_card.model.provider, model=rate_card.model, rate_card=rate_card)
    tokens_in, tokens_out = 1000, 500
    run = template.log_prompt_run(
        wallet=wallet,
        rate_card=rate_card,
        user=owner,
        client=client,
        prompt_text="Hello Alice",
        response_text="Hi there",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        metadata={"model": template.model.name},
    )
    wallet.refresh_from_db()
    expected_cost = rate_card.cost_for_usage(tokens_in, tokens_out)
    assert wallet.balance_cents == 1000 - expected_cost
    usage = run.usage_log
    assert usage.cost_cents == expected_cost
    assert usage.metadata["model"] == template.model.name
