from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Entity

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ['object_id', 'name', 'description', 'address', 'status']

class UserSerializer(serializers.ModelSerializer):
    entity = EntitySerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['object_id', 'email', 'first_name', 'last_name', 'phone_number', 
                  'address', 'status', 'entity', 'created_date']
        read_only_fields = ['object_id', 'created_date']

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email', '')
        password = data.get('password', '')
        
        if email and password:
            user = authenticate(email=email, password=password)
            
            if user:
                if not user.status == 'active':
                    raise serializers.ValidationError("User account is not active.")
                
                refresh = RefreshToken.for_user(user)
                
                data = {
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                return data
            else:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")
