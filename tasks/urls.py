from rest_framework import routers
from .api import TaskViewSet

routers = routers.DefaultRouter()

routers.register('api/v1/tasks', TaskViewSet, 'tasks')
 
urlpatterns = routers.urls
