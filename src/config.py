import os
import yaml
from functools import lru_cache
from dotenv import load_dotenv
from typing import Dict, Any

class EnvSettings:
    def __init__(self):
        # Required parameters
        self.infura_api_key = os.getenv('INFURA_API_KEY')
        self.drpc_api_key = os.getenv('DRPC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.db_uri = os.getenv('DB_URI')

        # Optional parameters
        self.proxy_host = os.getenv('PROXY_HOST')
        self.proxy_port = int(os.getenv('PROXY_PORT', 0))
        self.proxy_user = os.getenv('PROXY_USER', '')
        self.proxy_password = os.getenv('PROXY_PASSWORD', '')

        self._validate_required()

    def _validate_required(self):
        required = {
            'INFURA_API_KEY': self.infura_api_key,
            'DRPC_API_KEY': self.drpc_api_key,
            'OPENAI_API_KEY': self.openai_api_key,
            'DB_URI': self.db_uri,
        }

        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f'Missing required environment variables: {", ".join(missing)}')

class AppConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.general = config_data.get('general', {})
        self.blockchains = config_data.get('blockchains', {})
        self.database = config_data.get('database', {})
        self.paths = config_data.get('paths', {})
        self.openai = config_data.get('openai', {})
    
    @classmethod
    def from_yaml(cls, path: str):
        with open(path, 'r') as f:
            raw_config = yaml.safe_load(f)
        return cls(raw_config)

@lru_cache(maxsize=None)
def get_env_settings() -> EnvSettings:
    load_dotenv()
    return EnvSettings()

@lru_cache(maxsize=None)
def get_app_config(config_path: str = 'config.yaml') -> AppConfig:
    return AppConfig.from_yaml(config_path)