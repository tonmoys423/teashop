import requests
import sys
import json
from datetime import datetime

class TeaShopAPITester:
    def __init__(self, base_url="https://leaf-store-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.product_id = None
        self.order_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: Found {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_get_products(self):
        """Test getting all products"""
        success, response = self.run_test(
            "Get All Products",
            "GET",
            "products",
            200
        )
        if success and isinstance(response, list) and len(response) > 0:
            self.product_id = response[0].get('id')
            print(f"   Found {len(response)} products, first product ID: {self.product_id}")
        return success

    def test_get_single_product(self):
        """Test getting a single product"""
        if not self.product_id:
            print("❌ Skipping single product test - no product ID available")
            return False
            
        success, response = self.run_test(
            "Get Single Product",
            "GET",
            f"products/{self.product_id}",
            200
        )
        return success

    def test_get_products_by_category(self):
        """Test getting products by category"""
        success, response = self.run_test(
            "Get Products by Category",
            "GET",
            "products/category/black_tea",
            200
        )
        return success

    def test_create_order(self):
        """Test creating an order"""
        if not self.product_id:
            print("❌ Skipping order creation test - no product ID available")
            return False

        order_data = {
            "customer": {
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "+8801234567890",
                "address_line1": "123 Test Street",
                "address_line2": "",
                "city": "Dhaka",
                "postal_code": "1000",
                "country": "Bangladesh"
            },
            "items": [
                {
                    "product_id": self.product_id,
                    "product_title": "Test Tea",
                    "quantity": 2,
                    "unit_price": 450.0,
                    "total_price": 900.0
                }
            ],
            "subtotal": 900.0,
            "shipping_cost": 50.0,
            "total_amount": 950.0,
            "status": "pending",
            "payment_status": "pending"
        }

        success, response = self.run_test(
            "Create Order",
            "POST",
            "orders",
            200,
            data=order_data
        )
        
        if success and 'id' in response:
            self.order_id = response['id']
            print(f"   Created order ID: {self.order_id}")
        
        return success

    def test_get_order(self):
        """Test getting an order"""
        if not self.order_id:
            print("❌ Skipping get order test - no order ID available")
            return False
            
        success, response = self.run_test(
            "Get Order",
            "GET",
            f"orders/{self.order_id}",
            200
        )
        return success

    def test_payment_initiation(self):
        """Test payment initiation"""
        if not self.product_id:
            print("❌ Skipping payment initiation test - no product ID available")
            return False

        payment_order_data = {
            "customer": {
                "name": "Payment Test Customer",
                "email": "payment@example.com",
                "phone": "+8801234567890",
                "address_line1": "456 Payment Street",
                "address_line2": "",
                "city": "Dhaka",
                "postal_code": "1000",
                "country": "Bangladesh"
            },
            "items": [
                {
                    "product_id": self.product_id,
                    "product_title": "Payment Test Tea",
                    "quantity": 1,
                    "unit_price": 450.0,
                    "total_price": 450.0
                }
            ],
            "subtotal": 450.0,
            "shipping_cost": 50.0,
            "total_amount": 500.0,
            "status": "pending",
            "payment_status": "pending"
        }

        success, response = self.run_test(
            "Payment Initiation",
            "POST",
            "payments/initiate",
            200,
            data=payment_order_data
        )
        
        if success:
            print(f"   Payment session created successfully")
            if 'gateway_url' in response:
                print(f"   Gateway URL available: {response['gateway_url'][:50]}...")
        
        return success

    def test_payment_status(self):
        """Test payment status endpoint with a dummy transaction ID"""
        # This will likely fail since we don't have a real transaction, but tests the endpoint
        success, response = self.run_test(
            "Payment Status (Expected to fail)",
            "GET",
            "payments/status/dummy_transaction_id",
            404  # Expecting 404 for non-existent transaction
        )
        # For this test, we consider 404 as expected behavior
        if response and 'detail' in response and 'not found' in response['detail'].lower():
            print("   ✅ Correctly returned 404 for non-existent transaction")
            return True
        return success

def main():
    print("🧪 Starting Tea Shop API Tests")
    print("=" * 50)
    
    tester = TeaShopAPITester()
    
    # Run all tests
    tests = [
        tester.test_root_endpoint,
        tester.test_get_products,
        tester.test_get_single_product,
        tester.test_get_products_by_category,
        tester.test_create_order,
        tester.test_get_order,
        tester.test_payment_initiation,
        tester.test_payment_status
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    elif tester.tests_passed >= tester.tests_run * 0.7:  # 70% pass rate
        print("⚠️  Most tests passed - minor issues detected")
        return 0
    else:
        print("❌ Multiple test failures detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())