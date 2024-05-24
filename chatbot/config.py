from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    line_channel_access_token: SecretStr
    line_channel_secret: SecretStr
    openai_api_key: SecretStr
    data_path: str = "../data/embed/data.csv"
    system_prompt: str = "You are a helpful assistant."
    openai_model: str = "gpt-3.5-turbo"
    openai_temp: int = 0


config = Config()
