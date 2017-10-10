from django.conf.urls import url, include
from api import views
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token

router = DefaultRouter()
router.register(r'users', views.UserViewSet, base_name="users")
router.register(r'decks', views.DeckViewSet, base_name="decks")
router.register(r'cards', views.CardViewSet, base_name="cards")
router.register(r'reviews', views.ReviewViewSet, base_name="reviews")

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^memoray-auth/', obtain_jwt_token)
]
