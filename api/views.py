from api.models import Card, Review
from api.serializers import CardSerializer, ReviewSerializer

from rest_framework import viewsets


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
