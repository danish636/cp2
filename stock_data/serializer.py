from rest_framework import serializers
from .models import Industry_report, General_topic, Macroeconomics, Blog


class Industryreportserializer(serializers.ModelSerializer):
    class Meta:
        model = Industry_report
        fields = "__all__"

class Generaltopicserializer(serializers.ModelSerializer):
    class Meta:
        model = General_topic
        fields = "__all__"

class Blogserializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = "__all__"

class AllBlogserializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ("id", "Blog_heading")
        
class Macroeconomictopicserializer(serializers.ModelSerializer):
    class Meta:
        model = Macroeconomics
        fields = "__all__"