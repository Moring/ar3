import pytest
from prompts.models import Provider, ModelConfig, PromptTemplate
from billing.models import ProviderRateCard
@pytest.mark.story("S-018")
def test_set_model_on_template(db):
    prov = Provider.objects.create(name="OpenAI")
    model = ModelConfig.objects.create(provider=prov, name="gpt-4o-mini", input_cost_per_1k=0.0, output_cost_per_1k=0.0)
    pt = PromptTemplate.objects.create(name="t1", body="x", provider=prov, model=model)
    assert pt.model.name == "gpt-4o-mini"


@pytest.mark.story("S-018")
def test_rate_card_lookup(db):
    prov = Provider.objects.create(name="Anthropic")
    model = ModelConfig.objects.create(provider=prov, name="claude-sonnet", input_cost_per_1k=0.0, output_cost_per_1k=0.0)
    rate_card = ProviderRateCard.objects.create(model=model, input_cost_per_1k_cents=120, output_cost_per_1k_cents=240)
    pt = PromptTemplate.objects.create(name="rc", body="x", provider=prov, model=model)
    assert pt.resolve_rate_card() == rate_card
