from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta


class Deck(models.Model):
    user = models.ForeignKey(User, related_name="decks",
                             on_delete=models.CASCADE)
    name = models.CharField(max_length=40)


class Card(models.Model):
    deck = models.ForeignKey(Deck, related_name="cards",
                             on_delete=models.CASCADE)
    front = models.CharField(max_length=200)
    back = models.CharField(max_length=200)
    creation_date = models.DateTimeField(auto_now_add=True)
    interval = models.IntegerField(default=0)
    easiness_factor = models.FloatField(default=2.5)

    @property
    def is_due(self):
        if self.last_review_date():
            next_review = self.last_review_date() + timedelta(days=self.interval)
            return next_review <= timezone.now()
        else:
            return True

    def last_review_date(self):
        if self.reviews.all().count() == 0:
            return None
        else:
            return self.reviews.all()[0].review_date

    def review(self, answer_quality):
        if self.times_reviewed() == 0:
            self.interval = 0;
        elif self.times_reviewed() == 1:
            self.interval = 1;
        elif self.times_reviewed() == 2:
            self.interval = 6;
        else:
            easiness_factor = self.new_easiness_factor(answer_quality)
            self.easiness_factor = easiness_factor
            interval = self.new_interval(easiness_factor)
            self.interval = interval

    def times_reviewed(self):
        return self.reviews.all().count()

    def new_easiness_factor(self, answer_quality):
        MAX_EASINESS_FACTOR = 2.5
        MIN_EASINESS_FACTOR = 1.1

        new_easiness_factor = self.easiness_factor - 0.8 + 0.28
        * answer_quality - 0.02 * answer_quality * answer_quality

        if new_easiness_factor > MAX_EASINESS_FACTOR:
            new_easiness_factor = MAX_EASINESS_FACTOR
        if new_easiness_factor < MIN_EASINESS_FACTOR:
            new_easiness_factor = MIN_EASINESS_FACTOR

        return round(new_easiness_factor, 2)

    def new_interval(self, easiness_factor):
        return int(self.interval * easiness_factor)


class Review(models.Model):
    card = models.ForeignKey(Card, related_name='reviews',
                             on_delete=models.CASCADE)
    review_date = models.DateTimeField(auto_now_add=True)
    answer_quality = models.IntegerField()

    class Meta:
        ordering = ["-review_date"]
