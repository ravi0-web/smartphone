from django.contrib import admin
from django.urls import path
from .views import recommend_phones,contact_view

from .import views

urlpatterns = [
    path('home/',views.home,name="home"),
  path('',views.signup,name="signup"),
 path('login_/', views.login_, name='login_'),
 path('logout/', views.logoutuser, name='logoutuser'),

  
 path('recommend/', recommend_phones, name='recommend_phones'),

path('phone/<slug:model_slug>/', views.phone_detail_view, name='phone_detail'),
 path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('search-results/', views.search_results, name='search_results'),
        path('search-phones/', views.search_phones, name='search_phones'),  
    path('compare/', views.compare, name='compare'),
     path('contact/', contact_view, name='contact'),
     path('about/', views.about_view, name='about'),


]
