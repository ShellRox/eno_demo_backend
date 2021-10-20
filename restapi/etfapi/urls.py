from django.urls import path, re_path

from . import views

urlpatterns = [
    path('add_article/', views.add_article, name='add_article'),
    re_path('^articles/(?P<article_id>[0-9]{6})/$', views.get_article_data, name="get_article_data"),
    re_path('^article_token_metadata/(?P<article_id>[0-9]{6})/$', views.get_article_metaplex_metadata, name="get_article_data"),
    path('metadata_test/', views.metadata_test, name='metadata_test'),
    path('metadata_image_test/', views.metadata_image_test, name='metadata_image_test'),
    path('validate_author/', views.validate_ownership, name='validate_ownership'),
]
