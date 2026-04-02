from rest_framework import serializers
from .models import SellerProfile


class SellerProfileSerializer(serializers.ModelSerializer):
    shop_logo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = SellerProfile
        fields = [
            'id',
            'shop_name',
            'shop_description',
            'shop_logo',
            'region',
            'district',
            'adress',
            'rating',
            'total_sales',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'rating',
            'total_sales',
            'created_at',
            'updated_at'
        ]