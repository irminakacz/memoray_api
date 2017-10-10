from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User

from api.models import Deck, Card, Review
from api.serializers import UserSerializer, DeckSerializer, CardSerializer, ReviewSerializer

import json


class CardModelTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="user1")
        deck = Deck.objects.create(name="deck1", user=user)
        Card.objects.create(front="front1", back="back1", deck=deck)
        Card.objects.create(front="front2", back="back2", deck=deck, interval=6)
        Card.objects.create(front="front3", back="back2", deck=deck, interval=30)

    def test_if_default_last_review_date_is_empty(self):
        card = Card.objects.get(front="front1")
        self.assertEqual(card.last_review_date(), None)

    def test_if_default_times_reviewed_is_zero(self):
        card = Card.objects.get(front="front1")
        self.assertEqual(card.times_reviewed(), 0)

    def test_if_new_card_is_due(self):
        card = Card.objects.get(front="front1")
        self.assertEqual(card.is_due, True)

    def test_if_new_easiness_factor_is_calculated_correctly(self):
        card = Card.objects.get(front="front1")
        self.assertEqual(card.new_easiness_factor(0), 1.7)
        self.assertEqual(card.new_easiness_factor(1), 1.96)
        self.assertEqual(card.new_easiness_factor(2), 2.18)
        self.assertEqual(card.new_easiness_factor(3), 2.36)
        self.assertEqual(card.new_easiness_factor(4), 2.5)
        self.assertEqual(card.new_easiness_factor(5), 2.5)

    def test_if_new_interval_is_calculated_correctly(self):
        card1 = Card.objects.get(front="front2")
        card2 = Card.objects.get(front="front3")
        self.assertEqual(card1.new_interval(1.5), 9)
        self.assertEqual(card2.new_interval(0.86), 25)


class CardReviewIntegrationTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="user1")
        deck = Deck.objects.create(name="deck1", user=user)
        Card.objects.create(front="front1", back="back1", deck=deck)

    def test_if_times_reviewed_updated_after_each_review(self):
        card = Card.objects.get(front="front1")
        Review.objects.create(card=card, answer_quality=2)
        self.assertEqual(card.times_reviewed(), 1)
        Review.objects.create(card=card, answer_quality=3)
        Review.objects.create(card=card, answer_quality=1)
        self.assertEqual(card.times_reviewed(), 3)

    def test_if_last_review_date_equals_last_review_date(self):
        card = Card.objects.get(front="front1")
        review = Review.objects.create(card=card, answer_quality=2)
        self.assertEqual(card.last_review_date(), review.review_date)

    def test_if_easiness_factor_not_gets_updated_until_third_review(self):
        card = Card.objects.get(front="front1")
        review = Review.objects.create(card=card, answer_quality=4)
        card.review(review.answer_quality)
        review = Review.objects.create(card=card, answer_quality=3)
        card.review(review.answer_quality)
        review = Review.objects.create(card=card, answer_quality=1)
        card.review(review.answer_quality)
        self.assertNotEqual(card.easiness_factor, 2.5)

    def test_if_interval_gets_updated_by_review(self):
        card = Card.objects.get(front="front1")
        review = Review.objects.create(card=card, answer_quality=2)
        card.review(review.answer_quality)
        self.assertNotEqual(card.interval, 0)

    def test_if_card_is_due_immediately_after_review(self):
        card = Card.objects.get(front="front1")
        review = Review.objects.create(card=card, answer_quality=4)
        card.review(review.answer_quality)
        self.assertEqual(card.is_due, False)


class DeckCardIntegrationTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="user1")
        deck1 = Deck.objects.create(name="deck1", user=user)
        deck2 = Deck.objects.create(name="deck2", user=user)
        Card.objects.create(front="front1", back="back1", deck=deck1)
        Card.objects.create(front="front2", back="back2", deck=deck1)
        Card.objects.create(front="front3", back="back3", deck=deck1)
        Card.objects.create(front="front4", back="back4", deck=deck2)

    def test_if_cards_include_all_cards_of_given_deck(self):
        deck1 = Deck.objects.get(name="deck1")
        deck2 = Deck.objects.get(name="deck2")
        self.assertEqual(deck1.cards.all().count(), 3)
        self.assertEqual(deck2.cards.all().count(), 1)


