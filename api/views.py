from rest_framework import generics, permissions, response
from .serializers import CustomUserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import get_user_model
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Item, UserTrandAction, CollectionItem, UserCollectionAction, Comment, VirtualPortfolioItem
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils import timezone
import json
from .serializers import CollectionItemSerializer, CommentSerializer
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return response.Response({
            "access": str(access),
            "refresh": str(refresh)
        })


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
import json

@csrf_exempt
def update_user_data(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Invalid token format"}, status=401)
    token = auth_header.split(' ')[1]

    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']  
    except (InvalidToken, TokenError) as e:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
        update_fields = {}
        if 'name' in data:
            update_fields['name'] = data['name']
        if 'status' in data:
            update_fields['status'] = data['status']
        if 'pic' in data:
            update_fields['pic'] = data['pic']
    
        user, created = User.objects.update_or_create(
            id=user_id,
            defaults=update_fields
        )
        return JsonResponse({"message": "User updated", "user_id": user.id})
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

COINRANKING_BASE_URL = 'https://api.coinranking.com/v2'

def get_crypto(request):
    offset = request.GET.get('offset', 0)
    url = f"{COINRANKING_BASE_URL}/coins?limit=40&offset={offset}"
    headers = {
    }
    response = requests.get(url, headers=headers)
    return JsonResponse(response.json(), safe=False)

def get_crypto_by_change(request, order_direction):
    url = f"{COINRANKING_BASE_URL}/coins?limit=10&orderBy=change&orderDirection={order_direction}"
    headers = {
    }
    response = requests.get(url, headers=headers)
    return JsonResponse(response.json(), safe=False)


@csrf_exempt
def get_crypto_by_id(request, id):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1]
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
    except:
        user = None

    url = f"{COINRANKING_BASE_URL}/coin/{id}"
    headers = {}
    response = requests.get(url, headers=headers)
    data = response.json()

    if 'data' not in data or 'coin' not in data['data']:
        return JsonResponse({"error": "Coin not found"}, status=404)

    coin_data = data['data']['coin']

    item, created = Item.objects.update_or_create(
        id=id,
        defaults={
            'name': coin_data.get('name', 'Unknown'),  # Имя из API
            'price': float(coin_data.get('price', 0.0)),  # Цена из API
            'icon': coin_data.get('iconUrl', ''),  # Иконка из API
            'type': 'crypto',  # Тип (можно указать другой, если нужно)
            'human_trand_up': 0.0,  # Начальное значение human_trand
            'human_trand_down': 0.0,  # Начальное значение human_trand
            'change': coin_data.get('change', 0),
        }
    )

    comments = item.comments.all().values('text', 'date')

    prices = [float(price) for price in coin_data['sparkline'] if price is not None]
    retail_trand = get_market_trand(prices)

    if user:
        user_trand_action = item.user_trand_actions.filter(user_id=user.id).first()
        user_action = user_trand_action.action if user_trand_action else 'none'
        favorite = user.favorites.filter(id=id).exists()
        virtual_stock = user.get_virtual_stock(id)
    else:
        user_action = None
        favorite = None
        virtual_stock = None

    response_data = {
        "coin": coin_data,
        "comments": list(comments),
        "user_action": user_action,
        "human_trand_up": item.human_trand_up,
        "human_trand_down": item.human_trand_down,
        "retail_trand": retail_trand,
        "favourite": favorite,
        "virtual_stock": virtual_stock
    }

    return JsonResponse(response_data, safe=False)
    

def get_market_trand(prices, window=6):
    if len(prices) < window:
        return "UNKNOWN"

    sma = []
    for i in range(window - 1, len(prices)):
        sum_window = sum(prices[i - window + 1:i + 1])
        sma.append(sum_window / window)

    last_sma = sma[-1]
    prev_sma = sma[-2]

    if last_sma > prev_sma:
        return "UP"
    elif last_sma < prev_sma:
        return "DOWN"
    else:
        return "SIDEWAYS"


