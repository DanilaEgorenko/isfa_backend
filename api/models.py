from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.http import JsonResponse
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name, password, **extra_fields)

class Comment(models.Model):
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    author_id = models.IntegerField()
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='comments_item', null=True, blank=True)
    collection = models.ForeignKey('CollectionItem', on_delete=models.CASCADE, related_name='comments_collection', null=True, blank=True)

    def __str__(self):
        return f"Comment by user {self.author_id} on {self.date}"
    
class ChartData(models.Model):
    time = models.DateTimeField()
    high = models.FloatField()
    low = models.FloatField()
    open = models.FloatField()
    close = models.FloatField()

    def __str__(self):
        return f"Chart data at {self.time}"
    
class RetailTrandItem(models.Model):
    current_price = models.FloatField()
    min = models.FloatField()
    max = models.FloatField()

    def __str__(self):
        return f"Retail trend: {self.current_price}"
    
class RetailTrandItems(models.Model):
    day = models.OneToOneField(RetailTrandItem, on_delete=models.CASCADE, related_name='day_trend')
    week = models.OneToOneField(RetailTrandItem, on_delete=models.CASCADE, related_name='week_trend')
    month = models.OneToOneField(RetailTrandItem, on_delete=models.CASCADE, related_name='month_trend')
    year = models.OneToOneField(RetailTrandItem, on_delete=models.CASCADE, related_name='year_trend')

    def __str__(self):
        return "Retail trends"
    
class Item(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    price = models.FloatField()
    predict_price = models.FloatField(null=True, blank=True)
    icon = models.CharField(max_length=255)
    color = models.CharField(max_length=50, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(max_length=100)
    chart = models.ManyToManyField(ChartData, blank=True)
    comments = models.ManyToManyField('Comment', related_name='comments_item', blank=True)
    rating = models.FloatField(default=0.0)
    human_trand_up = models.FloatField(default=0.0)
    human_trand_down = models.FloatField(default=0.0)
    retail_trand = models.OneToOneField(RetailTrandItems, on_delete=models.SET_NULL, null=True, blank=True)
    change = models.FloatField(null=True, blank=True, default=0.0)

    def __str__(self):
        return self.name
    
class CollectionItem(models.Model):
    name = models.CharField(max_length=255)
    id = models.AutoField(primary_key=True)
    human_trand_up = models.FloatField(default=0.0)
    human_trand_down = models.FloatField(default=0.0)
    description = models.TextField()
    short_description = models.CharField(max_length=255)
    pic = models.CharField(max_length=255)
    color = models.CharField(max_length=50, null=True, blank=True)
    items = models.ManyToManyField(Item, blank=True)
    comments = models.ManyToManyField('Comment', related_name='comments_collection', blank=True)

    def __str__(self):
        return self.name
    
    def calculate_retail_trand(self):
        """
        Рассчитывает retail_trand для коллекции на основе связанных items.
        """
        items = self.items.all()
        if not items:
            return 0.0

        total_retail_trand = 0.0
        count = 0

        for item in items:
            if hasattr(item, 'retail_trand') and item.retail_trand is not None:
                total_retail_trand += item.retail_trand
                count += 1

        return total_retail_trand / count if count > 0 else 0.0
    
class UserTrandAction(models.Model):
    ACTION_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('none', 'None'),
    ]

    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='none')
    date = models.DateTimeField(default=timezone.now)  # Время действия
    user_id = models.IntegerField()  # ID пользователя
    item = models.ForeignKey('Item', related_name='user_trand_actions', on_delete=models.CASCADE)  # Связь с Item

    class Meta:
        unique_together = ('user_id', 'item')  # Уникальная запись для каждого пользователя и элемента

    def __str__(self):
        return f"User {self.user_id} action on {self.item.name} ({self.action})"
    

class UserCollectionAction(models.Model):
    ACTION_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('none', 'None'),
    ]

    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='none')
    date = models.DateTimeField(default=timezone.now)  # Время действия
    user_id = models.IntegerField()  # ID пользователя
    collection = models.ForeignKey('CollectionItem', related_name='user_collection_actions', on_delete=models.CASCADE)  # Связь с CollectionItem

    class Meta:
        unique_together = ('user_id', 'collection')  # Уникальная запись для каждого пользователя и коллекции

    def __str__(self):
        return f"User {self.user_id} action on {self.collection.name} ({self.action})"
    
class VirtualPortfolioItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    value = models.FloatField()
    count = models.IntegerField()

    def __str__(self):
        return f"{self.item.name}"
    
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'Admin', 'Admin'
        USER = 'User', 'User'

    name = models.CharField(max_length=20)
    username = None
    email = models.EmailField(unique=True)
    pic = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    rating = models.FloatField(default=0.0)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    favorites = models.ManyToManyField(Item, blank=True)
    virtual_stock_portfolio = models.ManyToManyField(
        VirtualPortfolioItem,
        blank=True
    )
    trand_activities = models.ManyToManyField(UserTrandAction, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def get_virtual_stock(self, id):
        try:
            item = self.virtual_stock_portfolio.get(item__id=id)
            return {
                'count': item.count,
                'value': item.value
            }
        except VirtualPortfolioItem.DoesNotExist:
            return None

    def toggle_favorite(self, item_id):
        item = Item.objects.get(id=item_id)
        if self.favorites.filter(id=item_id).exists():
            self.favorites.remove(item)
            return False
        else:
            self.favorites.add(item)
            return True

    objects = UserManager()  # Используем кастомный менеджер

    def __str__(self):
        return self.name
    
class MainPage(models.Model):
    top_highest = models.ManyToManyField(Item, related_name='top_highest', blank=True)
    top_lowest = models.ManyToManyField(Item, related_name='top_lowest', blank=True)
    collections = models.ManyToManyField(CollectionItem, blank=True)
    activeItems = models.ManyToManyField(Item, related_name='active_items', blank=True)
    list = models.ManyToManyField(Item, related_name='list_items', blank=True)

    def __str__(self):
        return "Main Page Data"