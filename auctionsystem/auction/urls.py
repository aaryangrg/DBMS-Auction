from django.contrib import admin
from .views import *
from django.urls import path,include

urlpatterns = [
    path('item/all/',AllAuctionItems.as_view(),name = 'all-items'),
    path('item/add/', CreateItemView.as_view(), name = 'create-item'),
    path('item/<str:pk>/', ItemDetailView.as_view(), name = 'item-details'),
    path('item/bid/<str:pk>/',BidOnItemView.as_view(), name = 'bid-on-item'),
    path('login/', LoginView.as_view(), name = 'login'),
    path('register/', RegisterUser.as_view(), name = 'register'),
    path('profile', UserProfileView.as_view(), name = "user-profile"),
    path('logout/', logout_view, name = "logout")
]