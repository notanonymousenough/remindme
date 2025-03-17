from uvicorn.protocols.http.flow_control import service_unavailable

from backend.control_plane.config import get_settings
from backend.control_plane.service.reminders import RemindersService


class Context:
    services = [RemindersService]
    reminders_service = ...
    reminders_repository = ...
    db = ...

    # как вариант:
    def  __init__(self):
        self.settings = ...
        for service in services:
            service(repo)


    def get_reminders_service():
        if get_reminders_repository():
            ok
        raise ValueError

    def get_reminders_repository():
        if get_db():
            return ...
        raise ValueError

    def get_db(self):
        if get_settings():

class AbstractService:
    def __init__(self, repository):
        if not repository:
            raise ValueError
        self.repo = repository

    def get_repo(self):
        return self.repo