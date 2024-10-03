class MultiSerializerMixin:
    """Миксин для выбора сериалайзера из словаря `serializer_classes`."""

    serializer_classes = None

    def get_serializer_class(self):
        """Возвращает сериалайзер.

        Выбирает из словаря `serializers_classes` сералайзер,
        соответсвующий действию, заданному в словаре.
        """
        try:
            return self.serializer_classes[self.action]
        except KeyError:
            return super().get_serializer_class()
