#!/usr/bin/python
import secrets
import time
from servers import service
from configs import services_config


class SleepCpuService(service.Service):
    def __init__(self):
        super().__init__()

    def _onUpdate(self):
        time.sleep(services_config.INTERVALS_SECOND +
                   secrets.choice([-1, 1]) * secrets.randbelow(services_config.INTERVALS_RAND_MAX))
