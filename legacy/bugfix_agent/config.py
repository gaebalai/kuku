"""Configuration management for Bugfix Agent v5

This module provides configuration loading and access functions:
- load_config: Load config.toml with caching
- get_config_value: Access nested config values via dot notation
- get_workdir: Get the working directory with fallbacks
"""

import os
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

# Default config path (relative to this file's parent directory)
CONFIG_PATH = Path(__file__).parent.parent / "config.toml"


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
 """설정파일를읽어들이는(캐시付き)

 환경변수 BUGFIX_AGENT_CONFIG 로 경로를덮어쓰기가능.
 파일이존재하지 않는다경우는空の辞書를 반환하다.
 """
 config_path = Path(os.environ.get("BUGFIX_AGENT_CONFIG", CONFIG_PATH))
 if config_path.exists():
 return tomllib.loads(config_path.read_text(encoding="utf-8"))
 return {}


def get_config_value(key_path: str, default: Any = None) -> Any:
 """ドット記法로 설정값를취득한다

 Args:
 key_path: "agent.max_loop_count" 와 같은ドット区切り의 키경로
 default: 키이존재하지 않는다경우의기본값값
 """
 config = load_config()
 keys = key_path.split(".")
 value = config
 for key in keys:
 if isinstance(value, dict) and key in value:
 value = value[key]
 else:
 return default
 return value


def get_workdir() -> Path:
 """작업디렉토리를취득한다

 우선順位:
 1. 환경변수 BUGFIX_AGENT_WORKDIR
 2. config.toml 의 agent.workdir
 3. 리포지토리루트를자동検出(이파일의4階계층上)
 """
 env_workdir = os.environ.get("BUGFIX_AGENT_WORKDIR")
 if env_workdir:
 return Path(env_workdir)

 config_workdir = get_config_value("agent.workdir", "")
 if config_workdir:
 return Path(config_workdir)

 # bugfix_agent/config.py -> bugfix_agent -> repo_root
 return Path(__file__).parents[1]