class UserSerializerTestCase(TestCase):
    def setUp(self):
        User.objects.create(username="user1")

    def test_if_user_serializer_produce_desired_output(self):
        user = User.objects.get(username="user1")
        serializer = UserSerializer(user)
        desired_output = {
            "id": user.id,
            "username": user.username,
            "decks": []
        }
        self.assertEqual(serializer.data, desired_output)


class DeckSerializerTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="user1")
        Deck.objects.create(name="deck1", user=user)

    def test_if_deck_serializer_produce_desired_output(self):
        user = User.objects.get(username="user1")
        deck = Deck.objects.get(name="deck1")
        serializer = DeckSerializer(deck)
        desired_output = {
            "id": deck.id,
            "name": "deck1",
            "user": user.id,
            "cards": []
        }
        self.assertEqual(serializer.data, desired_output)


class CardSerializerTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="user1")
        deck = Deck.objects.create(name="deck1", user=user)
        Card.objects.create(front="front1", back="back1", deck=deck)

    def test_if_card_serializer_produce_desired_output(self):
        deck = Deck.objects.get(name="deck1")
        card = Card.objects.get(front="front1")
        serializer = CardSerializer(card)
        desired_output = {
            "id": card.id,
            "front": "front1",
            "back": "back1",
            "is_due": True,
            "deck": deck.id
        }
        self.assertEqual(serializer.data, desired_output)


class ReviewSerializerTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="user1")
        deck = Deck.objects.create(name="deck1", user=user)
        card = Card.objects.create(front="front1", back="back1", deck=deck)
        Review.objects.create(card=card, answer_quality=4)

    def test_if_review_serializer_produce_desired_output(self):
        card = Card.objects.get(front="front1")
        review = Review.objects.get(card=card)
        serializer = ReviewSerializer(review)
        desired_output = {
            "id": review.id,
            "review_date":
            (review.review_date).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "answer_quality": 4,
            "card": card.id
        }
        self.assertEqual(serializer.data, desired_output)


