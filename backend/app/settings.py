from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    provider: str = Field('mock', validation_alias='FIELDFIX_PROVIDER', pattern='^(mock|meta)$')
    api_key: str = Field('', validation_alias='MODEL_API_KEY', repr=False)
    base_url: str = Field('https://api.meta.ai/v1', validation_alias='META_BASE_URL')
    model: str = Field('muse-spark-1.3', validation_alias='META_MODEL')
    reasoning_effort: str = Field('low', validation_alias='META_REASONING_EFFORT', pattern='^(minimal|low|medium|high|xhigh)$')
    db: str = Field('.data/fieldfix.sqlite', validation_alias='FIELDFIX_DB')
    live_limit: int = Field(30, validation_alias='FIELDFIX_LIVE_REQUEST_LIMIT', ge=0, le=1000)
    enable_demo: bool = Field(True, validation_alias='FIELDFIX_ENABLE_DEMO')
