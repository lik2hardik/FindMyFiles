from backend import config


def test_config_loads_groq_key_from_dotenv_file():
    assert config.GROQ_KEY
    assert isinstance(config.GROQ_KEY, str)
    assert config.GROQ_KEY.startswith("gsk_")
