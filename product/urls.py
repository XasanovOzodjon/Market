from django.urls import path
from .views import ProductListCreateView, ProductDetailView, GetAllCategories, GetProductsByCategory, SetProductPublish, SetProductArchive, SetProductSold, FavoritesView, ProductImageUploadView

urlpatterns = [
    path('categories/', GetAllCategories.as_view(), name='category-list'),
    path('categories/<slug:slug>/', GetAllCategories.as_view(), name='category-detail'),
    path('categories/<slug:slug>/products/', GetProductsByCategory.as_view(), name='category-products'),
    
    
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/publish/', SetProductPublish.as_view(), name="product-set-public"),
    path('products/<int:pk>/archive/', SetProductArchive.as_view(), name="product-set-archive"),
    path('products/<int:pk>/sold/', SetProductSold.as_view(), name="product-set-sold"),
    path('products/<int:product_id>/images/', ProductImageUploadView.as_view(), name='product-image-upload'),
    

    path('favorites/', FavoritesView.as_view(), name='favorite-list-create'),
    path('favorites/<int:pk>/', FavoritesView.as_view(), name='favorite-detail'),


]