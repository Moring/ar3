import pytest
from llm_gateway.safety import check_prompt_safe

@pytest.mark.story("S-021")
def test_flagged_prompt_blocked():
    ok, reason = check_prompt_safe("please DROP TABLE users;")
    assert not ok
    assert reason

@pytest.mark.story("S-021")
def test_safe_prompt_passes():
    ok, reason = check_prompt_safe("hello world")
    assert ok
