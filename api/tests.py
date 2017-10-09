from django.test import TestCase
from django.utils import timezone
from api.models import Card, Review
from api.serializers import CardSerializer, ReviewSerializer


class CardTestCase(TestCase):
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
