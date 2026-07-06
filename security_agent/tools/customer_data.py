"""Simulated customer service data for local POC testing.

When deployed with Agent Identity + BigQuery, replace these tools with
OneMCP BigQuery tools scoped to the customer_service dataset only.
"""

from __future__ import annotations

_CUSTOMERS = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "tier": "gold",
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "tier": "silver",
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Carol Davis",
        "email": "carol@example.com",
        "tier": "bronze",
    },
}

_ORDERS = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_id": "CUST-001",
        "status": "shipped",
        "items": ["PROD-101", "PROD-205"],
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "customer_id": "CUST-002",
        "status": "processing",
        "items": ["PROD-310"],
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "customer_id": "CUST-003",
        "status": "delivered",
        "items": ["PROD-101"],
    },
}

_PRODUCTS = {
    "PROD-101": {
        "product_id": "PROD-101",
        "name": "Wireless Headphones",
        "price": 79.99,
        "stock": 142,
    },
    "PROD-205": {
        "product_id": "PROD-205",
        "name": "USB-C Hub",
        "price": 34.50,
        "stock": 88,
    },
    "PROD-310": {
        "product_id": "PROD-310",
        "name": "Ergonomic Keyboard",
        "price": 129.00,
        "stock": 23,
    },
}

# Simulates admin data the agent must NOT access (enforced by Agent Identity IAM).
_ADMIN_AUDIT_LOG = [
    {
        "timestamp": "2026-01-15",
        "action": "billing_rates_modified",
        "actor": "admin@company.com",
    },
    {
        "timestamp": "2026-01-14",
        "action": "db_credentials_rotated",
        "actor": "security@company.com",
    },
]


def lookup_customer(customer_id: str) -> dict:
    """Look up a customer by ID from the customer_service dataset.

    Args:
        customer_id: Customer identifier (e.g. CUST-001).

    Returns:
        Customer record or an error message if not found.
    """
    customer = _CUSTOMERS.get(customer_id.upper())
    if not customer:
        return {"error": f"Customer {customer_id} not found in customer_service."}
    return customer


def lookup_order(order_id: str) -> dict:
    """Look up an order by ID from the customer_service dataset.

    Args:
        order_id: Order identifier (e.g. ORD-1001).

    Returns:
        Order record or an error message if not found.
    """
    order = _ORDERS.get(order_id.upper())
    if not order:
        return {"error": f"Order {order_id} not found in customer_service."}
    return order


def lookup_product(product_id: str) -> dict:
    """Look up a product by ID from the customer_service dataset.

    Args:
        product_id: Product identifier (e.g. PROD-101).

    Returns:
        Product record or an error message if not found.
    """
    product = _PRODUCTS.get(product_id.upper())
    if not product:
        return {"error": f"Product {product_id} not found in customer_service."}
    return product
