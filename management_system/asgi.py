import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'management_system.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

from channels.routing import ProtocolTypeRouter, URLRouter

# import chat.routing
import notification.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notification.routing.websocket_urlpatterns
        )
    )
})
