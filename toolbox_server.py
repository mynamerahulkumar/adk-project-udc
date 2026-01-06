#!/usr/bin/env python3
"""
MCP Toolbox Server for database tool access.
This server exposes the get-product-price tool via HTTP.
"""

import os
import json
import mysql.connector
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration from environment
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USERNAME'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'database': 'betty'
}

def get_db_connection():
    """Create a new database connection."""
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/tools', methods=['GET'])
def list_tools():
    """List available tools."""
    return jsonify({
        "tools": [
            {
                "name": "get-product-price",
                "description": "Query the bird store database to get the price of a product by name",
                "parameters": {
                    "product_name": {
                        "type": "string",
                        "description": "The name of the product to look up (e.g., 'Bird Seed Mix')"
                    }
                }
            }
        ]
    })

@app.route('/tools/get-product-price/call', methods=['POST'])
def call_get_product_price():
    """Call the get-product-price tool."""
    try:
        data = request.json
        product_name = data.get('product_name', '').strip()
        
        if not product_name:
            return jsonify({"error": "product_name is required"}), 400
        
        # Query the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT product_name, price 
            FROM products 
            WHERE LOWER(product_name) LIKE LOWER(CONCAT('%', %s, '%'))
            LIMIT 1
        """
        
        cursor.execute(query, (product_name,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                "product_name": result['product_name'],
                "price": float(result['price'])
            })
        else:
            return jsonify({"error": f"Product '{product_name}' not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.getenv('TOOLBOX_PORT', 8080))
    print(f"Starting Toolbox Server...")
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"Listening on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
