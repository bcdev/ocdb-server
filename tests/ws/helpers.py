import os
from typing import Optional

import yaml

from eocdb.core.service import Service
from eocdb.ws.context import WsContext
from eocdb.ws.reqparams import RequestParams


def new_test_service_context() -> WsContext:
    ctx = WsContext(base_dir=get_test_res_dir())
    config_file = os.path.join(ctx.base_dir, 'config.yml')
    with open(config_file) as fp:
        ctx.configure(yaml.load(fp))
    return ctx


def get_test_res_dir() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), 'res'))


class RequestParamsMock(RequestParams):
    def __init__(self, **kvp):
        self.kvp = kvp

    def get_query_argument(self, name: str, default: Optional[str]) -> Optional[str]:
        return self.kvp.get(name, default)


class DatabaseTestDriver(Service):

    def init(self, **config):
        super().init(**config)

    def update(self, **config):
        super().update(**config)

    def dispose(self):
        super().dispose()
