from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static

from geotools.geolocation_tools import fetch_coordinates
from geotools.models import Location
from .models import Product, Order, OrderItems
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, ListField


class OrderItemsSerializer(ModelSerializer):
    class Meta:
        model = OrderItems
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = ListField(child=OrderItemsSerializer(), allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'products', 'firstname', 'lastname', 'phonenumber', 'address']


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
@transaction.atomic
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_order = serializer.validated_data

    location, is_created = Location.objects.get_or_create(address=validated_order['address'])
    if is_created:
        customer_coordinates = fetch_coordinates(
            settings.YANDEX_API,
            validated_order['address']
        )
        if customer_coordinates:
            location.long, location.lat = customer_coordinates
            location.save()
        else:
            location.long, location.lat = None, None
            location.save()

    order = Order.objects.create(
        firstname=validated_order['firstname'],
        lastname=validated_order['lastname'],
        phonenumber=validated_order['phonenumber'],
        address=validated_order['address'],
        location=location
    )

    order_items = [
        OrderItems(
            product=product['product'],
            order=order,
            quantity=product['quantity'])
        for product in validated_order['products']
    ]
    OrderItems.objects.bulk_create(order_items)

    serializer = OrderSerializer(order, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)
