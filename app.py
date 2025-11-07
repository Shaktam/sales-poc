from flask import Flask, render_template, jsonify, request
from database import init_db
from werkzeug.utils import secure_filename
import openpyxl
import os
from models import (
    get_all_categories,
    get_all_items,
    create_bill,
    get_all_bills,
    get_total_revenue,
    get_item_analytics,
    get_category_analytics,
    create_item,
    update_item,
    delete_item,
    clear_all_bills,
    get_bill_with_items,
    update_bill,
    delete_bill
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Main POS interface."""
    return render_template('index.html')

@app.route('/analytics')
def analytics():
    """Analytics dashboard."""
    return render_template('analytics.html')

@app.route('/admin')
def admin():
    """Admin interface for managing items."""
    return render_template('admin.html')

# API Endpoints

@app.route('/api/categories', methods=['GET'])
def api_categories():
    """Get all categories."""
    categories = get_all_categories()
    return jsonify(categories)

@app.route('/api/items', methods=['GET', 'POST'])
def api_items():
    """Get all items or create a new item."""
    if request.method == 'GET':
        category_id = request.args.get('category_id', type=int)
        items = get_all_items(category_id=category_id)
        return jsonify(items)
    elif request.method == 'POST':
        data = request.get_json()
        category_id = data.get('category_id')
        name = data.get('name')
        price = data.get('price')
        image_url = data.get('image_url')
        
        if not category_id or not name or price is None:
            return jsonify({'error': 'Missing required fields: category_id, name, price'}), 400
        
        try:
            item = create_item(category_id, name, price, image_url)
            return jsonify(item), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/items/<int:item_id>', methods=['PUT', 'DELETE'])
def api_item(item_id):
    """Update or delete an item."""
    if request.method == 'PUT':
        data = request.get_json()
        category_id = data.get('category_id')
        name = data.get('name')
        price = data.get('price')
        image_url = data.get('image_url')
        
        if not category_id or not name or price is None:
            return jsonify({'error': 'Missing required fields: category_id, name, price'}), 400
        
        try:
            item = update_item(item_id, category_id, name, price, image_url)
            return jsonify(item)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    elif request.method == 'DELETE':
        try:
            delete_item(item_id)
            return jsonify({'message': 'Item deleted successfully'}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/bills', methods=['GET', 'POST'])
def api_bills():
    """Get all bills or create a new bill."""
    if request.method == 'GET':
        bills = get_all_bills()
        return jsonify(bills)
    elif request.method == 'POST':
        data = request.get_json()
        bill_items = data.get('items', [])
        
        if not bill_items:
            return jsonify({'error': 'Bill must contain at least one item'}), 400
        
        # Validate bill items
        for item in bill_items:
            if 'item_id' not in item or 'quantity' not in item or 'unit_price' not in item:
                return jsonify({'error': 'Invalid bill item format'}), 400
            item['subtotal'] = item['quantity'] * item['unit_price']
        
        bill = create_bill(bill_items)
        return jsonify(bill), 201

@app.route('/api/analytics/revenue', methods=['GET'])
def api_revenue():
    """Get total sales revenue."""
    total_revenue = get_total_revenue()
    return jsonify({'total_revenue': total_revenue})

@app.route('/api/analytics/items', methods=['GET'])
def api_item_analytics():
    """Get per-item sales analytics."""
    analytics = get_item_analytics()
    return jsonify(analytics)

@app.route('/api/analytics/categories', methods=['GET'])
def api_category_analytics():
    """Get per-category sales analytics."""
    analytics = get_category_analytics()
    return jsonify(analytics)

@app.route('/api/bills/<int:bill_id>', methods=['GET', 'PUT', 'DELETE'])
def api_bill(bill_id):
    """Get, update, or delete a specific bill."""
    if request.method == 'GET':
        bill = get_bill_with_items(bill_id)
        if not bill:
            return jsonify({'error': 'Bill not found'}), 404
        return jsonify(bill)
    elif request.method == 'PUT':
        data = request.get_json()
        bill_items = data.get('items', [])
        
        if not bill_items:
            return jsonify({'error': 'Bill must contain at least one item'}), 400
        
        # Validate bill items
        for item in bill_items:
            if 'item_id' not in item or 'quantity' not in item or 'unit_price' not in item:
                return jsonify({'error': 'Invalid bill item format'}), 400
            item['subtotal'] = item['quantity'] * item['unit_price']
        
        try:
            bill = update_bill(bill_id, bill_items)
            return jsonify(bill)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    elif request.method == 'DELETE':
        try:
            delete_bill(bill_id)
            return jsonify({'message': 'Bill deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/bills/clear', methods=['POST'])
def api_clear_bills():
    """Clear all bills and analytics data."""
    try:
        clear_all_bills()
        return jsonify({'message': 'All sales and analytics data cleared successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/import-excel', methods=['POST'])
def api_import_excel():
    """Import items from Excel file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .xlsx and .xls files are allowed.'}), 400
    
    try:
        # Read Excel file
        wb = openpyxl.load_workbook(file, read_only=True)
        ws = wb.active
        
        # Expected columns: Category, Name, Price, Image URL (optional)
        items = []
        errors = []
        categories_map = {}
        
        # Get all categories and create a map
        categories = get_all_categories()
        for cat in categories:
            categories_map[cat['name'].lower()] = cat['id']
        
        # Read rows (skip header row)
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):  # Skip empty rows
                continue
            
            try:
                category_name = str(row[0]).strip() if row[0] else None
                item_name = str(row[1]).strip() if row[1] else None
                price = float(row[2]) if row[2] else None
                image_url = str(row[3]).strip() if len(row) > 3 and row[3] else None
                
                if not category_name or not item_name or price is None:
                    errors.append(f'Row {row_idx}: Missing required fields (Category, Name, Price)')
                    continue
                
                # Get or create category
                category_key = category_name.lower()
                if category_key not in categories_map:
                    # Category doesn't exist, skip or create? For now, skip
                    errors.append(f'Row {row_idx}: Category "{category_name}" not found')
                    continue
                
                category_id = categories_map[category_key]
                
                items.append({
                    'category_id': category_id,
                    'name': item_name,
                    'price': price,
                    'image_url': image_url if image_url and image_url != 'None' else None
                })
            except Exception as e:
                errors.append(f'Row {row_idx}: {str(e)}')
        
        # Create items
        created_items = []
        for item in items:
            try:
                created_item = create_item(
                    item['category_id'],
                    item['name'],
                    item['price'],
                    item['image_url']
                )
                created_items.append(created_item)
            except Exception as e:
                errors.append(f'Error creating item "{item["name"]}": {str(e)}')
        
        return jsonify({
            'message': f'Successfully imported {len(created_items)} items',
            'created': len(created_items),
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 400

if __name__ == '__main__':
   # app.run(debug=True, port=5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
