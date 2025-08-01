from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')
router.register(r'recipes', views.RecipeViewSet, basename='recipe')
router.register(r'favorites', views.FavoriteRecipeViewSet, basename='favorite')
router.register(r'images', views.RecipeImageViewSet, basename='image')

urlpatterns = [
    path('health/', views.health, name='Health'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('', include(router.urls)),
]
