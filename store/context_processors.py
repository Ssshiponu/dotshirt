from .models import Cart

def cart_processor(request):
    """
    Context processor that adds cart information to all templates
    """
    cart = None
    
    # Get cart based on user or session
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    elif hasattr(request, 'session') and request.session.session_key:
        session_id = request.session.session_key
        try:
            cart = Cart.objects.get(session_id=session_id)
        except Cart.DoesNotExist:
            # No cart yet
            pass
    
    return {'cart': cart}
