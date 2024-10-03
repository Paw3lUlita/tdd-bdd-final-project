# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Change it an save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_deserialize_invalid_type_for_available(self):
        """It should raise a DataValidationError for invalid type for 'available'"""
        data = {
            "name": "Fedora",
            "description": "A red hat",
            "price": "12.50",
            "available": "yes",  # Invalid type: should be a boolean
            "category": "CLOTHS"
        }
        product = Product()
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(data)
        self.assertEqual(
            str(context.exception),
            "Invalid type for boolean [available]: <class 'str'>"
        )

    def test_deserialize_missing_name(self):
        """It should raise a DataValidationError for missing name"""
        data = {
            "description": "A red hat",
            "price": "12.50",
            "available": True,
            "category": "CLOTHS"
        }
        product = Product()
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(data)
        self.assertEqual(str(context.exception), "Invalid product: missing name")

    def test_deserialize_missing_description(self):
        """It should raise a DataValidationError for missing description"""
        data = {
            "name": "Fedora",
            "price": "12.50",
            "available": True,
            "category": "CLOTHS"
        }
        product = Product()
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(data)
        self.assertEqual(str(context.exception), "Invalid product: missing description")

    def test_deserialize_invalid_category(self):
        """It should raise a DataValidationError for an invalid category"""
        data = {
            "name": "Fedora",
            "description": "A red hat",
            "price": "12.50",
            "available": True,
            "category": "INVALID_CATEGORY"  # Invalid category
        }
        product = Product()
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(data)
        self.assertEqual(str(context.exception), "Invalid attribute: INVALID_CATEGORY")

    def test_update_product_without_id(self):
        """It should raise a DataValidationError when updating without ID"""
        product = ProductFactory()
        product.id = None
        with self.assertRaises(DataValidationError) as context:
            product.update()
        self.assertEqual(str(context.exception), "Update called with empty ID field")

    def test_find_by_price_existing(self):
        """It should Find Products by Existing Price"""
        # Create products with known prices
        product1 = ProductFactory(price=Decimal('9.99'))
        product2 = ProductFactory(price=Decimal('19.99'))
        product3 = ProductFactory(price=Decimal('9.99'))  # Same price as product1

        # Add products to the database
        product1.create()
        product2.create()
        product3.create()

        # Find products by price
        found_products = Product.find_by_price(Decimal('9.99')).all()
        
        # Assert that the correct number of products is returned
        self.assertEqual(len(found_products), 2)  # Should find both product1 and product3
        self.assertIn(product1, found_products)    # Check if product1 is in the results
        self.assertIn(product3, found_products)    # Check if product3 is in the results

    def test_find_by_price_non_existing(self):
        """It should Return No Products for Non-Existing Price"""
        # Create some products
        product1 = ProductFactory(price=Decimal('9.99'))
        product1.create()

        # Try to find a price that doesn't exist
        found_products = Product.find_by_price(Decimal('29.99')).all()

        # Assert that no products are found
        self.assertEqual(len(found_products), 0)  # Should return an empty list
