from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User

from api.models import Deck, Card, Review
from api.serializers import UserSerializer, DeckSerializer, CardSerializer, ReviewSerializer

from rest_framework.test import APIClient
import json


class CardModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.deck = Deck.objects.create(name="deck1", user=self.user)
        self.card1 = Card.objects.create(
            front="front1", back="back1", deck=self.deck)
        self.card2 = Card.objects.create(
            front="front2", back="back2", deck=self.deck, interval=6)
        self.card3 = Card.objects.create(
            front="front3", back="back2", deck=self.deck, interval=30)

    def test_if_default_last_review_date_is_empty(self):
        self.assertEqual(self.card1.last_review_date(), None)

    def test_if_default_times_reviewed_is_zero(self):
        self.assertEqual(self.card1.times_reviewed(), 0)

    def test_if_new_card_is_due(self):
        self.assertEqual(self.card1.is_due, True)

    def test_if_new_easiness_factor_is_calculated_correctly(self):
        self.assertEqual(self.card1.new_easiness_factor(0), 1.7)
        self.assertEqual(self.card1.new_easiness_factor(1), 1.96)
        self.assertEqual(self.card1.new_easiness_factor(2), 2.18)
        self.assertEqual(self.card1.new_easiness_factor(3), 2.36)
        self.assertEqual(self.card1.new_easiness_factor(4), 2.5)
        self.assertEqual(self.card1.new_easiness_factor(5), 2.5)

    def test_if_new_interval_is_calculated_correctly(self):
        self.assertEqual(self.card2.new_interval(1.5), 9)
        self.assertEqual(self.card3.new_interval(0.86), 25)


class CardReviewIntegrationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.deck = Deck.objects.create(name="deck1", user=self.user)
        self.card = Card.objects.create(
            front="front1", back="back1", deck=self.deck)

    def test_if_times_reviewed_updated_after_each_review(self):
        Review.objects.create(card=self.card, answer_quality=2)
        self.assertEqual(self.card.times_reviewed(), 1)
        Review.objects.create(card=self.card, answer_quality=3)
        Review.objects.create(card=self.card, answer_quality=1)
        self.assertEqual(self.card.times_reviewed(), 3)

    def test_if_last_review_date_equals_last_review_date(self):
        review1 = Review.objects.create(card=self.card, answer_quality=2)
        review2 = Review.objects.create(card=self.card, answer_quality=4)
        self.assertEqual(self.card.last_review_date(),
                         review2.review_date)

    def test_if_easiness_factor_not_updated_until_third_review(self):
        review = Review.objects.create(card=self.card, answer_quality=4)
        self.card.review(review.answer_quality)
        review = Review.objects.create(card=self.card, answer_quality=3)
        self.card.review(review.answer_quality)
        review = Review.objects.create(card=self.card, answer_quality=1)
        self.card.review(review.answer_quality)
        self.assertNotEqual(self.card.easiness_factor, 2.5)

    def test_if_interval_gets_updated_by_review(self):
        review = Review.objects.create(card=self.card, answer_quality=2)
        self.card.review(review.answer_quality)
        self.assertNotEqual(self.card.interval, 0)

    def test_if_card_is_due_immediately_after_review(self):
        review = Review.objects.create(card=self.card, answer_quality=4)
        self.card.review(review.answer_quality)
        self.assertEqual(self.card.is_due, False)


class DeckCardIntegrationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.deck1 = Deck.objects.create(name="deck1", user=self.user)
        self.deck2 = Deck.objects.create(name="deck2", user=self.user)
        Card.objects.create(front="front1", back="back1", deck=self.deck1)
        Card.objects.create(front="front2", back="back2", deck=self.deck1)
        Card.objects.create(front="front3", back="back3", deck=self.deck1)
        Card.objects.create(front="front4", back="back4", deck=self.deck2)

    def test_if_cards_include_all_cards_of_given_deck(self):
        self.assertEqual(self.deck1.cards.all().count(), 3)
        self.assertEqual(self.deck2.cards.all().count(), 1)


class UserSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")

    def test_if_user_serializer_produce_desired_output(self):
        serializer = UserSerializer(self.user)
        desired_output = {
            "id": self.user.id,
            "username": self.user.username,
            "decks": []
        }
        self.assertEqual(serializer.data, desired_output)


class DeckSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.deck = Deck.objects.create(name="deck1", user=self.user)

    def test_if_deck_serializer_produce_desired_output(self):
        serializer = DeckSerializer(self.deck)
        desired_output = {
            "id": self.deck.id,
            "name": "deck1",
            "user": self.user.id,
            "cards": []
        }
        self.assertEqual(serializer.data, desired_output)


class CardSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.deck = Deck.objects.create(name="deck1", user=self.user)
        self.card = Card.objects.create(
            front="front1", back="back1", deck=self.deck)

    def test_if_card_serializer_produce_desired_output(self):
        serializer = CardSerializer(self.card)
        desired_output = {
            "id": self.card.id,
            "front": "front1",
            "back": "back1",
            "is_due": True,
            "deck": self.deck.id
        }
        self.assertEqual(serializer.data, desired_output)


class ReviewSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.deck = Deck.objects.create(name="deck1", user=self.user)
        self.card = Card.objects.create(
            front="front1", back="back1", deck=self.deck)
        self.review = Review.objects.create(card=self.card, answer_quality=4)

    def test_if_review_serializer_produce_desired_output(self):
        review = Review.objects.get(card=self.card)
        serializer = ReviewSerializer(self.review)
        desired_output = {
            "id": self.review.id,
            "review_date":
            (self.review.review_date).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "answer_quality": 4,
            "card": self.card.id
        }
        self.assertEqual(serializer.data, desired_output)


class UserViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.client = APIClient()

    def test_getting_all_users(self):
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)

    def test_getting_one_user(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/users/' + str(self.user1.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['username'], "user1")

    def test_deleting_user(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete('/users/' + str(self.user2.id) + '/')
        self.assertEqual(response.status_code, 204)
        response = self.client.get('/users/' + str(self.user2.id) + '/')
        self.assertEqual(response.status_code, 404)

    def test_patching_user(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch('/users/' + str(self.user1.id) + '/',
                                content_type='application/json',
                                data='{"password": "new_password"}')
        self.assertEqual(response.status_code, 201)

    def test_creating_user(self):
        user_data = {
            "username": "user3",
            "password": "password1"
        }
        response = self.client.post('/users/', content_type='application/json',
                                data=json.dumps(user_data))
        user3 = User.objects.get(username="user3");
        self.client.force_authenticate(user=user3)
        response = self.client.get('/users/' + str(user3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['username'], "user3")


class DeckViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.deck1 = Deck.objects.create(name="deck1", user=self.user1)
        self.deck2 = Deck.objects.create(name="deck2", user=self.user1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    def test_getting_all_decks(self):
        response = self.client.get('/decks/')
        self.assertEqual(response.status_code, 200)

    def test_getting_one_deck(self):
        response = self.client.get('/decks/' + str(self.deck1.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['name'], "deck1")

    def test_deleting_deck(self):
        response = self.client.delete('/decks/' + str(self.deck2.id) + '/')
        self.assertEqual(response.status_code, 204)
        response = self.client.get('/decks/' + str(self.deck2.id) + '/')
        self.assertEqual(response.status_code, 404)

    def test_patching_deck(self):
        response = self.client.patch('/decks/' + str(self.deck1.id) + '/',
                                content_type='application/json',
                                data='{"name": "new_name"}')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['name'], "new_name")

    def test_creating_deck(self):
        deck_data = {
            "name": "deck3"
        }
        response = self.client.post('/decks/', content_type='application/json',
                                data=json.dumps(deck_data))
        deck3 = Deck.objects.get(name="deck3");
        response = self.client.get('/decks/' + str(deck3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['name'], "deck3")


class CardViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.deck = Deck.objects.create(name="deck1", user=self.user)
        self.card1 = Card.objects.create(
            front="front1", back="back1", deck=self.deck)
        self.card2 = Card.objects.create(
            front="front2", back="back2", deck=self.deck)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_getting_all_cards(self):
        response = self.client.get('/cards/')
        self.assertEqual(response.status_code, 200)

    def test_getting_card(self):
        response = self.client.get('/cards/' + str(self.card1.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['front'], "front1")

    def test_deleting_card(self):
        response = self.client.delete('/cards/' + str(self.card2.id) + '/')
        self.assertEqual(response.status_code, 204)
        response = self.client.get('/cards/' + str(self.card2.id) + '/')
        self.assertEqual(response.status_code, 404)

    def test_patching_card(self):
        response = self.client.patch('/cards/' + str(self.card1.id) + '/',
                                content_type='application/json',
                                data='{"front": "new_front"}')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['front'], "new_front")

    def test_creating_card(self):
        card_data = {
            "front": "front3",
            "back": "back3",
            "deck": self.deck.id
        }
        response = self.client.post('/cards/', content_type='application/json',
                                data=json.dumps(card_data))
        card3 = Card.objects.get(front="front3");
        response = self.client.get('/cards/' + str(card3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['front'], "front3")

class ReviewViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.deck = Deck.objects.create(name="deck1", user=self.user)
        self.card1 = Card.objects.create(
            front="front1", back="back1", deck=self.deck)
        self.card2 = Card.objects.create(
            front="front2", back="back2", deck=self.deck)
        self.card3 = Card.objects.create(
            front="front3", back="back3", deck=self.deck)
        self.review11 = Review.objects.create(card=self.card1, answer_quality=2)
        self.review12 = Review.objects.create(card=self.card1, answer_quality=5)
        self.review21 = Review.objects.create(card=self.card2, answer_quality=3)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_getting_all_reviews(self):
        response = self.client.get('/reviews/')
        self.assertEqual(response.status_code, 200)

    def test_getting_card(self):
        response = self.client.get('/reviews/' + str(self.review21.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['answer_quality'], 3)

    def test_creating_review(self):
        review_data = {
            "card": self.card2.id,
            "answer_quality": 1
        }
        response = self.client.post('/reviews/', content_type='application/json',
                                data=json.dumps(review_data))
        self.assertEqual(response.status_code, 200)
        review22 = Review.objects.get(answer_quality=1)
        response = self.client.get('/reviews/' + str(review22.id) + '/')
        self.assertEqual(response.status_code, 200)

    def test_is_card_reviewed_after_creating_new_review(self):
        response = self.client.get('/cards/' + str(self.card3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['is_due'], True)

        review_data = {
            "card": self.card3.id,
            "answer_quality": 1
        }
        response = self.client.post('/reviews/', content_type='application/json',
                                data=json.dumps(review_data))
        self.assertEqual(response.status_code, 200)
        review22 = Review.objects.get(answer_quality=1)
        response = self.client.get('/reviews/' + str(review22.id) + '/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/cards/' + str(self.card3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['is_due'], False)


