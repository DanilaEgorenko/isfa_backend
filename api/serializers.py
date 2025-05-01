from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Item, Comment, CollectionItem, VirtualPortfolioItem

User = get_user_model()

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'price', 'icon', 'type', 'change']  # Укажите нужные поля

class FavoriteItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'icon', 'type']

class VirtualStockItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer()

    class Meta:
        model = VirtualPortfolioItem
        fields = ['item', 'value', 'count']

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    favorites = FavoriteItemSerializer(many=True, read_only=True)
    virtual_stock_portfolio = VirtualStockItemSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'status', 'pic', 'rating', 'favorites', 'trand_activities', 'virtual_stock_portfolio']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['name'] = user.name
        token['id'] = user.id
        token['pic'] = user.pic
        return token

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'text', 'date', 'author']

    def get_author(self, obj):
        try:
            user = User.objects.get(id=obj.author_id)
            return {
                'id': user.id,
                'username': user.name,
                'avatar': user.pic if user.pic else None
            }
        except User.DoesNotExist:
            return {
                'id': None,
                'username': 'Unknown',
                'avatar': None
            }
    
class CollectionItemSerializer(serializers.ModelSerializer):
    retail_trand = serializers.SerializerMethodField()
    items = ItemSerializer(many=True, read_only=True)  # Вложенные объекты items
    comments = CommentSerializer(many=True, read_only=True)  # Вложенные объекты comments

    class Meta:
        model = CollectionItem
        fields = [
            'id', 'name', 'description', 'short_description', 'pic', 'color',
            'retail_trand', 'human_trand_up', 'human_trand_down', 'items', 'comments'
        ]

    # Метод для вычисления retail_trand
    def get_retail_trand(self, obj):
        return obj.calculate_retail_trand()