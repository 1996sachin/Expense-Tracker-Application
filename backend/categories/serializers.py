from rest_framework import serializers
from .models import Category
class CategorySerializer(serializers.ModelSerializer):
    class Meta: model=Category; fields='__all__'; read_only_fields=['user']
    def create(self,data): data['user']=self.context['request'].user; return super().create(data)
