#import Serializers
from rest_framework import serializers
#import User models
from .models import User

#define User Class
class UserSerializer(serializers.ModelSerializer):
    #Set password serializers
    password = serializers.CharField(write_only=True)
    #define meta class
    class Meta:
        model = User
        fields = (
            'username',
            'password',
            'phone',
            'address',
            'gender',
            'age',
            'description',
            'first_name',
            'last_name',
            'email'
        )
    #define creating user function
    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        #hashing password for validation
        user.set_password(validated_data['password'])
        user.save()
        return user
