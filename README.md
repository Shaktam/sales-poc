# POS System for Sale Event

A web-based Point of Sale system for managing a sale event with product categories, transaction processing, bill recording, and sales analytics.

## Features

- **Product Management**: Display 2 categories with multiple items, each with quantity and price
- **POS Interface**: Select items, adjust quantities, and calculate totals in real-time
- **Bill Recording**: Generate unique bill numbers and save complete transaction records
- **Sales Analytics**: View total revenue, per-item sales statistics, and per-category summaries

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Backend**: Python Flask
- **Database**: SQLite

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database**
   ```bash
   python database.py
   ```
   This will create the SQLite database (`pos_system.db`) with sample data including 2 categories (Health Basket and Aswins) with sample items.

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### POS Interface (`/`)

1. Select a category or view all items
2. Click on items to add them to the cart
3. Adjust quantities using the +/- buttons in the cart
4. Click "Complete Transaction" to finalize the sale
5. View the bill number and total in the success modal

### Analytics Dashboard (`/analytics`)

- View total sales revenue
- See sales breakdown by category
- Analyze per-item sales statistics
- Review recent bills

## Database Schema

The system uses SQLite with the following tables:

- **categories**: Product categories
- **items**: Products within categories
- **bills**: Transaction records
- **bill_items**: Items in each bill (junction table)

## API Endpoints

- `GET /api/categories` - Get all categories
- `GET /api/items` - Get all items (optionally filtered by category)
- `POST /api/bills` - Create new bill
- `GET /api/bills` - Get all bills
- `GET /api/analytics/revenue` - Get total revenue
- `GET /api/analytics/items` - Get per-item sales stats
- `GET /api/analytics/categories` - Get per-category sales stats

## Project Structure

```
SalesCounter/
├── app.py                 # Flask backend server
├── database.py            # Database initialization and schema
├── models.py              # Data models/helpers
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   └── js/
│       └── main.js        # Frontend JavaScript
├── templates/
│   ├── index.html         # Main POS interface
│   └── analytics.html     # Sales analytics dashboard
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Notes

- The database is automatically initialized with sample data when first run
- All bills are permanently stored in the SQLite database
- The system generates unique bill numbers in the format: `BILL-YYYYMMDD-XXXXXXXX`

