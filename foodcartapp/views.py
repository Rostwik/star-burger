from django.http import JsonResponse
from django.templatetags.static import static

from .models import Product, Order, OrderItems
from rest_framework.decorators import api_view
from rest_framework.response import Response
import re


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    data = request.data
    print(data)
    pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    result = re.match(pattern, data['phonenumber'])
    print(bool(result))
    if not data.get('products') or not isinstance(data['products'], list):
        return Response({'error': 'products key are not presented or not list'})
    if not data.get('firstname') or not isinstance(data['firstname'], str):
        return Response({'error': 'The key "firstname" is not specified or not str'})
    elif not data.get('lastname') or not isinstance(data['lastname'], str):
        return Response({'error': 'The key "lastname" is not specified or not str'})
    elif not data.get('phonenumber') or not isinstance(data['phonenumber'], str) or bool(result) is not True:
        return Response({'error': 'The key "phonenumber" is not specified or not str'})
    elif not data.get('address') or not isinstance(data['address'], str):
        return Response({'error': 'The key "address" is not specified or not str'})

    order = Order.objects.create(
        firstname=data['firstname'],
        lastname=data['lastname'],
        phone_number=data['phonenumber'],
        address=data['address']
    )

    for product in data['products']:
        order_product = Product.objects.get(id=product['product'])
        OrderItems.objects.create(
            order=order,
            product=order_product,
            quantity=product['quantity']
        )

    return Response()
