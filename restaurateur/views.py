from operator import itemgetter

from django import forms
from django.conf import settings
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from geopy import distance

from foodcartapp.models import Product, Restaurant, Order
from geotools.geolocation_tools import fetch_coordinates
from geotools.models import Location
from star_burger.settings import YANDEX_API


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    restaurants = Restaurant.objects.prefetch_related('menu_items')
    restaurants_menus = {}
    for restaurant in restaurants:
        restaurant_menu = [dish.product for dish in restaurant.menu_items.all()]
        restaurants_menus[restaurant] = restaurant_menu

    orders = list(Order.objects.exclude(status__in=['з']).calculate_order_sum())

    for order in orders:
        if order.address != order.location.address:
            location, is_created = Location.objects.get_or_create(address=order.address)
            if is_created:
                customer_coordinates = fetch_coordinates(
                    settings.YANDEX_API,
                    order.address
                )
                if customer_coordinates:
                    location.long, location.lat = customer_coordinates
                    location.save()
                    order.location = location
                    order.save()
                else:
                    location.long, location.lat = None, None
                    location.save()
        customer_coordinates = order.location.lat, order.location.long
        relevant_restaurants = []
        order_items = [item.product for item in order.order_items.all()]
        for restaurant, menu in restaurants_menus.items():
            if set(order_items) <= set(menu):
                restaurant_coordinates = restaurant.location.lat, restaurant.location.long
                if restaurant_coordinates and customer_coordinates:
                    restaurant_distance = distance.distance(restaurant_coordinates, customer_coordinates).km
                    relevant_restaurants.append((restaurant, restaurant_distance))
                else:
                    relevant_restaurants.append((restaurant, 'ошибка определения координат'))
        order.relevant_restaurants = sorted(relevant_restaurants, key=itemgetter(1))

    return render(request, template_name='orders.html', context={
        "orders": orders
    })
