from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from .models import Category, Ingredient, Recipe, RecipeIngredient, FavoriteRecipe, RecipeImage

User = get_user_model()

# PUBLIC_INTERFACE
class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model (safe fields only)."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

# PUBLIC_INTERFACE
class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for registering new users."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

# PUBLIC_INTERFACE
class LoginSerializer(serializers.Serializer):
    """Serializer for validating user login."""
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials.")

# PUBLIC_INTERFACE
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

# PUBLIC_INTERFACE
class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'description']

# PUBLIC_INTERFACE
class RecipeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeImage
        fields = ['id', 'image', 'uploaded_at']

# PUBLIC_INTERFACE
class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), write_only=True, source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient', 'ingredient_id', 'quantity', 'unit']

# PUBLIC_INTERFACE
class RecipeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, many=True, source='categories'
    )
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, read_only=True)
    ingredient_data = serializers.ListField(
        write_only=True,
        child=serializers.DictField(),
        required=False,
        help_text="List of {'ingredient_id': int, 'quantity': float, 'unit': str}"
    )
    images = RecipeImageSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'description', 'instructions',
            'cook_time_minutes', 'user', 'created_at', 'updated_at',
            'categories', 'category_ids',
            'ingredients', 'ingredient_data',
            'images'
        ]

    def create(self, validated_data):
        category_objs = validated_data.pop('categories', [])
        ingredient_data = validated_data.pop('ingredient_data', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.categories.set(category_objs)
        for ing in ingredient_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ing['ingredient'],
                quantity=ing['quantity'],
                unit=ing.get('unit', '')
            )
        return recipe

    def update(self, instance, validated_data):
        if 'categories' in validated_data:
            instance.categories.set(validated_data.get('categories', []))
        if 'ingredient_data' in validated_data:
            instance.recipeingredient_set.all().delete()
            for ing in validated_data['ingredient_data']:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ing['ingredient'],
                    quantity=ing['quantity'],
                    unit=ing.get('unit', '')
                )
        for field in ['title', 'description', 'instructions', 'cook_time_minutes']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance

# PUBLIC_INTERFACE
class FavoriteRecipeSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(), write_only=True, source='recipe'
    )

    class Meta:
        model = FavoriteRecipe
        fields = ['id', 'user', 'recipe', 'recipe_id', 'added_at']
        read_only_fields = ['user', 'recipe', 'added_at']
