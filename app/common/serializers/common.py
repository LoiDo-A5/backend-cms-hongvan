from rest_framework import serializers


class ChoiceFieldSerializer(serializers.ChoiceField):
    def to_representation(self, key):
        return {'key': key, 'value': self.choices.get(key, None)}
