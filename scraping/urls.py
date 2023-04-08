from django.urls import path
from scraping import views

urlpatterns = [
    path('smartphones/', views.Smartphones),
]
