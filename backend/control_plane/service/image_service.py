from backend.control_plane.db.repositories.neuro_image import NeuroImageRepository


class ImageService:
    def __init__(self):
        self.repo = NeuroImageRepository()

    def neuroimages_by(self, ):
        pass

_image_service = ImageService()


def get_image_service():
    return _image_service
