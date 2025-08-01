from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets, mixins, filters
from django.contrib.auth import get_user_model, login, logout
from .models import Category, Ingredient, Recipe, FavoriteRecipe, RecipeImage
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    CategorySerializer, IngredientSerializer,
    RecipeSerializer,
    FavoriteRecipeSerializer, RecipeImageSerializer
)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()

# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='get',
    operation_summary="API health check",
    tags=["Health"],
    responses={200: openapi.Response('Server status', schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
    ))}
)
@api_view(['GET'])
def health(request):
    """Returns a 200 with a simple health check message (used for testing liveness)."""
    return Response({"message": "Server is up!"})

# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    operation_summary="Register new user",
    tags=["Auth"]
)
@api_view(['POST'])
def register(request):
    """Register a new user account."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    operation_summary="Login",
    tags=["Auth"]
)
@api_view(['POST'])
def login_view(request):
    """Login a user and return user info."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        login(request, serializer.validated_data)
        return Response(UserSerializer(serializer.validated_data).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_summary="Logout",
    tags=["Auth"]
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout the current user."""
    logout(request)
    return Response({"message": "Successfully logged out."})

# PUBLIC_INTERFACE
class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD, list, and search for recipe categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']

# PUBLIC_INTERFACE
class IngredientViewSet(viewsets.ModelViewSet):
    """
    CRUD, list, and search for ingredients.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']

# PUBLIC_INTERFACE
class RecipeViewSet(viewsets.ModelViewSet):
    """
    Full CRUD and search API for recipes.
    Users must authenticate to create/edit/delete.
    Filtering/search supports title, description, cook time, ingredient name, and category.
    """
    queryset = Recipe.objects.prefetch_related('categories', 'ingredients', 'images').all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, filters.DjangoFilterBackend]
    search_fields = ['title', 'description', 'instructions']
    filterset_fields = ['categories__id', 'cook_time_minutes']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        ingredient = self.request.query_params.get('ingredient')
        if ingredient:
            qs = qs.filter(ingredients__name__icontains=ingredient)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(categories__name__icontains=category)
        return qs.distinct()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        """Add recipe to user's favorites."""
        recipe = self.get_object()
        user = request.user
        favorite, created = FavoriteRecipe.objects.get_or_create(user=user, recipe=recipe)
        if created:
            return Response({"message": "Recipe added to favorites."})
        return Response({"message": "Already in favorites."})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unfavorite(self, request, pk=None):
        """Remove recipe from user's favorites."""
        recipe = self.get_object()
        user = request.user
        FavoriteRecipe.objects.filter(user=user, recipe=recipe).delete()
        return Response({"message": "Recipe removed from favorites."})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my(self, request):
        """List all recipes created by the authenticated user."""
        recipes = Recipe.objects.filter(user=request.user)
        page = self.paginate_queryset(recipes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(recipes, many=True)
        return Response(serializer.data)

# PUBLIC_INTERFACE
class FavoriteRecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List all favorites for the current user.
    """
    serializer_class = FavoriteRecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteRecipe.objects.filter(user=self.request.user)

# PUBLIC_INTERFACE
class RecipeImageViewSet(mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """
    Upload and delete recipe images.
    """
    queryset = RecipeImage.objects.all()
    serializer_class = RecipeImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        recipe_id = self.request.data.get('recipe')
        recipe = Recipe.objects.get(id=recipe_id)
        serializer.save(recipe=recipe)

