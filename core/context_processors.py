from .models import Cart

def cart_count_context(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            return {'global_cart_count': cart.total_count}
    return {'global_cart_count': 0}