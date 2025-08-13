from fastapi import FastAPI, APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
import requests
import json
import hashlib


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Tea Shop API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SSLCommerz Configuration
class SSLCommerzConfig:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "sandbox")
        self.is_sandbox = self.environment == "sandbox"
        
        if self.is_sandbox:
            self.store_id = os.getenv("SSLCOMMERZ_SANDBOX_STORE_ID", "teststore123")
            self.store_password = os.getenv("SSLCOMMERZ_SANDBOX_STORE_PASSWORD", "testpassword")
            self.api_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
            self.validation_url = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
        else:
            self.store_id = os.getenv("SSLCOMMERZ_LIVE_STORE_ID")
            self.store_password = os.getenv("SSLCOMMERZ_LIVE_STORE_PASSWORD")
            self.api_url = "https://securepay.sslcommerz.com/gwprocess/v4/api.php"
            self.validation_url = "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"

sslcommerz_config = SSLCommerzConfig()

# Models
class TeaCategory(str, Enum):
    BLACK_TEA = "black_tea"
    GREEN_TEA = "green_tea"
    HERBAL_TEA = "herbal_tea"
    OOLONG_TEA = "oolong_tea"
    WHITE_TEA = "white_tea"
    SPECIALTY_BLEND = "specialty_blend"

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    price: float
    description: str
    content: str
    image_url: str
    category: TeaCategory
    inventory_count: int = 100
    is_available: bool = True
    weight_grams: int
    origin_country: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OrderItem(BaseModel):
    product_id: str
    product_title: str
    quantity: int
    unit_price: float
    total_price: float

class CustomerInfo(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    postal_code: str
    country: str = "Bangladesh"

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer: CustomerInfo
    items: List[OrderItem]
    subtotal: float
    shipping_cost: float = 50.0
    total_amount: float
    status: str = "pending"
    payment_status: str = "pending"
    transaction_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# SSLCommerz Service
class SSLCommerzService:
    def __init__(self, config: SSLCommerzConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'TeaShop-FastAPI/1.0'
        })
    
    def generate_transaction_id(self) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4().hex[:8])
        return f"TEA{timestamp}{random_part}"
    
    def create_payment_session(self, order: Order, success_url: str, 
                             fail_url: str, cancel_url: str, ipn_url: str) -> Dict[str, Any]:
        transaction_id = self.generate_transaction_id()
        
        payment_data = {
            'store_id': self.config.store_id,
            'store_passwd': self.config.store_password,
            'total_amount': str(order.total_amount),
            'currency': 'BDT',
            'tran_id': transaction_id,
            'success_url': success_url,
            'fail_url': fail_url,
            'cancel_url': cancel_url,
            'ipn_url': ipn_url,
            'cus_name': order.customer.name,
            'cus_email': order.customer.email,
            'cus_add1': order.customer.address_line1,
            'cus_add2': order.customer.address_line2 or '',
            'cus_city': order.customer.city,
            'cus_state': order.customer.city,
            'cus_postcode': order.customer.postal_code,
            'cus_country': order.customer.country,
            'cus_phone': order.customer.phone,
            'cus_fax': order.customer.phone,
            'product_name': 'Tea Shop Order',
            'product_category': 'Tea Products',
            'product_profile': 'general',
            'shipping_method': 'YES',
            'ship_name': order.customer.name,
            'ship_add1': order.customer.address_line1,
            'ship_add2': order.customer.address_line2 or '',
            'ship_city': order.customer.city,
            'ship_state': order.customer.city,
            'ship_postcode': order.customer.postal_code,
            'ship_country': order.customer.country,
            'value_a': order.id,
            'value_b': order.customer.email,
            'value_c': str(len(order.items)),
            'value_d': datetime.utcnow().isoformat(),
        }
        
        try:
            response = self.session.post(self.config.api_url, data=payment_data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'SUCCESS':
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'session_key': result.get('sessionkey'),
                    'gateway_url': result.get('GatewayPageURL'),
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('failedreason', 'Payment session creation failed'),
                    'data': result
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'data': None
            }

sslcommerz_service = SSLCommerzService(sslcommerz_config)

