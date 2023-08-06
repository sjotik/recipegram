from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientsFilterSet, RecipeFilterSet
from recipes.models import (
    Favorite, Ingredient, Recipe, ShoppingCart, Subscribe, Tag)
from users.models import User
from .serializers import (
    IngredientSeriaizer,
    RecipeCreateSerializer,
    RecipeShowSerializer,
    RecipeShowShortSerializer,
    SubscribeSerializer,
    TagSeriaizer,
    )
from .utils import CustomPagination


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSeriaizer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSeriaizer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientsFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeShowSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet

    def get_serializer_class(self):
        # if self.action == 'create' or self.action == 'update':
        #     return RecipeCreateSerializer
        if self.request.method in ('POST', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeShowSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_name='favorite',
        url_path='favorite',
        # permission_classes=[]
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if recipe.is_favorited.filter(user=user).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite = Favorite(user=user, recipe=recipe)
            favorite.save()
            serializer = RecipeShowShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            if not recipe.is_favorited.filter(user=user).exists():
                return Response(
                    {'errors': 'Такого рецепта в избранном нет'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_name='shopping_cart',
        url_path='shopping_cart',
        # permission_classes=[]
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if recipe.in_shopping_cart.filter(user=user).exists():
                return Response(
                    {'errors': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart = ShoppingCart(user=user, recipe=recipe)
            cart.save()
            serializer = RecipeShowShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            if not recipe.in_shopping_cart.filter(user=user).exists():
                return Response(
                    {'errors': 'Рецепта в корзине нет'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribtionsApiView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = SubscribeSerializer
    # permission_classes = []
    # pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(subscribed__user=user)


class SubscribeApiView(APIView):

    # permission_classes = []

    def post(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)

        if user.subscriber.filter(author=author).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST)

        if user == author:
            return Response(
                {'errors': 'Невозможно подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST)

        subscription = Subscribe(user=user, author=author)
        subscription.save()
        serializer = SubscribeSerializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)

        if not user.subscriber.filter(author=author).exists():
            return Response(
                {'errors': 'Такой подписки не существует'},
                status=status.HTTP_400_BAD_REQUEST)

        subscription = get_object_or_404(Subscribe, user=user, author=author)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
