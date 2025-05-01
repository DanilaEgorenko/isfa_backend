from django.contrib import admin
from .models import (
    User, Comment, ChartData, RetailTrandItem, RetailTrandItems, Item, CollectionItem,
    UserTrandAction, VirtualPortfolioItem, MainPage
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'name', 'role', 'rating')
    search_fields = ('email', 'name')
    list_filter = ('role', 'rating')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_id', 'text', 'date')
    search_fields = ('author_id', 'text')
    list_filter = ('date', 'author_id')

@admin.register(ChartData)
class ChartDataAdmin(admin.ModelAdmin):
    list_display = ('time', 'open', 'high', 'low', 'close')
    list_filter = ('time',)

@admin.register(RetailTrandItem)
class RetailTrandItemAdmin(admin.ModelAdmin):
    list_display = ('current_price', 'min', 'max')

@admin.register(RetailTrandItems)
class RetailTrandItemsAdmin(admin.ModelAdmin):
    list_display = ('id',)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'rating', 'type', 'category')
    search_fields = ('name', 'category', 'type')
    list_filter = ('type', 'category', 'rating')

@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'short_description', 'human_trand_up', 'human_trand_down')
    search_fields = ('name', 'short_description')
    list_filter = ('human_trand_up', 'human_trand_down')

@admin.register(UserTrandAction)
class UserTrandActionAdmin(admin.ModelAdmin):
    list_display = ('action', 'date')

@admin.register(VirtualPortfolioItem)
class VirtualPortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('item', 'value', 'count')

@admin.register(MainPage)
class MainPageAdmin(admin.ModelAdmin):
    list_display = ('id',)
