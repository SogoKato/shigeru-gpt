from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    line_channel_access_token: SecretStr
    line_channel_secret: SecretStr
    openai_api_key: SecretStr
    data_path: str = "../data/embed/datav2.csv"
    system_prompt: str = "You are a helpful assistant."
    openai_model: str = "gpt-4o-mini"
    openai_temp: int = 0
    max_history_per_conversation: int = 6


config = Config()
