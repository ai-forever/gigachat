from gigachat.models.with_x_headers import WithXHeaders


class AssistantFileDelete(WithXHeaders):
    """Информация об удаленном файле"""

    file_id: str
    """Идентификатор прикрепленного к ассистенту файла"""
    deleted: bool
    """Признак удаления. Если true - файл удален из ассистента"""