@csrf_exempt
def vote_item(request, id):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Invalid token format"}, status=401)

    token = auth_header.split(' ')[1]

    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
    except (InvalidToken, TokenError):
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        item = Item.objects.get(id=id)
    except Item.DoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)

    try:
        data = json.loads(request.body)
        action = data.get('action')  # 'up' или 'down'
        if action not in ['up', 'down']:
            return JsonResponse({"error": "Invalid action"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Проверяем, голосовал ли пользователь ранее
    user_action, created = UserTrandAction.objects.get_or_create(
        user_id=user_id,
        item=item,
        defaults={'action': action, 'date': timezone.now()}  # Действие по умолчанию
    )

    if not created:
        # Если пользователь уже голосовал, обновляем действие
        if user_action.action == action:
            # Если действие совпадает, ничего не делаем
            return JsonResponse({"error": "User has already voted this way"}, status=400)
        else:
            # Если действие противоположное, обнуляем предыдущий голос
            if user_action.action == 'up' and action == 'down':
                item.human_trand_up -= 1  # Отменяем предыдущий up
            if user_action.action == 'down' and action == 'up':
                item.human_trand_down -= 1  # Отменяем предыдущий down
            user_action.action = 'none'
    else:
        # Если это новый голос, обновляем human_trand
        if action == 'up':
            item.human_trand_up += 1
        elif action == 'down':
            item.human_trand_down += 1
        user_action.action = action

    user_action.date = timezone.now()
    user_action.save()
    item.save()

    return JsonResponse({"message": f"Vote {action} successful"})

@csrf_exempt
def vote_collection(request, id):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Invalid token format"}, status=401)

    token = auth_header.split(' ')[1]

    try:
        # Декодируем токен
        access_token = AccessToken(token)
        user_id = access_token['user_id']
    except (InvalidToken, TokenError):
        return JsonResponse({"error": "Invalid token"}, status=401)

    # Получаем коллекцию (CollectionItem)
    try:
        collection = CollectionItem.objects.get(id=id)
    except CollectionItem.DoesNotExist:
        return JsonResponse({"error": "Collection not found"}, status=404)

    # Получаем действие из тела запроса
    try:
        data = json.loads(request.body)
        action = data.get('action')  # 'up' или 'down'
        if action not in ['up', 'down']:
            return JsonResponse({"error": "Invalid action"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Проверяем, голосовал ли пользователь ранее
    user_action, created = UserCollectionAction.objects.get_or_create(
        user_id=user_id,
        collection=collection,
        defaults={'action': action, 'date': timezone.now()}  # Действие по умолчанию
    )

    if not created:
        # Если пользователь уже голосовал, обновляем действие
        if user_action.action == action:
            # Если действие совпадает, ничего не делаем
            return JsonResponse({"error": "User has already voted this way"}, status=400)
        else:
            # Если действие противоположное, обнуляем предыдущий голос
            if user_action.action == 'up' and action == 'down':
                collection.human_trand_up -= 1  # Отменяем предыдущий up
            if user_action.action == 'down' and action == 'up':
                collection.human_trand_down -= 1  # Отменяем предыдущий down
            user_action.action = 'none'
    else:
        # Если это новый голос, обновляем human_trand
        if action == 'up':
            collection.human_trand_up += 1
        elif action == 'down':
            collection.human_trand_down += 1

    user_action.date = timezone.now()
    user_action.save()
    collection.save()

    return JsonResponse({"message": f"Vote {action} successful"})


@csrf_exempt
def get_collection(request, id):
    collection = CollectionItem.objects.get(id=id)
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1]
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
    except:
        user = None

    if user:
        user_action = UserCollectionAction.objects.filter(
            user_id=user_id,
            collection=collection
        ).first()
        response_data['user_action'] = user_action.action if user_action else 'none'
    else:
        response_data['user_action'] = None

    serializer = CollectionItemSerializer(collection)
    response_data = serializer.data
    return JsonResponse(response_data)

@csrf_exempt
def get_all_collections(request):
    """
    Возвращает список всех коллекций с полями: id, name, short_description, pic.
    """
    collections = CollectionItem.objects.all().values('id', 'name', 'short_description', 'pic')
    return JsonResponse(list(collections), safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def add_comment(request):
    data = json.loads(request.body)
    text = data.get('text')
    item_id = data.get('item_id')
    collection_id = data.get('collection_id')

    if item_id and collection_id:
        return JsonResponse({'error': 'Comment can be associated with either an item or a collection, not both.'}, status=400)

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Invalid token format"}, status=401)
    token = auth_header.split(' ')[1]

    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']  
    except (InvalidToken, TokenError) as e:
        return JsonResponse({"error": "Invalid token"}, status=401)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    comment = Comment.objects.create(
        text=text,
        author_id=user_id,
        item_id=item_id,
        collection_id=collection_id
    )

    return JsonResponse({
        'id': comment.id,
        'text': comment.text,
        'date': comment.date,
        'author': {
            'id': user_id,
            'username': user.username,
            'avatar': user.pic if user.pic else None
        }
    }, status=201)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)

    comment.delete()
    return JsonResponse({'message': 'Comment deleted successfully'}, status=200)

@api_view(['GET'])
def get_comments(request):
    object_type = request.query_params.get('type')
    object_id = request.query_params.get('id')

    if not object_type or not object_id:
        return Response({'error': 'Both type and id are required'}, status=400)

    if object_type not in ['item', 'collection']:
        return Response({'error': 'Invalid type. Use "item" or "collection"'}, status=400)

    if object_type == 'item':
        comments = Comment.objects.filter(item_id=object_id).order_by('-date')
    else:
        comments = Comment.objects.filter(collection_id=object_id).order_by('-date')

    serializer = CommentSerializer(comments, many=True)
    return Response({'comments': serializer.data})

@api_view(['POST'])
def toggle_favorite_api(request, id):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Invalid token format"}, status=401)
    token = auth_header.split(' ')[1]

    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']  
    except (InvalidToken, TokenError) as e:
        return JsonResponse({"error": "Invalid token"}, status=401)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    is_favorite = user.toggle_favorite(id)
    return Response({"is_favorite": is_favorite})

@api_view(['POST'])
def manage_virtual_portfolio(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Invalid token format"}, status=401)
    
    token = auth_header.split(' ')[1]
    
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']  
    except (InvalidToken, TokenError) as e:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    item_id = request.data.get('item_id')
    quantity = int(request.data.get('quantity', 0))
    price_per_unit = float(request.data.get('price_per_unit', 0))
    type = request.data.get('type', 'add')

    item = Item.objects.get(id=item_id)

    portfolio_item, created = VirtualPortfolioItem.objects.get_or_create(
        user=user,
        item=item,
        defaults={
            'count': quantity,
            'value': quantity * price_per_unit
        }
    )

    if created:
        user.virtual_stock_portfolio.add(portfolio_item)

    if not created:
        if type == 'add':
            portfolio_item.count += quantity
            portfolio_item.value += quantity * price_per_unit
        else:
            portfolio_item.value -= (portfolio_item.value / portfolio_item.count) * quantity
            portfolio_item.count -= quantity

    if portfolio_item.count == 0:
        user.virtual_stock_portfolio.remove(portfolio_item)
    
    portfolio_item.save()
        
    return JsonResponse({'count': portfolio_item.count, 'value': portfolio_item.value})