class UserViewsTestCase(TestCase):
    def setUp(self):
        user1 = User.objects.create(username="user1")
        user2 = User.objects.create(username="user2")

    def test_getting_all_users(self):
        client = Client()
        response = client.get('/users/')
        self.assertEqual(response.status_code, 200)

    def test_getting_one_user(self):
        user1 = User.objects.get(username="user1")
        client = Client()
        response = client.get('/users/' + str(user1.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['username'], "user1")

    def test_deleting_user(self):
        user2 = User.objects.get(username="user2")
        client = Client()
        response = client.delete('/users/' + str(user2.id) + '/')
        self.assertEqual(response.status_code, 204)
        response = client.get('/users/' + str(user2.id) + '/')
        self.assertEqual(response.status_code, 404)

    def test_patching_user(self):
        user1 = User.objects.get(username="user1")
        client = Client()
        response = client.patch('/users/' + str(user1.id) + '/',
                                content_type='application/json',
                                data='{"username": "new_username"}')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['username'], "new_username")

    def test_creating_user(self):
        client = Client()
        user_data = {
            "username": "user3",
            "decks": []
        }
        response = client.post('/users/', content_type='application/json',
                                data=json.dumps(user_data))
        user3 = User.objects.get(username="user3");
        response = client.get('/users/' + str(user3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['username'], "user3")


class DeckViewsTestCase(TestCase):
    def setUp(self):
        user1 = User.objects.create(username="user1")
        deck1 = Deck.objects.create(name="deck1", user=user1)
        deck2 = Deck.objects.create(name="deck2", user=user1)

    def test_getting_all_decks(self):
        client = Client()
        response = client.get('/decks/')
        self.assertEqual(response.status_code, 200)

    def test_getting_one_deck(self):
        deck1 = Deck.objects.get(name="deck1")
        client = Client()
        response = client.get('/decks/' + str(deck1.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['name'], "deck1")

    def test_deleting_deck(self):
        deck2 = Deck.objects.get(name="deck2")
        client = Client()
        response = client.delete('/decks/' + str(deck2.id) + '/')
        self.assertEqual(response.status_code, 204)
        response = client.get('/decks/' + str(deck2.id) + '/')
        self.assertEqual(response.status_code, 404)

    def test_patching_deck(self):
        deck1 = Deck.objects.get(name="deck1")
        client = Client()
        response = client.patch('/decks/' + str(deck1.id) + '/',
                                content_type='application/json',
                                data='{"name": "new_name"}')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['name'], "new_name")

    def test_creating_deck(self):
        user1 = User.objects.get(username="user1")
        client = Client()
        deck_data = {
            "user": user1.id,
            "name": "deck3",
            "cards": []
        }
        response = client.post('/decks/', content_type='application/json',
                                data=json.dumps(deck_data))
        deck3 = Deck.objects.get(name="deck3");
        response = client.get('/decks/' + str(deck3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['name'], "deck3")


class CardViewsTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="user1")
        deck = Deck.objects.create(name="deck1", user=user)
        card1 = Card.objects.create(front="front1", back="back1", deck=deck)
        card2 = Card.objects.create(front="front2", back="back2", deck=deck)

    def test_getting_all_cards(self):
        client = Client()
        response = client.get('/cards/')
        self.assertEqual(response.status_code, 200)

    def test_getting_card(self):
        card1 = Card.objects.get(front="front1")
        client = Client()
        response = client.get('/cards/' + str(card1.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['front'], "front1")

    def test_deleting_card(self):
        card2 = Card.objects.get(front="front2")
        client = Client()
        response = client.delete('/cards/' + str(card2.id) + '/')
        self.assertEqual(response.status_code, 204)
        response = client.get('/cards/' + str(card2.id) + '/')
        self.assertEqual(response.status_code, 404)

    def test_patching_card(self):
        card1 = Card.objects.get(front="front1")
        client = Client()
        response = client.patch('/cards/' + str(card1.id) + '/',
                                content_type='application/json',
                                data='{"front": "new_front"}')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['front'], "new_front")

    def test_creating_card(self):
        deck = Deck.objects.get(name="deck1")
        client = Client()
        card_data = {
            "front": "front3",
            "back": "back3",
            "deck": deck.id
        }
        response = client.post('/cards/', content_type='application/json',
                                data=json.dumps(card_data))
        card3 = Card.objects.get(front="front3");
        response = client.get('/cards/' + str(card3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['front'], "front3")

class ReviewViewsTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="user1")
        deck = Deck.objects.create(name="deck1", user=user)
        card1 = Card.objects.create(front="front1", back="back1", deck=deck)
        card2 = Card.objects.create(front="front2", back="back2", deck=deck)
        card3 = Card.objects.create(front="front3", back="back3", deck=deck)
        review11 = Review.objects.create(card=card1, answer_quality=2)
        review12 = Review.objects.create(card=card1, answer_quality=5)
        review21 = Review.objects.create(card=card2, answer_quality=3)

    def test_getting_all_reviews(self):
        client = Client()
        response = client.get('/reviews/')
        self.assertEqual(response.status_code, 200)

    def test_getting_card(self):
        card2 = Card.objects.get(front="front2")
        review21 = Review.objects.get(card=card2)
        client = Client()
        response = client.get('/reviews/' + str(review21.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['answer_quality'], 3)

    def test_creating_review(self):
        card2 = Card.objects.get(front="front2")
        client = Client()
        review_data = {
            "card": card2.id,
            "answer_quality": 1
        }
        response = client.post('/reviews/', content_type='application/json',
                                data=json.dumps(review_data))
        self.assertEqual(response.status_code, 200)
        review22 = Review.objects.get(answer_quality=1)
        response = client.get('/reviews/' + str(review22.id) + '/')
        self.assertEqual(response.status_code, 200)

    def test_is_card_reviewed_after_creating_new_review(self):
        card3 = Card.objects.get(front="front3")
        client = Client()

        response = client.get('/cards/' + str(card3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['is_due'], True)

        review_data = {
            "card": card3.id,
            "answer_quality": 1
        }
        response = client.post('/reviews/', content_type='application/json',
                                data=json.dumps(review_data))
        self.assertEqual(response.status_code, 200)
        review22 = Review.objects.get(answer_quality=1)
        response = client.get('/reviews/' + str(review22.id) + '/')
        self.assertEqual(response.status_code, 200)

        response = client.get('/cards/' + str(card3.id) + '/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads((response.content).decode('utf-8'))
        self.assertEqual(response_dict['is_due'], False)


