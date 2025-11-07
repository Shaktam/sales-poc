from database import get_db_connection
from datetime import datetime
import uuid

def generate_bill_number():
    """Generate a unique bill number."""
    timestamp = datetime.now().strftime('%Y%m%d')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f'BILL-{timestamp}-{unique_id}'

def get_all_categories():
    """Get all categories from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories ORDER BY name')
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories

def get_all_items(category_id=None):
    """Get all items, optionally filtered by category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if category_id:
        cursor.execute('''
            SELECT i.*, c.name as category_name
            FROM items i
            JOIN categories c ON i.category_id = c.id
            WHERE i.category_id = ?
            ORDER BY i.name
        ''', (category_id,))
    else:
        cursor.execute('''
            SELECT i.*, c.name as category_name
            FROM items i
            JOIN categories c ON i.category_id = c.id
            ORDER BY c.name, i.name
        ''')
    
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

def create_bill(bill_items):
    """Create a new bill with items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate total
    total_amount = sum(item['subtotal'] for item in bill_items)
    
    # Generate bill number
    bill_number = generate_bill_number()
    
    # Insert bill
    cursor.execute('''
        INSERT INTO bills (bill_number, total_amount)
        VALUES (?, ?)
    ''', (bill_number, total_amount))
    
    bill_id = cursor.lastrowid
    
    # Insert bill items
    for item in bill_items:
        cursor.execute('''
            INSERT INTO bill_items (bill_id, item_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        ''', (bill_id, item['item_id'], item['quantity'], item['unit_price'], item['subtotal']))
    
    conn.commit()
    conn.close()
    
    return {
        'bill_id': bill_id,
        'bill_number': bill_number,
        'total_amount': total_amount
    }

def get_all_bills():
    """Get all bills from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM bills
        ORDER BY created_at DESC
    ''')
    bills = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return bills

def get_total_revenue():
    """Calculate total sales revenue."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COALESCE(SUM(total_amount), 0) as total FROM bills')
    result = cursor.fetchone()
    conn.close()
    return result['total']

def get_item_analytics():
    """Get per-item sales analytics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            i.id,
            i.name,
            i.price,
            c.name as category_name,
            COALESCE(SUM(bi.quantity), 0) as total_quantity_sold,
            COALESCE(SUM(bi.subtotal), 0) as total_revenue
        FROM items i
        JOIN categories c ON i.category_id = c.id
        LEFT JOIN bill_items bi ON i.id = bi.item_id
        GROUP BY i.id, i.name, i.price, c.name
        ORDER BY total_revenue DESC, c.name, i.name
    ''')
    analytics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return analytics

def get_category_analytics():
    """Get per-category sales analytics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            c.id,
            c.name,
            COALESCE(SUM(bi.quantity), 0) as total_items_sold,
            COALESCE(SUM(bi.subtotal), 0) as total_revenue
        FROM categories c
        LEFT JOIN items i ON c.id = i.category_id
        LEFT JOIN bill_items bi ON i.id = bi.item_id
        GROUP BY c.id, c.name
        ORDER BY total_revenue DESC, c.name
    ''')
    analytics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return analytics

def create_item(category_id, name, price, image_url=None):
    """Create a new item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO items (category_id, name, price, image_url)
        VALUES (?, ?, ?, ?)
    ''', (category_id, name, price, image_url))
    item_id = cursor.lastrowid
    conn.commit()
    
    # Fetch the created item with category name
    cursor.execute('''
        SELECT i.*, c.name as category_name
        FROM items i
        JOIN categories c ON i.category_id = c.id
        WHERE i.id = ?
    ''', (item_id,))
    item = dict(cursor.fetchone())
    conn.close()
    return item

def update_item(item_id, category_id, name, price, image_url=None):
    """Update an existing item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE items
        SET category_id = ?, name = ?, price = ?, image_url = ?
        WHERE id = ?
    ''', (category_id, name, price, image_url, item_id))
    conn.commit()
    
    # Fetch the updated item with category name
    cursor.execute('''
        SELECT i.*, c.name as category_name
        FROM items i
        JOIN categories c ON i.category_id = c.id
        WHERE i.id = ?
    ''', (item_id,))
    item = dict(cursor.fetchone())
    conn.close()
    return item

def delete_item(item_id):
    """Delete an item if it hasn't been used in any bills."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if item has been used in bills
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM bill_items
        WHERE item_id = ?
    ''', (item_id,))
    result = cursor.fetchone()
    
    if result['count'] > 0:
        conn.close()
        raise ValueError(f'Cannot delete item: it has been used in {result["count"]} bill(s)')
    
    # Delete the item
    cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return True

def clear_all_bills():
    """Clear all bills and bill_items from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete all bill_items first (due to foreign key constraint)
    cursor.execute('DELETE FROM bill_items')
    
    # Delete all bills
    cursor.execute('DELETE FROM bills')
    
    conn.commit()
    conn.close()
    return True

def get_bill_with_items(bill_id):
    """Get a bill with its items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get bill
    cursor.execute('SELECT * FROM bills WHERE id = ?', (bill_id,))
    bill = cursor.fetchone()
    
    if not bill:
        conn.close()
        return None
    
    bill_dict = dict(bill)
    
    # Get bill items
    cursor.execute('''
        SELECT 
            bi.*,
            i.name as item_name,
            i.price as current_price
        FROM bill_items bi
        JOIN items i ON bi.item_id = i.id
        WHERE bi.bill_id = ?
    ''', (bill_id,))
    
    bill_items = [dict(row) for row in cursor.fetchall()]
    bill_dict['items'] = bill_items
    
    conn.close()
    return bill_dict

def update_bill(bill_id, bill_items):
    """Update a bill with new items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate new total
    total_amount = sum(item['subtotal'] for item in bill_items)
    
    # Update bill
    cursor.execute('''
        UPDATE bills
        SET total_amount = ?
        WHERE id = ?
    ''', (total_amount, bill_id))
    
    # Delete old bill items
    cursor.execute('DELETE FROM bill_items WHERE bill_id = ?', (bill_id,))
    
    # Insert new bill items
    for item in bill_items:
        cursor.execute('''
            INSERT INTO bill_items (bill_id, item_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        ''', (bill_id, item['item_id'], item['quantity'], item['unit_price'], item['subtotal']))
    
    conn.commit()
    conn.close()
    
    return get_bill_with_items(bill_id)

def delete_bill(bill_id):
    """Delete a bill and its items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete bill items first
    cursor.execute('DELETE FROM bill_items WHERE bill_id = ?', (bill_id,))
    
    # Delete bill
    cursor.execute('DELETE FROM bills WHERE id = ?', (bill_id,))
    
    conn.commit()
    conn.close()
    return True

