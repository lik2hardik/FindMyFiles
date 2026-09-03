from backend import config


def test_config_loads_llm_api_key():
    """Test that LLM_API_KEY is loaded (may be None if no env var set)."""
    assert hasattr(config, "LLM_API_KEY")
    if config.LLM_API_KEY:
        assert isinstance(config.LLM_API_KEY, str)


def test_config_loads_llm_base_url():
    """Test that LLM_BASE_URL is loaded with a default value."""
    assert config.LLM_BASE_URL
    assert isinstance(config.LLM_BASE_URL, str)


def test_config_loads_llm_vision_model():
    """Test that LLM_VISION_MODEL is loaded with a default value."""
    assert config.LLM_VISION_MODEL
    assert isinstance(config.LLM_VISION_MODEL, str)


def test_config_loads_llm_audio_model():
    """Test that LLM_AUDIO_MODEL is loaded with a default value."""
    assert config.LLM_AUDIO_MODEL
    assert isinstance(config.LLM_AUDIO_MODEL, str)
