from .base import BaseRepository
from ..models.neuro_image import NeuroImage


class NeuroImageRepository(BaseRepository[NeuroImage]):
    def __init__(self):
        super().__init__(NeuroImage)
