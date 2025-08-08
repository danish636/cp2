from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import date

class UserSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['is_admin'] = user.is_admin
        token['prime_user'] = user.prime_user
        token['trail'] = (date.today() - user.created_at).days <= 14
        token['trail_days'] = (date.today() - user.created_at).days
        token['is_subscribed'] = user.is_subscribed
        token['email'] = user.email
        # print(token.name)
        return token

    def validate(self, attrs):
        request = self.context["request"]
        request_data = request.data
        data = super(UserSerializer, self).validate(attrs)
        return data
    
    
class UserCustomSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = ["email","first_name","middle_name","last_name","phone_number"]
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

class UserDcfCalculatorFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDcfCalculatorFilter
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

class UserScreenerFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserScreenerFilter
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"
        # fields = ['courseId', 'courseName', 'author', 'courseDescription', 'image']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPortfolio
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)