# myapp/middleware.py
import threading

_thread_locals = threading.local()

def get_current_user():
    """Récupère l'utilisateur courant stocké dans le thread local."""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """
    Middleware qui stocke l'utilisateur actuel dans le thread local
    pour qu'il soit accessible depuis n'importe où dans le code.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Stocke l'utilisateur dans le thread local
        _thread_locals.user = request.user if hasattr(request, 'user') else None
        
        response = self.get_response(request)
        
        # Nettoie après la réponse pour éviter les fuites de mémoire
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
            
        return response