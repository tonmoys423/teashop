import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { ShoppingCart, Plus, Minus, Leaf, Search, User, Heart, Star } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Cart Context
const CartContext = createContext();

const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);

  const addToCart = (product, quantity = 1) => {
    setCartItems(prev => {
      const existingItem = prev.find(item => item.id === product.id);
      if (existingItem) {
        return prev.map(item => 
          item.id === product.id 
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [...prev, { ...product, quantity }];
    });
  };

  const removeFromCart = (productId) => {
    setCartItems(prev => prev.filter(item => item.id !== productId));
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId);
    } else {
      setCartItems(prev => 
        prev.map(item => 
          item.id === productId ? { ...item, quantity } : item
        )
      );
    }
  };

  const clearCart = () => {
    setCartItems([]);
  };

  const getTotalAmount = () => {
    return cartItems.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const getTotalItems = () => {
    return cartItems.reduce((total, item) => total + item.quantity, 0);
  };

  return (
    <CartContext.Provider value={{
      cartItems,
      addToCart,
      removeFromCart,
      updateQuantity,
      clearCart,
      getTotalAmount,
      getTotalItems
    }}>
      {children}
    </CartContext.Provider>
  );
};

const useCart = () => useContext(CartContext);

// Header Component
const Header = () => {
  const navigate = useNavigate();
  const { getTotalItems } = useCart();
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo" onClick={() => navigate("/")}>
          <Leaf className="logo-icon" />
          <span>TeaLeaf</span>
        </div>
        
        <div className="search-bar">
          <Search className="search-icon" />
          <input
            type="text"
            placeholder="Search premium teas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <nav className="nav-menu">
          <button onClick={() => navigate("/")} className="nav-button">Shop</button>
          <button onClick={() => navigate("/about")} className="nav-button">About</button>
          <button onClick={() => navigate("/contact")} className="nav-button">Contact</button>
        </nav>

        <div className="header-actions">
          <button className="action-button">
            <Heart size={20} />
          </button>
          <button className="action-button">
            <User size={20} />
          </button>
          <button className="cart-button" onClick={() => navigate("/cart")}>
            <ShoppingCart size={20} />
            {getTotalItems() > 0 && <span className="cart-count">{getTotalItems()}</span>}
          </button>
        </div>
      </div>
    </header>
  );
};

