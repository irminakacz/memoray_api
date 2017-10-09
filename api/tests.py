from django.test import TestCase, Client
from django.utils import timezone
from api.models import Card, Review
from api.serializers import CardSerializer, ReviewSerializer
import json


class CardModelTestCase(TestCase):
    def setUp(self):
        Card.objects.create(front="default")
        Card.objects.create(front="front1", interval=6)
        Card.objects.create(front="front2", interval=30)

    def test_if_default_last_review_date_is_empty(self):
        card = Card.objects.get(front="default")
        self.assertEqual(card.last_review_date(), None)

    def test_if_default_times_reviewed_is_zero(self):
        card = Card.objects.get(front="default")
        self.assertEqual(card.times_reviewed(), 0)

    def test_if_new_card_is_due(self):
        card = Card.objects.get(front="default")
        self.assertEqual(card.is_due, True)

    def test_if_new_easiness_factor_is_calculated_correctly(self):
        card = Card.objects.get(front="default")
        self.assertEqual(card.new_easiness_factor(0), 1.7)
        self.assertEqual(card.new_easiness_factor(1), 1.96)
        self.assertEqual(card.new_easiness_factor(2), 2.18)
        self.assertEqual(card.new_easiness_factor(3), 2.36)
        self.assertEqual(card.new_easiness_factor(4), 2.5)
        self.assertEqual(card.new_easiness_factor(5), 2.5)

    def test_if_new_interval_is_calculated_correctly(self):
        card1 = Card.objects.get(front="front1")
        card2 = Card.objects.get(front="front2")
        self.assertEqual(card1.new_interval(1.5), 9)
        self.assertEqual(card2.new_interval(0.86), 25)


class CardReviewIntegrationTestCase(TestCase):
    def setUp(self):
        Card.objects.create(front="default")

    def test_if_times_reviewed_updated_after_each_review(self):
        card = Card.objects.get(front="default")
        Review.objects.create(card=card, answer_quality=2)
        self.assertEqual(card.times_reviewed(), 1)
        Review.objects.create(card=card, answer_quality=3)
        Review.objects.create(card=card, answer_quality=1)
        self.assertEqual(card.times_reviewed(), 3)

    def test_if_last_review_date_equals_last_review_date(self):
        card = Card.objects.get(front="default")
        review = Review.objects.create(card=card, answer_quality=2)
        self.assertEqual(card.last_review_date(), review.review_date)

    def test_if_easiness_factor_not_gets_updated_until_third_review(self):
        card = Card.objects.get(front="default")
        review = Review.objects.create(card=card, answer_quality=4)
        card.review(review.answer_quality)
        review = Review.objects.create(card=card, answer_quality=3)
        card.review(review.answer_quality)
        review = Review.objects.create(card=card, answer_quality=1)
        card.review(review.answer_quality)
        self.assertNotEqual(card.easiness_factor, 2.5)

    def test_if_interval_gets_updated_by_review(self):
        card = Card.objects.get(front="default")
        review = Review.objects.create(card=card, answer_quality=2)
        card.review(review.answer_quality)
        self.assertNotEqual(card.interval, 0)

    def test_if_card_is_due_immediately_after_review(self):
        card = Card.objects.get(front="default")
        review = Review.objects.create(card=card, answer_quality=4)
        card.review(review.answer_quality)
        self.assertEqual(card.is_due, False)


class CardSerializerTestCase(TestCase):
    def setUp(self):
        Card.objects.create(front="card", back="serializer")

    def test_if_card_serializer_produce_desired_output(self):
        card = Card.objects.get(front="card")
        serializer = CardSerializer(card)
        desired_output = {
            "id": card.id,
            "front": "card",
            "back": "serializer",
            "is_due": True
        }
        self.assertEqual(serializer.data, desired_output)


class ReviewSerializerTestCase(TestCase):
    def setUp(self):
        card = Card.objects.create(front="review", back="serializer")
        Review.objects.create(card=card, answer_quality=4)

    def test_if_review_serializer_produce_desired_output(self):
        card = Card.objects.get(front="review")
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


class CardViewsTestCase(TestCase):
    def setUp(self):
        card1 = Card.objects.create(front="front1", back="back1")
        card2 = Card.objects.create(front="front2", back="back2")

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
        client = Client()
        card_data = {
            "front": "front3",
            "back": "back3"
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
        card1 = Card.objects.create(front="front1", back="back1")
        card2 = Card.objects.create(front="front2", back="back2")
        card3 = Card.objects.create(front="front3", back="back3")
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