# Sample tea products data
SAMPLE_PRODUCTS = [
    {
        "title": "Earl Grey Premium",
        "price": 450.0,
        "description": "Classic Earl Grey with bergamot and cornflower petals",
        "content": "A timeless classic blend of Ceylon black tea scented with bergamot oil and adorned with beautiful cornflower petals. Perfect for afternoon tea service.",
        "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400",
        "category": "black_tea",
        "weight_grams": 100,
        "origin_country": "Sri Lanka"
    },
    {
        "title": "Dragon Well Green Tea",
        "price": 380.0,
        "description": "Delicate Chinese green tea with sweet, nutty flavor",
        "content": "Hand-picked Dragon Well (Longjing) green tea from the hills of Hangzhou. Known for its flat, sword-shaped leaves and refreshing taste.",
        "image_url": "https://images.unsplash.com/photo-1627435601361-ec25f5b1d0e5?w=400",
        "category": "green_tea",
        "weight_grams": 100,
        "origin_country": "China"
    },
    {
        "title": "Himalayan Gold",
        "price": 650.0,
        "description": "Premium high-altitude black tea from Nepal",
        "content": "Exceptional black tea grown at high altitudes in the Himalayas. Full-bodied with muscatel notes and golden liquor.",
        "image_url": "https://images.unsplash.com/photo-1597318759977-caeb0c3a5b37?w=400",
        "category": "black_tea",
        "weight_grams": 100,
        "origin_country": "Nepal"
    },
    {
        "title": "Chamomile Dream",
        "price": 320.0,
        "description": "Soothing herbal blend perfect for bedtime",
        "content": "Pure chamomile flowers combined with lavender and honey granules. Naturally caffeine-free and perfect for evening relaxation.",
        "image_url": "https://images.unsplash.com/photo-1556881286-5a5d1e7a4d4e?w=400",
        "category": "herbal_tea",
        "weight_grams": 100,
        "origin_country": "Egypt"
    },
    {
        "title": "Royal Oolong",
        "price": 520.0,
        "description": "Traditional Taiwanese oolong with floral notes",
        "content": "Semi-fermented oolong tea from high-mountain gardens in Taiwan. Complex flavor profile with orchid-like aroma and smooth finish.",
        "image_url": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=400",
        "category": "oolong_tea",
        "weight_grams": 100,
        "origin_country": "Taiwan"
    },
    {
        "title": "Silver Needle White Tea",
        "price": 750.0,
        "description": "Rare and delicate white tea with subtle sweetness",
        "content": "Premium white tea made from young silver buds. Light, subtle flavor with natural sweetness and minimal processing preserves antioxidants.",
        "image_url": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400",
        "category": "white_tea",
        "weight_grams": 100,
        "origin_country": "China"
    },
    {
        "title": "Royal Breakfast Blend",
        "price": 420.0,
        "description": "Robust morning blend of Assam and Ceylon teas",
        "content": "A hearty breakfast blend combining the best of Assam and Ceylon black teas. Strong, malty flavor that pairs perfectly with milk.",
        "image_url": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400",
        "category": "specialty_blend",
        "weight_grams": 100,
        "origin_country": "India"
    },
    {
        "title": "Jasmine Phoenix Pearls",
        "price": 580.0,
        "description": "Hand-rolled green tea scented with jasmine flowers",
        "content": "Green tea leaves hand-rolled into pearls and scented with fresh jasmine flowers. Aromatic and refreshing with floral undertones.",
        "image_url": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400",
        "category": "green_tea",
        "weight_grams": 100,
        "origin_country": "China"
    }
]

# Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to Tea Shop API"}

@api_router.get("/products", response_model=List[Product])
async def get_products():
    products = await db.products.find().to_list(1000)
    if not products:
        # Initialize with sample products if empty
        sample_products = [Product(**product) for product in SAMPLE_PRODUCTS]
        await db.products.insert_many([product.dict() for product in sample_products])
        products = await db.products.find().to_list(1000)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.get("/products/category/{category}")
async def get_products_by_category(category: TeaCategory):
    products = await db.products.find({"category": category}).to_list(1000)
    return [Product(**product) for product in products]

@api_router.post("/orders", response_model=Order)
async def create_order(order: Order):
    await db.orders.insert_one(order.dict())
    return order

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order(**order)