// Product Card Component
const ProductCard = ({ product }) => {
  const { addToCart } = useCart();
  const navigate = useNavigate();

  const handleAddToCart = (e) => {
    e.stopPropagation();
    addToCart(product);
  };

  return (
    <div className="product-card" onClick={() => navigate(`/product/${product.id}`)}>
      <div className="product-image">
        <img src={product.image_url} alt={product.title} />
        <div className="product-overlay">
          <button className="quick-add-btn" onClick={handleAddToCart}>
            <Plus size={16} />
            Quick Add
          </button>
        </div>
      </div>
      <div className="product-info">
        <div className="product-category">{product.category.replace('_', ' ').toUpperCase()}</div>
        <h3 className="product-title">{product.title}</h3>
        <p className="product-description">{product.description}</p>
        <div className="product-rating">
          <div className="stars">
            {[...Array(5)].map((_, i) => (
              <Star key={i} size={14} className="star filled" />
            ))}
          </div>
          <span className="rating-count">(24)</span>
        </div>
        <div className="product-footer">
          <div className="price">৳{product.price}</div>
          <button className="add-to-cart-btn" onClick={handleAddToCart}>
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
};

// Home Page
const Home = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await axios.get(`${API}/products`);
        setProducts(response.data);
      } catch (error) {
        console.error("Failed to fetch products:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading premium teas...</p>
      </div>
    );
  }

  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            Premium Tea Collection
            <span className="accent">From Around the World</span>
          </h1>
          <p className="hero-subtitle">
            Discover our carefully curated selection of the finest teas, 
            sourced directly from the world's best tea gardens.
          </p>
          <button className="cta-button">
            <Leaf size={20} />
            Explore Collection
          </button>
        </div>
        <div className="hero-image">
          <img src="https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=600" alt="Premium Tea" />
        </div>
      </section>

      <section className="categories">
        <h2 className="section-title">Shop by Category</h2>
        <div className="category-grid">
          {[
            { name: "Black Tea", image: "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=300", count: "12 varieties" },
            { name: "Green Tea", image: "https://images.unsplash.com/photo-1627435601361-ec25f5b1d0e5?w=300", count: "8 varieties" },
            { name: "Herbal Tea", image: "https://images.unsplash.com/photo-1556881286-5a5d1e7a4d4e?w=300", count: "15 varieties" },
            { name: "White Tea", image: "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=300", count: "6 varieties" }
          ].map((category) => (
            <div key={category.name} className="category-card">
              <img src={category.image} alt={category.name} />
              <div className="category-info">
                <h3>{category.name}</h3>
                <p>{category.count}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="products">
        <h2 className="section-title">Featured Products</h2>
        <div className="products-grid">
          {products.slice(0, 8).map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>
    </div>
  );
};

// Cart Page
const CartPage = () => {
  const { cartItems, updateQuantity, removeFromCart, getTotalAmount } = useCart();
  const navigate = useNavigate();

  if (cartItems.length === 0) {
    return (
      <div className="empty-cart">
        <div className="empty-cart-content">
          <ShoppingCart size={64} className="empty-cart-icon" />
          <h2>Your cart is empty</h2>
          <p>Start shopping to add items to your cart</p>
          <button className="cta-button" onClick={() => navigate("/")}>
            Continue Shopping
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="cart-page">
      <h1 className="page-title">Shopping Cart</h1>
      <div className="cart-content">
        <div className="cart-items">
          {cartItems.map(item => (
            <div key={item.id} className="cart-item">
              <img src={item.image_url} alt={item.title} className="cart-item-image" />
              <div className="cart-item-info">
                <h3>{item.title}</h3>
                <p className="cart-item-category">{item.category.replace('_', ' ')}</p>
                <div className="cart-item-price">৳{item.price}</div>
              </div>
              <div className="cart-item-controls">
                <div className="quantity-controls">
                  <button onClick={() => updateQuantity(item.id, item.quantity - 1)}>
                    <Minus size={16} />
                  </button>
                  <span className="quantity">{item.quantity}</span>
                  <button onClick={() => updateQuantity(item.id, item.quantity + 1)}>
                    <Plus size={16} />
                  </button>
                </div>
                <div className="cart-item-total">৳{(item.price * item.quantity).toFixed(2)}</div>
                <button 
                  className="remove-button"
                  onClick={() => removeFromCart(item.id)}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
        
        <div className="cart-summary">
          <h3>Order Summary</h3>
          <div className="summary-row">
            <span>Subtotal:</span>
            <span>৳{getTotalAmount().toFixed(2)}</span>
          </div>
          <div className="summary-row">
            <span>Shipping:</span>
            <span>৳50.00</span>
          </div>
          <div className="summary-row total">
            <span>Total:</span>
            <span>৳{(getTotalAmount() + 50).toFixed(2)}</span>
          </div>
          <button 
            className="checkout-button"
            onClick={() => navigate("/checkout")}
          >
            Proceed to Checkout
          </button>
        </div>
      </div>
    </div>
  );
};

// Checkout Page
const CheckoutPage = () => {
  const { cartItems, getTotalAmount, clearCart } = useCart();
  const navigate = useNavigate();
  
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: '',
    address_line1: '',
    address_line2: '',
    city: '',
    postal_code: '',
    country: 'Bangladesh'
  });
  
  const [processing, setProcessing] = useState(false);

  const handleInputChange = (e) => {
    setCustomerInfo({
      ...customerInfo,
      [e.target.name]: e.target.value
    });
  };

  const validateForm = () => {
    const required = ['name', 'email', 'phone', 'address_line1', 'city', 'postal_code'];
    return required.every(field => customerInfo[field].trim() !== '');
  };

  const handleCheckout = async () => {
    if (!validateForm()) {
      alert('Please fill in all required fields');
      return;
    }

    if (cartItems.length === 0) {
      alert('Your cart is empty');
      return;
    }

    setProcessing(true);

    try {
      const orderItems = cartItems.map(item => ({
        product_id: item.id,
        product_title: item.title,
        quantity: item.quantity,
        unit_price: item.price,
        total_price: item.price * item.quantity
      }));

      const subtotal = getTotalAmount();
      const shippingCost = 50.0;
      const totalAmount = subtotal + shippingCost;

      const order = {
        customer: customerInfo,
        items: orderItems,
        subtotal: subtotal,
        shipping_cost: shippingCost,
        total_amount: totalAmount,
        status: 'pending',
        payment_status: 'pending'
      };

      const response = await axios.post(`${API}/payments/initiate`, order);
      
      if (response.data.success) {
        clearCart();
        // Redirect to payment gateway
        window.location.replace(response.data.gateway_url);
      } else {
        throw new Error('Payment initiation failed');
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Checkout failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  if (cartItems.length === 0) {
    return (
      <div className="empty-cart">
        <div className="empty-cart-content">
          <h2>Your cart is empty</h2>
          <button className="cta-button" onClick={() => navigate("/")}>
            Continue Shopping
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <h1 className="page-title">Checkout</h1>
      <div className="checkout-content">
        <div className="checkout-form">
          <h3>Delivery Information</h3>
          <div className="form-row">
            <input
              type="text"
              name="name"
              placeholder="Full Name *"
              value={customerInfo.name}
              onChange={handleInputChange}
              required
            />
            <input
              type="email"
              name="email"
              placeholder="Email Address *"
              value={customerInfo.email}
              onChange={handleInputChange}
              required
            />
          </div>
          <div className="form-row">
            <input
              type="tel"
              name="phone"
              placeholder="Phone Number *"
              value={customerInfo.phone}
              onChange={handleInputChange}
              required
            />
            <input
              type="text"
              name="postal_code"
              placeholder="Postal Code *"
              value={customerInfo.postal_code}
              onChange={handleInputChange}
              required
            />
          </div>
          <input
            type="text"
            name="address_line1"
            placeholder="Address Line 1 *"
            value={customerInfo.address_line1}
            onChange={handleInputChange}
            required
          />
          <input
            type="text"
            name="address_line2"
            placeholder="Address Line 2 (Optional)"
            value={customerInfo.address_line2}
            onChange={handleInputChange}
          />
          <input
            type="text"
            name="city"
            placeholder="City *"
            value={customerInfo.city}
            onChange={handleInputChange}
            required
          />
        </div>

        <div className="order-summary">
          <h3>Order Summary</h3>
          <div className="order-items">
            {cartItems.map(item => (
              <div key={item.id} className="checkout-item">
                <img src={item.image_url} alt={item.title} />
                <div className="item-details">
                  <h4>{item.title}</h4>
                  <p>Qty: {item.quantity}</p>
                  <span className="item-price">৳{(item.price * item.quantity).toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
          
          <div className="summary-totals">
            <div className="summary-row">
              <span>Subtotal:</span>
              <span>৳{getTotalAmount().toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Shipping:</span>
              <span>৳50.00</span>
            </div>
            <div className="summary-row total">
              <span>Total:</span>
              <span>৳{(getTotalAmount() + 50).toFixed(2)}</span>
            </div>
          </div>

          <div className="checkout-actions">
            <button className="back-button" onClick={() => navigate('/cart')}>
              Back to Cart
            </button>
            <button 
              className="pay-button"
              onClick={handleCheckout}
              disabled={processing}
            >
              {processing ? 'Processing...' : `Pay ৳${(getTotalAmount() + 50).toFixed(2)}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Payment Status Pages
const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const transactionId = searchParams.get('transaction_id');

  return (
    <div className="payment-status success">
      <div className="status-card">
        <div className="success-icon">✅</div>
        <h2>Payment Successful!</h2>
        <p>Thank you for your purchase. Your order has been confirmed.</p>
        {transactionId && (
          <div className="transaction-details">
            <p><strong>Transaction ID:</strong> {transactionId}</p>
          </div>
        )}
        <div className="status-actions">
          <button className="primary-button" onClick={() => navigate('/')}>
            Continue Shopping
          </button>
        </div>
      </div>
    </div>
  );
};

const PaymentFailed = () => {
  const navigate = useNavigate();

  return (
    <div className="payment-status failed">
      <div className="status-card">
        <div className="error-icon">❌</div>
        <h2>Payment Failed</h2>
        <p>We're sorry, but your payment could not be processed.</p>
        <div className="status-actions">
          <button className="primary-button" onClick={() => navigate('/checkout')}>
            Try Again
          </button>
          <button className="secondary-button" onClick={() => navigate('/')}>
            Continue Shopping
          </button>
        </div>
      </div>
    </div>
  );
};

const PaymentCancelled = () => {
  const navigate = useNavigate();

  return (
    <div className="payment-status cancelled">
      <div className="status-card">
        <div className="warning-icon">⚠️</div>
        <h2>Payment Cancelled</h2>
        <p>You have cancelled the payment process.</p>
        <div className="status-actions">
          <button className="primary-button" onClick={() => navigate('/checkout')}>
            Complete Payment
          </button>
          <button className="secondary-button" onClick={() => navigate('/')}>
            Continue Shopping
          </button>
        </div>
      </div>
    </div>
  );
};

// Footer Component
const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-section">
          <div className="footer-logo">
            <Leaf className="logo-icon" />
            <span>TeaLeaf</span>
          </div>
          <p>Premium teas sourced from the finest gardens around the world.</p>
        </div>
        
        <div className="footer-section">
          <h4>Quick Links</h4>
          <ul>
            <li><a href="/">Shop</a></li>
            <li><a href="/about">About Us</a></li>
            <li><a href="/contact">Contact</a></li>
            <li><a href="/shipping">Shipping Info</a></li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4>Customer Service</h4>
          <ul>
            <li><a href="/faq">FAQ</a></li>
            <li><a href="/returns">Returns</a></li>
            <li><a href="/support">Support</a></li>
            <li><a href="/track">Track Order</a></li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4>Connect</h4>
          <div className="social-links">
            <a href="#" className="social-link">Facebook</a>
            <a href="#" className="social-link">Instagram</a>
            <a href="#" className="social-link">Twitter</a>
          </div>
        </div>
      </div>
      
      <div className="footer-bottom">
        <p>&copy; 2024 TeaLeaf. All rights reserved.</p>
      </div>
    </footer>
  );
};

function App() {
  return (
    <div className="App">
      <CartProvider>
        <BrowserRouter>
          <Header />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/cart" element={<CartPage />} />
              <Route path="/checkout" element={<CheckoutPage />} />
              <Route path="/payment/success" element={<PaymentSuccess />} />
              <Route path="/payment/failed" element={<PaymentFailed />} />
              <Route path="/payment/cancelled" element={<PaymentCancelled />} />
            </Routes>
          </main>
          <Footer />
        </BrowserRouter>
      </CartProvider>
    </div>
  );
}

export default App;