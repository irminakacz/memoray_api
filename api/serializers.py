from rest_framework import serializers
from api.models import Card, Review


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ('id', 'front', 'back', 'is_due')


class ReviewSerializer(serializers.ModelSerializer):
    card = serializers.ReadOnlyField(source="card.id")

    class Meta:
        model = Review
        fields = ('id', 'review_date', 'answer_quality', 'card')

