from rest_framework import viewsets, permissions
from .models import Task
from .serializers import TaskSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_queryset(self):
            return Task.objects.filter(username=self.request.user)

    @action(detail=True, methods=['patch'])
    def done(self, request, pk=None):
        '''
        Custom actions, detail especifica si sera usada para todas las instancias.
        '''

        task = self.get_object()
        
        task.done = not task.done

        task.save()

        return Response({
            'status': 'Task done' if task.done else 'Task undone'
        }, status=status.HTTP_200_OK)