# Payment Routes
@api_router.post("/payments/initiate")
async def initiate_payment(order: Order, request: Request):
    try:
        if not order.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")
        
        if order.total_amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid order amount")
        
        # Save order to database
        await db.orders.insert_one(order.dict())
        
        # Generate callback URLs
        base_url = str(request.base_url).rstrip('/')
        success_url = f"{base_url}/api/payments/success"
        fail_url = f"{base_url}/api/payments/fail"
        cancel_url = f"{base_url}/api/payments/cancel"
        ipn_url = f"{base_url}/api/payments/ipn"
        
        # Create payment session
        session_result = sslcommerz_service.create_payment_session(
            order=order,
            success_url=success_url,
            fail_url=fail_url,
            cancel_url=cancel_url,
            ipn_url=ipn_url
        )
        
        if session_result['success']:
            # Update order with transaction ID
            await db.orders.update_one(
                {"id": order.id},
                {"$set": {"transaction_id": session_result['transaction_id']}}
            )
            
            logger.info(f"Payment session created: {session_result['transaction_id']}")
            
            return {
                'success': True,
                'transaction_id': session_result['transaction_id'],
                'gateway_url': session_result['gateway_url'],
                'session_key': session_result['session_key']
            }
        else:
            logger.error(f"Payment session creation failed: {session_result['error']}")
            raise HTTPException(status_code=400, detail=session_result['error'])
            
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment initiation failed")

@api_router.post("/payments/success")
async def payment_success(request: Request):
    try:
        form_data = await request.form()
        payment_data = dict(form_data)
        
        transaction_id = payment_data.get('tran_id')
        logger.info(f"Payment success callback received: {transaction_id}")
        
        # Update order status
        await db.orders.update_one(
            {"transaction_id": transaction_id},
            {"$set": {"payment_status": "completed", "status": "confirmed"}}
        )
        
        # Redirect to frontend success page
        frontend_success_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/payment/success?transaction_id={transaction_id}"
        return RedirectResponse(url=frontend_success_url, status_code=303)
        
    except Exception as e:
        logger.error(f"Payment success handling error: {str(e)}")
        frontend_error_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/payment/error"
        return RedirectResponse(url=frontend_error_url, status_code=303)

@api_router.post("/payments/fail")
async def payment_fail(request: Request):
    try:
        form_data = await request.form()
        payment_data = dict(form_data)
        
        transaction_id = payment_data.get('tran_id')
        logger.warning(f"Payment failed callback received: {transaction_id}")
        
        # Update order status
        await db.orders.update_one(
            {"transaction_id": transaction_id},
            {"$set": {"payment_status": "failed", "status": "cancelled"}}
        )
        
        # Redirect to frontend failure page
        frontend_fail_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/payment/failed?transaction_id={transaction_id}"
        return RedirectResponse(url=frontend_fail_url, status_code=303)
        
    except Exception as e:
        logger.error(f"Payment failure handling error: {str(e)}")
        frontend_error_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/payment/error"
        return RedirectResponse(url=frontend_error_url, status_code=303)

@api_router.post("/payments/cancel")
async def payment_cancel(request: Request):
    try:
        form_data = await request.form()
        payment_data = dict(form_data)
        
        transaction_id = payment_data.get('tran_id')
        logger.info(f"Payment cancelled callback received: {transaction_id}")
        
        # Update order status
        await db.orders.update_one(
            {"transaction_id": transaction_id},
            {"$set": {"payment_status": "cancelled", "status": "cancelled"}}
        )
        
        # Redirect to frontend cancellation page
        frontend_cancel_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/payment/cancelled?transaction_id={transaction_id}"
        return RedirectResponse(url=frontend_cancel_url, status_code=303)
        
    except Exception as e:
        logger.error(f"Payment cancellation handling error: {str(e)}")
        frontend_error_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/payment/error"
        return RedirectResponse(url=frontend_error_url, status_code=303)

@api_router.get("/payments/status/{transaction_id}")
async def get_payment_status(transaction_id: str):
    try:
        order = await db.orders.find_one({"transaction_id": transaction_id})
        if not order:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {
            "transaction_id": transaction_id,
            "status": order.get("payment_status", "pending"),
            "amount": order.get("total_amount", 0),
            "currency": "BDT"
        }
    except Exception as e:
        logger.error(f"Status retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Status retrieval failed")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()