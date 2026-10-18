# python manage.py test core
from django.test import TestCase
from django.urls import reverse

from .models import Product

from django.contrib.auth.models import User




class ProductCatalogTests(TestCase):
    def setUp(self):
        self.available_product = Product.objects.create(
            name="Mango Smoothie",
            description="Fresh mango smoothie",
            price="5.00",
            stock=10,
            is_available=True,
        )

        Product.objects.create(
            name="Out of Stock Juice",
            price="3.00",
            stock=0,
            is_available=True,
        )

        Product.objects.create(
            name="Unavailable Juice",
            price="4.00",
            stock=5,
            is_available=False,
        )

    def test_catalog_returns_success(self):
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)

    def test_catalog_shows_available_products(self):
        response = self.client.get(reverse("product_list"))
        self.assertContains(response, "Mango Smoothie")
        self.assertNotContains(response, "Out of Stock Juice")
        self.assertNotContains(response, "Unavailable Juice")

    def test_product_detail_displays_product(self):
        response = self.client.get(
            reverse(
                "product_detail",
                args=[self.available_product.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mango Smoothie")

    def test_unavailable_product_detail_returns_404(self):
        unavailable_product = Product.objects.get(
            name="Unavailable Juice"
        )
        response = self.client.get(
            reverse("product_detail", args=[unavailable_product.pk])
        )
        self.assertEqual(response.status_code, 404)



class AuthenticationTests(TestCase):
    def test_register_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_user_can_register(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "testcustomer",
                "password1": "StrongTestPass123!",
                "password2": "StrongTestPass123!",
            },
        )
        self.assertTrue(
            User.objects.filter(username="testcustomer").exists()
        )
        self.assertRedirects(response, reverse("home"))

    def test_user_can_login(self):
        User.objects.create_user(
            username="testcustomer",
            password="StrongTestPass123!",
        )
        response = self.client.post(
            reverse("login"),
            {
                "username": "testcustomer",
                "password": "StrongTestPass123!",
            },
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(
            "_auth_user_id" in self.client.session
        )

    def test_logout_requires_post(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

    def test_user_can_logout(self):
        User.objects.create_user(
            username="testcustomer",
            password="StrongTestPass123!",
        )
        self.client.login(
            username="testcustomer",
            password="StrongTestPass123!",
        )
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)
