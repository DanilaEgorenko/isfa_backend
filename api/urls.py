from django.urls import path
from .views import RegisterView, CustomTokenObtainPairView, UserDetailView, update_user_data, get_crypto, get_crypto_by_change, get_crypto_by_id, vote_item, get_collection, get_all_collections, vote_collection, add_comment, delete_comment, get_comments, toggle_favorite_api, manage_virtual_portfolio
from .t_views import get_shares, get_etfs, get_bonds, get_futures, get_options, get_item
from .predict_views import predict_price
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user'),
    path('edit', update_user_data, name='update_user_data'),

    path('crypto/', get_crypto, name='get_crypto'),
    path('crypto/change/<str:order_direction>/', get_crypto_by_change, name='get_crypto_by_change'),
    path('crypto/<str:id>/', get_crypto_by_id, name='get_crypto_by_id'),
    path('items/<str:id>/vote/', vote_item, name='vote_item'),
    path('collections/<str:id>/vote/', vote_collection, name='vote_collection'),
    path('collections/<int:id>/', get_collection, name='get_collection'),
    path('collections/', get_all_collections, name='get_all_collections'),
    path('add_comment/', add_comment, name='add_comment'),
    path('delete_comment/<int:comment_id>/', delete_comment, name='delete_comment'),
    path('comments', get_comments, name='get_comments'),
    path('toggle_favourite/<str:id>', toggle_favorite_api, name='toggle_favourite'),
    path('manage_virtual_portfolio', manage_virtual_portfolio, name='manage_virtual_portfolio'),

    path('shares', get_shares, name='get_shares'),
    path('etfs', get_etfs, name='get_etfs'),
    path('bonds', get_bonds, name='get_bonds'),
    path('futures', get_futures, name='get_futures'),
    path('options', get_options, name='get_options'),
    path('item/<str:id>', get_item, name='get_item'),

    path('predict_price/', predict_price, name='predict_price'),
]