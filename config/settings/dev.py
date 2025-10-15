from .base import *

HUEY = {
    "huey_class": "huey.RedisHuey",
    "name": "app",
    "immediate_use_memory": False,
    "connection": {"url": env("REDIS_URL", default="redis://localhost:6379/0")},
}
