import pytest
from prompts.models import PromptTemplate, Provider, ModelConfig
@pytest.mark.story("S-017")
def test_template_renders_with_vars(db):
    prov = Provider.objects.create(name="OpenAI")
    model = ModelConfig.objects.create(provider=prov, name="gpt-4o", input_cost_per_1k=0.0, output_cost_per_1k=0.0)
    pt = PromptTemplate.objects.create(name="hello", body="Hi {{ name }}", provider=prov, model=model)
    from django.template import Template, Context
    out = Template(pt.body).render(Context({"name":"Alice"}))
    assert "Alice" in out


@pytest.mark.story("S-017")
def test_template_retrieval_params(db):
    prov = Provider.objects.create(name="Anthropic")
    model = ModelConfig.objects.create(provider=prov, name="claude", input_cost_per_1k=0.0, output_cost_per_1k=0.0)
    pt = PromptTemplate.objects.create(name="contextual", body="{{ prompt }}", provider=prov, model=model, retrieval_k=5, retrieval_min_score=0.2)
    params = pt.retrieval_params()
    assert params == {"k": 5, "min_score": 0.2}
