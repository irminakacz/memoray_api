from django.contrib.auth.models import User
from api.models import Deck, Card, Review
from api.serializers import UserSerializer, DeckSerializer, CardSerializer, ReviewSerializer

from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def create(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(card_id=request.data['card'])
            card = Card.objects.get(pk=request.data['card'])
            card.review(request.data['answer_quality'])
            card.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer


class DeckViewSet(viewsets.ModelViewSet):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
