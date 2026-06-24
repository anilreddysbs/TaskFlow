import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('taskflow')

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.correlation_id = str(uuid.uuid4())
        logger.info(
            f"Request {request.method} {request.path}",
            extra={
                'correlation_id': request.correlation_id,
                'user': str(request.user) if hasattr(request, 'user') else 'AnonymousUser',
                'ip': self.get_client_ip(request),
            }
        )

    def process_response(self, request, response):
        logger.info(
            f"Response {response.status_code} {request.path}",
            extra={
                'correlation_id': getattr(request, 'correlation_id', 'N/A'),
                'status': response.status_code,
            }
        )
        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

