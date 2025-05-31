from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Min, Max
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Product, Category, Cart, CartItem, Size, Color

def store(request):
    """View for filtering products by size, color, category, and price range"""
    products = Product.objects.all()
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category')
    size_id = request.GET.get('size')
    color_id = request.GET.get('color')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Apply filters if they exist
    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    
    if category_id and category_id != 'all':
        products = products.filter(category_id=category_id)
        
    if size_id and size_id != 'all':
        products = products.filter(sizes__id=size_id)
        
    if color_id and color_id != 'all':
        products = products.filter(colors__id=color_id)
        
    # Filter by price range if provided
    if min_price:
        try:
            products = products.filter(sale_price__gte=float(min_price))
        except (ValueError, TypeError):
            pass  # Ignore invalid price values
            
    if max_price:
        try:
            products = products.filter(sale_price__lte=float(max_price))
        except (ValueError, TypeError):
            pass  # Ignore invalid price values
    
    # Get all categories, sizes and colors for the filter dropdowns
    categories = Category.objects.all()
    sizes = Size.objects.all()
    colors = Color.objects.all()
    
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
    """View for displaying a single product's details by ID"""
    product = get_object_or_404(Product, id=id)

    context = {
        'product': product,
    }
    return render(request, 'store/product_detail.html', context)

def product_detail_by_slug(request, slug):
    """View for displaying a single product's details by slug"""
    product = get_object_or_404(Product, slug=slug)

    context = {
        'product': product,
    }
    return render(request, 'store/product_detail.html', context)

def add_to_cart(request, product_id):
    """View for adding a product to the cart"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            quantity = int(request.POST.get('quantity', 1))
            size = request.POST.get('size')
            color = request.POST.get('color')
            
            # Validate required attributes if the product requires them
            if product.sizes.exists() and not size:
                raise ValueError("Please select a size for this product")
                
            if product.colors.exists() and not color:
                raise ValueError("Please select a color for this product")
                
            # Make sure the selected size and color are valid for this product
            if size and not product.sizes.filter(name=size).exists():
                raise ValueError(f"Size '{size}' is not available for this product")
                
            if color and not product.colors.filter(name=color).exists():
                raise ValueError(f"Color '{color}' is not available for this product")
            
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
            
            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                size=get_object_or_404(Size, name=size) if size else None,
                color=get_object_or_404(Color, name=color) if color else None,
                defaults={'quantity': quantity}
            )
            
            if not created:
                # Update quantity for existing item
                cart_item.quantity += quantity
                cart_item.save()
                message = f'Updated {product.name} quantity in your cart'
            else:
                message = f'Added {product.name} to your cart!'
            
            # Add details about size and color if they were selected
            details = []
            if size:
                details.append(f"Size: {size}")
            if color:
                details.append(f"Color: {color}")
            if details:
                message += f" ({', '.join(details)})"
                
            # Get total cart items for display
            cart_count = sum(item.quantity for item in cart.items.all())
                
            status = 'success'
        except ValueError as e:
            message = str(e)
            status = 'warning'
            cart_count = None
        except Exception as e:
            message = f'Error adding to cart: {str(e)}'
            status = 'error'
            cart_count = None
        
        # Return appropriate response
        if request.headers.get('HX-Request'):
            if status == 'success':
                bg_color, text_color, icon = 'green-100', 'green-800', '✓'
            elif status == 'warning':
                bg_color, text_color, icon = 'yellow-100', 'yellow-800', '⚠️'
            else:
                bg_color, text_color, icon = 'red-100', 'red-800', '✗'
            
            response_html = f'''
            <div class="bg-{bg_color} text-{text_color} p-3 rounded-md mb-4 flex items-center justify-between">
                <span><span class="font-bold mr-1">{icon}</span> {message}</span>
            '''  
            
            response_html += '</div>'
            
            return HttpResponse(
                response_html,
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
    
    # Check if this is an AJAX request from Alpine.js or an HTMX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    is_htmx = request.headers.get('HX-Request')
    
    if is_ajax:
        # For Alpine.js AJAX requests, return JSON response
        return JsonResponse({
            'success': status == 'success',
            'message': message,
            'cart_count': sum(item.quantity for item in cart.items.all()) if cart else 0,
            'cart_total': cart.get_total_price() if cart else 0
        })
    elif is_htmx:
        # For HTMX requests, return HTML fragment
        return render(request, 'partials/cart_items.html', {'cart': cart})
    
    # Add a message if not AJAX or HTMX request
    messages.success(request, message) if status == 'success' else messages.error(request, message)
    
    # Redirect back to the referring page
    return redirect(request.META.get('HTTP_REFERER', 'store'))


@require_GET
def cart_data(request):
    """API endpoint to get cart data in JSON format for Alpine.js"""
    # Get or create cart based on user or session
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    # Prepare cart data
    items_data = []
    for item in cart.items.all():
        # Get first image URL if available
        image_url = ''
        if item.product.images.exists():
            image_url = item.product.images.first().image.url
        
        # Format item details
        item_data = {
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'name': str(item),  # This should include product name and any variant info
            'quantity': item.quantity,
            'price': item.product.get_final_price(),
            'image_url': image_url,
            'total': item.get_total(),
            'product_url': item.product.get_absolute_url()
        }
        items_data.append(item_data)
    
    # Prepare response data
    data = {
        'items': items_data,
        'items_count': sum(item.quantity for item in cart.items.all()),
        'total_price': cart.get_total_price()
    }
    
    return JsonResponse(data)

