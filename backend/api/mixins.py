from rest_framework.permissions import SAFE_METHODS

class MultiSerializerMixin:
    """Миксин для выбора сериалайзера из словаря `serializer_classes`."""

    serializer_classes = None

    def get_serializer_class(self):
        """Возвращает сериалайзер из словаря `serializers_classes`, соответсвующий действию."""
        try:
            if self.action in self.serializer_classes.keys():
                return self.serializer_classes[self.action]
            if self.request.method in SAFE_METHODS:
                return self.serializer_classes['read']
            return self.serializer_classes['write']
        except KeyError:
            return super().get_serializer_class()
