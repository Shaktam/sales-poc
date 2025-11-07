// Global state
let categories = [];
let items = [];
let cart = [];
let selectedCategoryId = null;

// API base URL
const API_BASE = '/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const currentPage = window.location.pathname;
    
    if (currentPage === '/') {
        initPOS();
    } else if (currentPage === '/analytics') {
        initAnalytics();
    }
});

// ==================== POS Page Functions ====================

async function initPOS() {
    await loadCategories();
    await loadItems();
    renderCategories();
    renderItems();
    setupEventListeners();
    updateCartDisplay();
}

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`);
        categories = await response.json();
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadItems(categoryId = null) {
    try {
        const url = categoryId 
            ? `${API_BASE}/items?category_id=${categoryId}`
            : `${API_BASE}/items`;
        const response = await fetch(url);
        items = await response.json();
    } catch (error) {
        console.error('Error loading items:', error);
    }
}

function renderCategories() {
    const container = document.getElementById('categories-container');
    container.innerHTML = '';
    
    categories.forEach(category => {
        const btn = document.createElement('button');
        btn.className = 'category-btn';
        btn.textContent = category.name;
        btn.dataset.categoryId = category.id;
        
        if (selectedCategoryId === category.id) {
            btn.classList.add('active');
        }
        
        btn.addEventListener('click', () => {
            selectedCategoryId = category.id;
            loadItems(category.id).then(() => {
                renderCategories();
                renderItems();
            });
        });
        
        container.appendChild(btn);
    });
    
    // Add "All" button
    const allBtn = document.createElement('button');
    allBtn.className = `category-btn ${selectedCategoryId === null ? 'active' : ''}`;
    allBtn.textContent = 'All';
    allBtn.addEventListener('click', () => {
        selectedCategoryId = null;
        loadItems().then(() => {
            renderCategories();
            renderItems();
        });
    });
    container.insertBefore(allBtn, container.firstChild);
}

function renderItems() {
    const container = document.getElementById('items-container');
    container.innerHTML = '';
    
    if (items.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">No items found</p>';
        return;
    }
    
    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
            <h3>${item.name}</h3>
            <div class="price">$${parseFloat(item.price).toFixed(2)}</div>
        `;
        
        card.addEventListener('click', () => {
            addToCart(item);
        });
        
        container.appendChild(card);
    });
}

function addToCart(item) {
    const existingItem = cart.find(cartItem => cartItem.item_id === item.id);
    
    if (existingItem) {
        existingItem.quantity += 1;
        existingItem.subtotal = existingItem.quantity * existingItem.unit_price;
    } else {
        cart.push({
            item_id: item.id,
            name: item.name,
            unit_price: parseFloat(item.price),
            quantity: 1,
            subtotal: parseFloat(item.price)
        });
    }
    
    updateCartDisplay();
}

function removeFromCart(itemId) {
    cart = cart.filter(item => item.item_id !== itemId);
    updateCartDisplay();
}

function updateQuantity(itemId, delta) {
    const item = cart.find(cartItem => cartItem.item_id === itemId);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            removeFromCart(itemId);
            return;
        }
        item.subtotal = item.quantity * item.unit_price;
        updateCartDisplay();
    }
}

function updateCartDisplay() {
    const container = document.getElementById('cart-items');
    const totalElement = document.getElementById('cart-total');
    const completeBtn = document.getElementById('complete-transaction');
    
    if (cart.length === 0) {
        container.innerHTML = '<p class="empty-cart">Cart is empty</p>';
        totalElement.textContent = '$0.00';
        completeBtn.disabled = true;
        return;
    }
    
    container.innerHTML = '';
    let total = 0;
    
    cart.forEach(item => {
        total += item.subtotal;
        
        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';
        cartItem.innerHTML = `
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-price">$${item.unit_price.toFixed(2)} each</div>
            </div>
            <div class="cart-item-controls">
                <button class="quantity-btn" onclick="updateQuantity(${item.item_id}, -1)">-</button>
                <span class="quantity-display">${item.quantity}</span>
                <button class="quantity-btn" onclick="updateQuantity(${item.item_id}, 1)">+</button>
            </div>
            <div class="cart-item-subtotal">$${item.subtotal.toFixed(2)}</div>
        `;
        
        container.appendChild(cartItem);
    });
    
    totalElement.textContent = `$${total.toFixed(2)}`;
    completeBtn.disabled = false;
}

