import django_filters
from tasks.models import Task


class TaskFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    priority = django_filters.CharFilter(field_name='priority', lookup_expr='iexact')
    assigned_to = django_filters.NumberFilter(field_name='assigned_to_id')
    project = django_filters.NumberFilter(field_name='project_id')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'assigned_to', 'project']
