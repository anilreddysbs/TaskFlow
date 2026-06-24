from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TeamViewSet, MeAPIView, ProjectViewSet, TaskViewSet, CommentViewSet, HealthCheckView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = router.urls + [
    path('health/', HealthCheckView.as_view(), name='health'),
    path('me/', MeAPIView.as_view(), name='me'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

