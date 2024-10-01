from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import CustomUser

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        
        if user is None:
            raise serializers.ValidationError('無効なユーザー名またはパスワードです。')
        
        attrs['user'] = user
        return attrs
