from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

class RegistarSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=3, max_length=100)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=True, validators=[validate_password])
    conform_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=True)
    email = serializers.EmailField(required=True)
    
    
    def validate(self, data):
        if data['password'] != data['conform_password']:
            raise serializers.ValidationError(
                "Password and Confirm Password do not match"
            )

        data.pop('conform_password')
        return data

class EmailCheckSerializer(serializers.Serializer):
    uid = serializers.CharField()
    pincode = serializers.IntegerField()