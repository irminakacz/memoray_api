from django.conf.urls import url, include
from api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'cards', views.CardViewSet)
router.register(r'reviews', views.ReviewViewSet)

urlpatterns = [
    url(r'^', include(router.urls))
]
