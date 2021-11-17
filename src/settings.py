import os
import logging
import logging.config

from pydantic import BaseSettings


class Settings(BaseSettings):
    api_prefix: str
    debug: str
    logger_config: str
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    access_token_expire_minutes: str
    app_password: str
    secret_key: str
    algorithm: str


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
basic_env_file, local_env_file = ".env", ".env.local"
local_env_file_path = os.path.join(project_root, local_env_file)
is_local_env_file_exist = os.path.isfile(local_env_file_path)
env_file = local_env_file if is_local_env_file_exist else basic_env_file


settings = Settings(
    _env_file=env_file,
    _env_file_encoding="utf-8"
)


# Logger settings
# logging.config.fileConfig(settings.logger_config)
