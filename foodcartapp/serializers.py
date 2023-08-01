from rest_framework.serializers import ModelSerializer, ListField
from django.conf import settings
from foodcartapp.models import OrderItems, Order
from geotools.geolocation_tools import fetch_coordinates
from geotools.models import Location


class OrderItemsSerializer(ModelSerializer):
    class Meta:
        model = OrderItems
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = ListField(child=OrderItemsSerializer(), allow_empty=False, write_only=True)

    def create(self, validated_data):
        products = validated_data.pop('products')
        address = validated_data['address']

        location, is_created = Location.objects.get_or_create(address=address)
        if is_created:
            customer_coordinates = fetch_coordinates(
                settings.YANDEX_API,
                address
            )
            if customer_coordinates:
                location.long, location.lat = customer_coordinates
                location.save()
            else:
                location.long, location.lat = None, None
                location.save()

        order = Order.objects.create(**validated_data)

        order_items = [
            OrderItems(
                product=product['product'],
                order=order,
                quantity=product['quantity'])
            for product in products
        ]
        OrderItems.objects.bulk_create(order_items)

        return order

    class Meta:
        model = Order
        fields = ['id', 'products', 'firstname', 'lastname', 'phonenumber', 'address']
