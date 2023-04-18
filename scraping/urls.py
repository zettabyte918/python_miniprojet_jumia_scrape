from django.urls import path
from scraping import views

urlpatterns = [
    path("", views.Smartphones, name="list_smartphone"),
    path("export/", views.export_to_excel, name="export_to_excel"),
]
