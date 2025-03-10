from typing import List

from gigachat.models.uploaded_file import UploadedFile
from gigachat.models.with_x_headers import WithXHeaders


class UploadedFiles(WithXHeaders):
    data: List[UploadedFile]
    """Список загруженных файлов"""
