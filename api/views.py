from django.contrib.auth.models import User
from api.models import Deck, Card, Review
from api.serializers import UserSerializer, DeckSerializer, CardSerializer, ReviewSerializer

from rest_framework import permissions
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        decks = Deck.objects.filter(user=self.request.user)
        cards = Card.objects.filter(deck__in=decks)
        return Review.objects.filter(card__in=cards)

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
    serializer_class = CardSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        decks = Deck.objects.filter(user=self.request.user)
        return Card.objects.filter(deck__in=decks)


class DeckViewSet(viewsets.ModelViewSet):
    serializer_class = DeckSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Deck.objects.filter(user=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)
