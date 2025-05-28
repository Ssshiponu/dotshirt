from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Min, Max
from .models import Product, Category, Cart, CartItem

# Create your views here.

def store(request):
    """View for the main store page displaying all products"""
    products = Product.objects.all()
    categories = Category.objects.all()

    # Get price range for filter
    price_range = Product.objects.aggregate(min_price=Min('price'), max_price=Max('price'))
    
    context = {
        'products': products,
        'categories': categories,
        'price_range': price_range,
    }
    return render(request, 'store/store.html', context)

def filter_products(request):
    """View for filtering products by size, color, category, and price range"""
    products = Product.objects.all()
    
    # Get filter parameters
    category_id = request.GET.get('category')
    size_id = request.GET.get('size')
    color_id = request.GET.get('color')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Apply filters if they exist
    if category_id and category_id != 'all':
        products = products.filter(category_id=category_id)
        
    if size_id and size_id != 'all':
        products = products.filter(sizes__id=size_id)
        
    if color_id and color_id != 'all':
        products = products.filter(colors__id=color_id)
        
    # Filter by price range if provided
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass  # Ignore invalid price values
            
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass  # Ignore invalid price values
    
    # Get all categories, sizes and colors for the filter dropdowns
    categories = Category.objects.all()
    sizes = Size.objects.all()
    colors = Color.objects.all()
    
    # If this is an HTMX request, return only the product grid
    if request.headers.get('HX-Request'):
        return render(request, 'store/product_grid.html', {'products': products})
    
    # For a regular request, return the complete page with filter options
    context = {
        'products': products,
        'categories': categories,
        'sizes': sizes,
        'colors': colors,
        'selected_category': category_id,
        'selected_size': size_id,
        'selected_color': color_id,
        'min_price': min_price,
        'max_price': max_price
    }
    
    return render(request, 'store/store.html', context)

def product_detail(request, id):
    """View for displaying a single product's details"""
    product = get_object_or_404(Product, id=id)
    
    context = {
        'product': product,
    }
    return render(request, 'store/product_detail.html', context)

def category(request, id):
    """View for displaying products by category"""
    category = get_object_or_404(Category, id=id)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()
    
    context = {
        'category': category,
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/store.html', context)

def search(request):
    """View for searching products"""
    query = request.GET.get('search', '')
    
    if query:
        # Search in product name and description
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query)
        )
    else:
        products = Product.objects.all()
    
    # If the request is HTMX, return only the product grid
    if request.headers.get('HX-Request'):
        return render(request, 'store/product_grid.html', {'products': products})
    
    # Otherwise return the full store page
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
        'search_query': query,
    }
    return render(request, 'store/store.html', context)

def add_to_cart(request, product_id):
    """View for adding a product to the cart"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            quantity = int(request.POST.get('quantity', 1))
            
            # Get or create cart based on session or user
            cart = None
            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                session_id = request.session.session_key
                if not session_id:
                    request.session.create()
                    session_id = request.session.session_key
                cart, created = Cart.objects.get_or_create(session_id=session_id)
            
            # Fix indentation - this should be outside the else block
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': 0}
            )
            
            # Update quantity
            cart_item.quantity += quantity
            cart_item.save()
            
            message = f'Added {product.name} to cart!'
            status = 'success'
        except Exception as e:
            message = f'Error adding to cart: {str(e)}'
            status = 'error'
        
        # Return appropriate response
        if request.headers.get('HX-Request'):
            bg_color = 'green-100' if status == 'success' else 'red-100'
            text_color = 'green-800' if status == 'success' else 'red-800'
            
            return HttpResponse(
                f'<div class="bg-{bg_color} text-{text_color} p-2 rounded mb-4">{message}</div>',
                content_type='text/html'
            )
        
        # Redirect to product page if not HTMX request
        return redirect('product_detail', id=product_id)
    
    # Handle GET request (should not happen)
    return redirect('store')


def remove_from_cart(request, item_id):
    """View for removing an item from the cart"""
    try:
        # First try to get the item based on the user's authentication status
        cart_item = None
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        else:
            session_id = request.session.session_key
            if session_id:
                cart_item = CartItem.objects.get(id=item_id, cart__session_id=session_id)
        
        # If we found the item, remove it
        if cart_item:
            product_name = cart_item.product.name
            cart_item.delete()
            message = f'Removed {product_name} from cart'
            status = 'success'
        else:
            message = 'Item not found in your cart'
            status = 'error'
    except CartItem.DoesNotExist:
        message = 'Item not found in your cart'
        status = 'error'
    except Exception as e:
        message = f'Error removing from cart: {str(e)}'
        status = 'error'
    
    # Get the updated cart items to refresh the cart view
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if session_id:
            cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    # Return appropriate response for HTMX
    if request.headers.get('HX-Request'):
        return render(request, 'partials/cart_items.html', {'cart': cart})
    
    # Add a message if not HTMX request
    messages.success(request, message) if status == 'success' else messages.error(request, message)
    
    # Redirect back to the referring page
    return redirect(request.META.get('HTTP_REFERER', 'store'))

