import requests
from django.http import JsonResponse
from django.core.cache import cache
import requests
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http import JsonResponse
from .models import Item, User
import pytz
from .views import get_market_trand
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.conf import settings

T_INVEST_BASE_URL = "https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1"
T_INVEST_AUTHORIZATION = settings.T_AUTHORIZATION

def get_daily_price_change(figi):
    url = f"{T_INVEST_BASE_URL}.MarketDataService/GetCandles"
    headers = {"Authorization": T_INVEST_AUTHORIZATION}
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(tz)
    today = now
    yesterday = today - timedelta(days=8)
    
    try:
        response = requests.post(url, headers=headers, json={
            "figi": figi,
            "from": yesterday.isoformat(),
            "to": today.isoformat(),
            "interval": "CANDLE_INTERVAL_HOUR"
        })
        response.raise_for_status()
        print(response.json(), today.isoformat(), yesterday.isoformat())
        
        candles = response.json().get("candles", [])
        for candle in candles:
            candle['open'] = convert_price(candle['open'])
            candle['close'] = convert_price(candle['close'])
            candle['low'] = convert_price(candle['low'])
            candle['high'] = convert_price(candle['high'])
        if not candles:
            return None
        return candles
    
    except Exception as e:
        print(f"Error getting price for {figi}: {e}")
        return None

def convert_price(price_dict):
    try:
        return float(price_dict['units']) + float(price_dict['nano']) / 1e9
    except:
        return 0.0

