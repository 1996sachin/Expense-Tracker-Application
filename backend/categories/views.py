from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category
from .serializers import CategorySerializer
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class=CategorySerializer
    def get_queryset(self): return Category.objects.filter(user=self.request.user) | Category.objects.filter(user__isnull=True)
    def perform_destroy(self, instance):
        if instance.user_id is None:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Default categories cannot be deleted.')
        instance.delete()
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        ids = request.data.get('ids', [])
        owned = {str(c.id): c for c in Category.objects.filter(user=request.user, id__in=ids)}
        if len(owned) != len(ids): return Response({'detail': 'Only your custom categories can be reordered.'}, status=status.HTTP_400_BAD_REQUEST)
        for position, category_id in enumerate(ids):
            category = owned[str(category_id)]; category.position = position; category.save(update_fields=['position'])
        return Response(CategorySerializer(Category.objects.filter(user=request.user).order_by('type', 'position', 'name'), many=True).data)
