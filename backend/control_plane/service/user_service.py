from backend.control_plane.db.repositories.user import UserRepository


class UserService:
    def __init__(self):
        self.repo = UserRepository()


_user_service = UserService()


def get_user_service():
    return _user_service
