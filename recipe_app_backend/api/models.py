from django.db import models
from django.contrib.auth import get_user_model

# PUBLIC_INTERFACE
class Category(models.Model):
    """
    A category under which recipes can be grouped,
    e.g., "Dessert", "Main Course", etc.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# PUBLIC_INTERFACE
class Ingredient(models.Model):
    """
    An ingredient that can be used in one or more recipes.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# PUBLIC_INTERFACE
class Recipe(models.Model):
    """
    Represents a cooking recipe created by a user.
    Includes fields for name, description, instructions, cooking time,
    associated user, categories, and ingredients (with quantity/unit).
    """
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cook_time_minutes = models.PositiveIntegerField()
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="recipes")
    categories = models.ManyToManyField('Category', related_name='recipes')
    ingredients = models.ManyToManyField(
        'Ingredient', through='RecipeIngredient', related_name='recipes'
    )

    def __str__(self):
        return self.title

# PUBLIC_INTERFACE
class RecipeIngredient(models.Model):
    """
    Through-model to link a Recipe and an Ingredient, storing quantity and unit for each relationship.
    """
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        q = f"{self.quantity:g}" if self.quantity else ""
        u = f" {self.unit}" if self.unit else ""
        return f"{self.ingredient.name} in {self.recipe.title}: {q}{u}"

# PUBLIC_INTERFACE
class FavoriteRecipe(models.Model):
    """
    A user's favorite recipe. Allows users to save/bookmark a recipe.
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="favorite_recipes")
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name="favorited_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"Favorite {self.recipe.title} by {self.user}"

# PUBLIC_INTERFACE
class RecipeImage(models.Model):
    """
    Stores images associated with recipes.
    """
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="recipe_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.recipe.title}"