function setupEventListeners() {
    document.getElementById('complete-transaction').addEventListener('click', completeTransaction);
    document.getElementById('clear-cart').addEventListener('click', clearCart);
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.querySelector('.close').addEventListener('click', closeModal);
    
    // Close modal on outside click
    document.getElementById('success-modal').addEventListener('click', (e) => {
        if (e.target.id === 'success-modal') {
            closeModal();
        }
    });
}

async function completeTransaction() {
    if (cart.length === 0) return;
    
    try {
        const billItems = cart.map(item => ({
            item_id: item.item_id,
            quantity: item.quantity,
            unit_price: item.unit_price
        }));
        
        const response = await fetch(`${API_BASE}/bills`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: billItems })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create bill');
        }
        
        const bill = await response.json();
        
        // Show success modal
        document.getElementById('bill-number').textContent = bill.bill_number;
        document.getElementById('bill-total').textContent = `$${bill.total_amount.toFixed(2)}`;
        document.getElementById('success-modal').classList.add('show');
        
        // Clear cart
        cart = [];
        updateCartDisplay();
        
    } catch (error) {
        console.error('Error completing transaction:', error);
        alert('Error completing transaction. Please try again.');
    }
}

function clearCart() {
    if (confirm('Are you sure you want to clear the cart?')) {
        cart = [];
        updateCartDisplay();
    }
}

function closeModal() {
    document.getElementById('success-modal').classList.remove('show');
}

// Make functions globally available for onclick handlers
window.updateQuantity = updateQuantity;

// ==================== Analytics Page Functions ====================

async function initAnalytics() {
    await loadRevenue();
    await loadCategoryAnalytics();
    await loadItemAnalytics();
    await loadRecentBills();
}

async function loadRevenue() {
    try {
        const response = await fetch(`${API_BASE}/analytics/revenue`);
        const data = await response.json();
        document.getElementById('total-revenue').textContent = `$${parseFloat(data.total_revenue).toFixed(2)}`;
    } catch (error) {
        console.error('Error loading revenue:', error);
    }
}

async function loadCategoryAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics/categories`);
        const analytics = await response.json();
        
        const tbody = document.querySelector('#category-table tbody');
        tbody.innerHTML = '';
        
        if (analytics.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #999;">No data available</td></tr>';
            return;
        }
        
        analytics.forEach(category => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${category.name}</td>
                <td>${category.total_items_sold}</td>
                <td>$${parseFloat(category.total_revenue).toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading category analytics:', error);
    }
}

async function loadItemAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics/items`);
        const analytics = await response.json();
        
        const tbody = document.querySelector('#item-table tbody');
        tbody.innerHTML = '';
        
        if (analytics.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #999;">No data available</td></tr>';
            return;
        }
        
        analytics.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.category_name}</td>
                <td>${item.name}</td>
                <td>$${parseFloat(item.price).toFixed(2)}</td>
                <td>${item.total_quantity_sold}</td>
                <td>$${parseFloat(item.total_revenue).toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading item analytics:', error);
    }
}

async function loadRecentBills() {
    try {
        const response = await fetch(`${API_BASE}/bills`);
        const bills = await response.json();
        
        const tbody = document.querySelector('#bills-table tbody');
        tbody.innerHTML = '';
        
        if (bills.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #999;">No bills yet</td></tr>';
            return;
        }
        
        // Show only recent 20 bills
        const recentBills = bills.slice(0, 20);
        
        recentBills.forEach(bill => {
            const row = document.createElement('tr');
            const date = new Date(bill.created_at);
            const formattedDate = date.toLocaleString();
            
            row.innerHTML = `
                <td>${bill.bill_number}</td>
                <td>$${parseFloat(bill.total_amount).toFixed(2)}</td>
                <td>${formattedDate}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading bills:', error);
    }
}

