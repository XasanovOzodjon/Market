from django.urls import path
from .views import ReviewsView, CreateReviewView

urlpatterns = [

    path("reviews/", ReviewsView.as_view()),

    path("reviews/create/", CreateReviewView.as_view()),

]