def get_shares(request):
    cached = cache.get('russian_shares')
    if cached:
        return JsonResponse(cached, safe=False)
    url = f"{T_INVEST_BASE_URL}.InstrumentsService/Shares"
    headers = {
        "Authorization": T_INVEST_AUTHORIZATION,
        "accept": "application/json",
    }
    payload = {
        "instrumentStatus": "INSTRUMENT_STATUS_ALL",
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json().get("instruments", [])
        russian_shares = [
            share for share in data 
            if (share.get("exchange") == "MOEX"  # Акции Московской биржи
                or share.get("isin", "").startswith("RU"))  # ISIN начинается с RU
        ]
        if not cached:
            cache.set('russian_shares', russian_shares, timeout=3600)
        return JsonResponse(russian_shares, safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_etfs(request):
    cached = cache.get('russian_etfs')
    if cached:
        return JsonResponse(cached, safe=False)
    url = f"{T_INVEST_BASE_URL}.InstrumentsService/Etfs"
    headers = {
        "Authorization": T_INVEST_AUTHORIZATION,
        "accept": "application/json",
    }
    payload = {
        "instrumentStatus": "INSTRUMENT_STATUS_ALL",
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json().get("instruments", [])
        russian_etfs = [
            etf for etf in data 
            if (etf.get("exchange") == "MOEX"  # Акции Московской биржи
                or etf.get("isin", "").startswith("RU"))  # ISIN начинается с RU
        ]
        if not cached:
            cache.set('russian_etfs', russian_etfs, timeout=3600)
        return JsonResponse(russian_etfs, safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
    

def get_bonds(request):
    cached = cache.get('russian_bonds')
    if cached:
        return JsonResponse(cached, safe=False)
    url = f"{T_INVEST_BASE_URL}.InstrumentsService/Bonds"
    headers = {
        "Authorization": T_INVEST_AUTHORIZATION,
        "accept": "application/json",
    }
    payload = {
        "instrumentStatus": "INSTRUMENT_STATUS_ALL",
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json().get("instruments", [])
        russian_bonds = [
            bond for bond in data 
            if (bond.get("exchange") == "MOEX"  # Акции Московской биржи
                or bond.get("isin", "").startswith("RU"))  # ISIN начинается с RU
        ]
        if not cached:
            cache.set('russian_bonds', russian_bonds, timeout=3600)
        return JsonResponse(russian_bonds, safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
    

def get_futures(request):
    cached = cache.get('russian_futures')
    if cached:
        return JsonResponse(cached, safe=False)
    url = f"{T_INVEST_BASE_URL}.InstrumentsService/Futures"
    headers = {
        "Authorization": T_INVEST_AUTHORIZATION,
        "accept": "application/json",
    }
    payload = {
        "instrumentStatus": "INSTRUMENT_STATUS_ALL",
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json().get("instruments", [])
        russian_futures = [
            future for future in data 
            if (future.get("countryOfRisk") == "RU")
        ]
        if not cached:
            cache.set('russian_futures', russian_futures, timeout=3600)
        return JsonResponse(russian_futures, safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
    

def get_options(request):
    cached = cache.get('russian_options')
    if cached:
        return JsonResponse(cached, safe=False)
    url = f"{T_INVEST_BASE_URL}.InstrumentsService/Options"
    headers = {
        "Authorization": T_INVEST_AUTHORIZATION,
        "accept": "application/json",
    }
    payload = {
        "instrumentStatus": "INSTRUMENT_STATUS_ALL",
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json().get("instruments", [])
        russian_options = [
            option for option in data 
            if (option.get("countryOfRisk") == "RU")
        ]
        if not cached:
            cache.set('russian_options', russian_options, timeout=3600)
        return JsonResponse(russian_options, safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt  
def get_item(request, id):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1]
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
    except:
        user = None
    
    url = f"{T_INVEST_BASE_URL}.InstrumentsService/GetInstrumentBy"
    headers = {
        "Authorization": T_INVEST_AUTHORIZATION,
        "accept": "application/json",
    }
    payload = {
        "idType": "INSTRUMENT_ID_TYPE_UID",
        "id": id
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json().get("instrument", {})

        candles = get_daily_price_change(data['figi'])
        data['candles'] = candles
        if candles:
            data['price'] = candles[-1]['close'] or 0.0
            data['change'] = candles[-1]['close'] / candles[-25]['close'] * 100 - 100
            prices = [price['close'] for price in candles if price is not None]
            data['retail_trand'] = get_market_trand(prices, 10)
        else:
            data['price'] = None
            data['change'] = None
            data['retail_trand'] = "UNKNOWN"

        if data['instrumentType'] == "bond":
            response_bond = requests.post(f"{T_INVEST_BASE_URL}.InstrumentsService/BondBy", json={
                "idType": "INSTRUMENT_ID_TYPE_FIGI",
                "id": data['figi']
            }, headers=headers)
            response_bond.raise_for_status()
            data_bond = response_bond.json().get("instrument", {})

            tz = pytz.timezone('Europe/Moscow')
            now = datetime.now(tz)
            today = now
            year_plus_one = today + timedelta(days=365)

            response_coupon = requests.post(f"{T_INVEST_BASE_URL}.InstrumentsService/GetBondEvents", json={
                "from": today.isoformat(),
                "to": year_plus_one.isoformat(),
                "instrumentId": data['figi']
            }, headers=headers)
            response_coupon.raise_for_status()
            data_coupon = response_coupon.json().get("events", [])

            data['bond_info'] = {
                'coupon': convert_price(data_coupon[0]['payOneBond']),
                'nominal': convert_price(data_bond['nominal']),
                'maturity_date': data_bond['maturityDate'],
                'nkd': convert_price(data_bond['aciValue']),
                'coupons_per_year': data_bond['couponQuantityPerYear']
            }

        item, created = Item.objects.update_or_create(
            id=id,
            defaults={
                'name': data.get('name', 'Unknown'),  # Имя из API
                'price': 0.0,
                'change': data.get('change', 0.0),  # Цена из API
                'icon': data['brand']['logoName'],
                'type': data.get('instrumentType'),
                'change': data.get('change', 0),
            }
        )
        data['human_trand_up'] = item.human_trand_up
        data['human_trand_down'] = item.human_trand_down
        if user:
            user_trand_action = item.user_trand_actions.filter(user_id=user.id).first()
            data.update({
                'user_action': user_trand_action.action if user_trand_action else 'none',
                'favorite': user.favorites.filter(id=id).exists(),
                'virtual_stock': user.get_virtual_stock(id),
            })
        else:
            data.update({
                'user_action': None,
                'favorite': None,
                'virtual_stock': None,
            })

        return JsonResponse(data, safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)