from rest_framework import viewsets
from .models import Category
from .serializers import CategorySerializer
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class=CategorySerializer
    def get_queryset(self): return Category.objects.filter(user=self.request.user) | Category.objects.filter(user__isnull=True)
