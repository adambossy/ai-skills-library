# Designing Agent-Friendly Tools

Tools are how agents interact with the world. Well-designed tools make agents effective; poorly designed tools cause confusion and failures.

## The Core Principle

**Design tools as if explaining to a literal-minded new hire who will follow your instructions exactly.**

Agents don't have implicit human context. They interpret tool definitions literally.

## Tool Definition Anatomy

### Name

```python
# BAD: Ambiguous, abbreviated
def send(e, s, b): ...
def proc(d): ...
def get(id): ...

# GOOD: Verbose, self-documenting
def send_email_to_recipient(recipient_email_address, subject_line, body_content): ...
def process_customer_order(order_data): ...
def get_user_profile_by_id(user_id): ...
```

### Description

The description is the most important part. Agents read this to decide when to use the tool.

```python
# BAD: Vague, assumes context
"""Send a message."""

# GOOD: Specific, includes when to use
"""
Send an email message to a single recipient.

Use this tool when:
- The user wants to send an email
- You need to notify someone via email
- An automated email notification is required

Do NOT use this tool for:
- Bulk email sending (use send_bulk_email instead)
- Internal system notifications (use log_event instead)
"""
```

### Parameters

```python
# BAD: Cryptic parameter names
def search(q: str, n: int, f: str): ...

# GOOD: Explicit names with clear purpose
def search_documents(
    search_query: str,
    max_results: int,
    file_type_filter: str
): ...
```

### Type Hints and Constraints

```python
from typing import Literal

def create_task(
    task_title: str,                           # Required string
    priority: Literal["low", "medium", "high"], # Constrained values
    due_date: str | None = None,               # Optional with default
    assignee_email: str | None = None
) -> dict:
    """
    Args:
        task_title: Brief description of the task (max 100 chars)
        priority: Task priority level
            - "low": Nice to have, no deadline pressure
            - "medium": Should be done soon
            - "high": Urgent, needs immediate attention
        due_date: Optional deadline in ISO 8601 format (YYYY-MM-DD)
        assignee_email: Email of person responsible (omit to leave unassigned)

    Returns:
        dict containing:
            - task_id (str): Unique identifier for the created task
            - created_at (str): ISO 8601 timestamp
            - status (str): Always "pending" for new tasks
    """
```

## Common Tool Patterns

### CRUD Operations

```python
def create_customer_record(
    customer_name: str,
    customer_email: str,
    customer_phone: str | None = None
) -> dict:
    """Create a new customer in the database."""

def get_customer_by_id(customer_id: str) -> dict | None:
    """Retrieve a customer record. Returns None if not found."""

def update_customer_record(
    customer_id: str,
    updates: dict
) -> dict:
    """Update specific fields on a customer record."""

def delete_customer_record(customer_id: str) -> bool:
    """Permanently delete a customer. Returns True if deleted."""
```

### Search and Filter

```python
def search_products(
    query: str,
    category_filter: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    sort_by: Literal["relevance", "price_asc", "price_desc"] = "relevance",
    max_results: int = 10
) -> list[dict]:
    """
    Search product catalog.

    Args:
        query: Search terms (matches product name and description)
        category_filter: Limit to specific category (e.g., "electronics")
        price_min: Minimum price filter (inclusive)
        price_max: Maximum price filter (inclusive)
        sort_by: Result ordering
        max_results: Maximum products to return (1-100)

    Returns:
        List of product dicts, each containing:
            - product_id, name, description, price, category, image_url
    """
```

### Confirmation-Required Actions

For destructive or irreversible operations:

```python
def delete_all_user_data(
    user_id: str,
    confirmation_phrase: str
) -> dict:
    """
    Permanently delete all data for a user. THIS CANNOT BE UNDONE.

    Before calling this tool:
    1. Confirm with the user they want to delete ALL their data
    2. Explain this action is irreversible
    3. Ask them to confirm by saying "permanently delete my data"

    Args:
        user_id: The user whose data will be deleted
        confirmation_phrase: Must be exactly "CONFIRM_DELETE" to proceed

    Returns:
        - success: bool
        - deleted_items_count: int
        - error: str | None
    """
```

## Error Response Design

Tools should return informative errors:

```python
def transfer_funds(from_account: str, to_account: str, amount: float) -> dict:
    """
    Returns on success:
        {"success": True, "transaction_id": "...", "new_balance": ...}

    Returns on failure:
        {"success": False, "error_code": "...", "error_message": "...", "suggestion": "..."}

    Possible error_codes:
        - "INSUFFICIENT_FUNDS": Not enough money in source account
        - "INVALID_ACCOUNT": One of the account IDs doesn't exist
        - "LIMIT_EXCEEDED": Transfer exceeds daily limit
        - "ACCOUNT_FROZEN": Source account is frozen
    """
```

## Tool Composition

Design tools that work well together:

```python
# These tools are designed to chain naturally:

def get_customer_orders(customer_id: str) -> list[dict]:
    """Get all orders for a customer. Returns list with order_id, status, total."""

def get_order_details(order_id: str) -> dict:
    """Get full details for a specific order including line items."""

def update_order_status(order_id: str, new_status: str) -> dict:
    """Update the status of an order."""

# Agent can naturally chain: get_customer_orders -> get_order_details -> update_order_status
```

## Anti-Patterns to Avoid

### God Tools

```python
# BAD: One tool that does everything
def manage_user(action: str, user_id: str, data: dict): ...

# GOOD: Separate tools for separate actions
def create_user(name: str, email: str): ...
def update_user(user_id: str, updates: dict): ...
def delete_user(user_id: str): ...
```

### Hidden Side Effects

```python
# BAD: Undocumented side effect
def get_user(user_id: str) -> dict:
    """Get user details."""
    log_user_access(user_id)  # Hidden side effect!
    return db.get(user_id)

# GOOD: Document all effects
def get_user(user_id: str) -> dict:
    """
    Get user details.

    Side effects:
        - Logs access event to audit trail
        - Updates user's last_accessed timestamp
    """
```

### Ambiguous Return Types

```python
# BAD: What does this return?
def process(data) -> dict: ...

# GOOD: Explicit return structure
def process_payment(payment_data: dict) -> dict:
    """
    Returns:
        {
            "success": bool,
            "transaction_id": str | None,  # Present if success=True
            "error": str | None,           # Present if success=False
            "receipt_url": str | None      # URL to payment receipt
        }
    """
```
