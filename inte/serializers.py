
from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password
 
class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
 
    class Meta:
        model = User
        fields = ['name', 'email', 'organization', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
 
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
 
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        validated_data.pop('confirm_password')
        user = User.objects.create(**validated_data)
        return user
   
 