import sqlite3
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from langchain.tools import tool
from pydantic import BaseModel, Field

from server.database import get_db_cursor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for tool inputs
class FindBooksInput(BaseModel):
    title: Optional[str] = Field(None, description="Book title to search for")
    author: Optional[str] = Field(None, description="Author name to search for")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    in_stock: Optional[bool] = Field(True, description="Only show books in stock")

class CreateOrderInput(BaseModel):
    customer_id: int = Field(..., description="ID of the customer")
    items: List[Dict[str, Any]] = Field(..., description="List of items with ISBN and quantity")

class RestockBookInput(BaseModel):
    isbn: str = Field(..., description="ISBN of the book to restock")
    quantity: int = Field(..., ge=1, description="Quantity to add to stock")

class UpdatePriceInput(BaseModel):
    isbn: str = Field(..., description="ISBN of the book to update")
    new_price: float = Field(..., ge=0, description="New price for the book")

class OrderStatusInput(BaseModel):
    order_id: int = Field(..., description="ID of the order to check")

class SearchKnowledgeInput(BaseModel):
    query: str = Field(..., description="Search query for the knowledge base")

@tool(args_schema=FindBooksInput)
def find_books_tool(title: Optional[str] = None, author: Optional[str] = None, 
                   max_price: Optional[float] = None, in_stock: bool = True) -> str:
    """Search for books in the library inventory by title, author, price, or availability."""
    try:
        with get_db_cursor() as cursor:
            # Build the query dynamically based on provided filters
            query = "SELECT * FROM books WHERE 1=1"
            params = []
            
            if title:
                query += " AND title LIKE ?"
                params.append(f"%{title}%")
            
            if author:
                query += " AND author LIKE ?"
                params.append(f"%{author}%")
            
            if max_price is not None:
                query += " AND price <= ?"
                params.append(max_price)
            
            if in_stock:
                query += " AND stock > 0"
            
            query += " ORDER BY title"
            
            cursor.execute(query, params)
            books = [dict(row) for row in cursor.fetchall()]
            
            if not books:
                return "No books found matching your criteria."
            
            # Format the response
            result = f"Found {len(books)} book(s):\n\n"
            for book in books:
                stock_status = f" (In stock: {book['stock']})" if book['stock'] > 0 else " (OUT OF STOCK)"
                result += f"- **{book['title']}** by {book['author']}\n"
                result += f"  ISBN: {book['isbn']}, Price: ${book['price']:.2f}{stock_status}\n\n"
            
            logger.info(f"Found {len(books)} books with filters: title={title}, author={author}, max_price={max_price}")
            return result
            
    except Exception as e:
        error_msg = f"Error searching for books: {str(e)}"
        logger.error(error_msg)
        return error_msg
def create_order_safe(customer_id: int, items: List[Dict[str, Any]]) -> str:
    """Safe order creation with proper transaction handling"""
    try:
        with get_db_cursor() as cursor:
            # Verify customer exists
            cursor.execute("SELECT id, name FROM customers WHERE id = ?", (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                return f"Error: Customer with ID {customer_id} not found."
            
            customer_name = customer["name"]
            
            # Validate items and calculate total
            total_amount = 0
            order_items = []
            
            for item in items:
                isbn = item.get('isbn')
                quantity = item.get('quantity')
                
                if not isbn or not quantity:
                    return "Error: Each item must have 'isbn' and 'quantity'."
                
                if quantity <= 0:
                    return f"Error: Quantity for ISBN {isbn} must be positive."
                
                # Get book details and check stock (with lock)
                cursor.execute("SELECT title, price, stock FROM books WHERE isbn = ?", (isbn,))
                book = cursor.fetchone()
                
                if not book:
                    return f"Error: Book with ISBN {isbn} not found."
                
                if book["stock"] < quantity:
                    return f"Error: Not enough stock for '{book['title']}'. Available: {book['stock']}, Requested: {quantity}"
                
                item_total = book["price"] * quantity
                total_amount += item_total
                
                order_items.append({
                    'isbn': isbn,
                    'title': book['title'],
                    'quantity': quantity,
                    'unit_price': float(book['price']),
                    'item_total': float(item_total)
                })
            
            # Create the order
            cursor.execute(
                "INSERT INTO orders (customer_id, total_amount, status) VALUES (?, ?, ?)",
                (customer_id, total_amount, 'completed')
            )
            order_id = cursor.lastrowid
            
            # Add order items and update stock
            for item in order_items:
                cursor.execute(
                    "INSERT INTO order_items (order_id, book_isbn, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, item['isbn'], item['quantity'], item['unit_price'])
                )
                
                # Update book stock
                cursor.execute(
                    "UPDATE books SET stock = stock - ? WHERE isbn = ?",
                    (item['quantity'], item['isbn'])
                )
            
            # Verify order was created
            cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
            verified_order = cursor.fetchone()
            
            if not verified_order:
                return f"Error: Order #{order_id} was not created successfully."
            
            # Format success response
            result = f"✅ Order #{order_id} created successfully for {customer_name}!\n\n"
            result += f"**Order Details:**\n"
            result += f"Total Amount: ${total_amount:.2f}\n\n"
            result += f"**Items:**\n"
            for item in order_items:
                result += f"- {item['title']} (ISBN: {item['isbn']})\n"
                result += f"  Quantity: {item['quantity']}, Price: ${item['unit_price']:.2f} each\n"
            
            # Verify stock was updated
            for item in order_items:
                cursor.execute("SELECT title, stock FROM books WHERE isbn = ?", (item['isbn'],))
                updated_book = cursor.fetchone()
                result += f"\n✅ Stock updated: '{updated_book['title']}' now has {updated_book['stock']} copies in stock."
            
            logger.info(f"Created order #{order_id} for customer {customer_id} with {len(items)} items")
            return result
            
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            # Retry once after a short delay
            time.sleep(0.1)
            try:
                return create_order_safe(customer_id, items)
            except Exception as retry_error:
                return f"Error creating order after retry: {str(retry_error)}"
        else:
            return f"Database error: {str(e)}"
    except Exception as e:
        return f"Error creating order: {str(e)}"

@tool(args_schema=CreateOrderInput)
def create_order_tool(customer_id: int, items: List[Dict[str, Any]]) -> str:
    """Create a new order for a customer with the specified books and quantities."""
    return create_order_safe(customer_id, items)

@tool(args_schema=CreateOrderInput)
def create_order_tool(customer_id: int, items: List[Dict[str, Any]]) -> str:
    """Create a new order for a customer with the specified books and quantities."""
    return create_order_safe(customer_id=customer_id,items=items)

    try:
        with get_db_cursor() as cursor:
            # Verify customer exists
            cursor.execute("SELECT id, name FROM customers WHERE id = ?", (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                return f"Error: Customer with ID {customer_id} not found."
            
            customer_name = customer["name"]
            
            # Validate items and calculate total
            total_amount = 0
            order_items = []
            
            for item in items:
                isbn = item.get('isbn')
                quantity = item.get('quantity')
                
                if not isbn or not quantity:
                    return "Error: Each item must have 'isbn' and 'quantity'."
                
                if quantity <= 0:
                    return f"Error: Quantity for ISBN {isbn} must be positive."
                
                # Get book details and check stock
                cursor.execute("SELECT title, price, stock FROM books WHERE isbn = ?", (isbn,))
                book = cursor.fetchone()
                
                if not book:
                    return f"Error: Book with ISBN {isbn} not found."
                
                if book["stock"] < quantity:
                    return f"Error: Not enough stock for '{book['title']}'. Available: {book['stock']}, Requested: {quantity}"
                
                item_total = book["price"] * quantity
                total_amount += item_total
                
                order_items.append({
                    'isbn': isbn,
                    'title': book['title'],
                    'quantity': quantity,
                    'unit_price': float(book['price']),
                    'item_total': float(item_total)
                })
            
            # Create the order
            cursor.execute(
                "INSERT INTO orders (customer_id, total_amount, status) VALUES (?, ?, ?)",
                (customer_id, total_amount, 'completed')
            )
            order_id = cursor.lastrowid
            
            # Add order items and update stock
            for item in order_items:
                cursor.execute(
                    "INSERT INTO order_items (order_id, book_isbn, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, item['isbn'], item['quantity'], item['unit_price'])
                )
                
                # Update book stock
                cursor.execute(
                    "UPDATE books SET stock = stock - ? WHERE isbn = ?",
                    (item['quantity'], item['isbn'])
                )
            
            # VERIFY: Immediately check if order was created
            cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
            verified_order = cursor.fetchone()
            
            if not verified_order:
                return f"Error: Order #{order_id} was not created successfully. Database verification failed."
            
            # Format success response
            result = f"✅ Order #{order_id} created successfully for {customer_name}!\n\n"
            result += f"**Order Details:**\n"
            result += f"Total Amount: ${total_amount:.2f}\n\n"
            result += f"**Items:**\n"
            for item in order_items:
                result += f"- {item['title']} (ISBN: {item['isbn']})\n"
                result += f"  Quantity: {item['quantity']}, Price: ${item['unit_price']:.2f} each\n"
            
            # Verify stock was updated
            for item in order_items:
                cursor.execute("SELECT title, stock FROM books WHERE isbn = ?", (item['isbn'],))
                updated_book = cursor.fetchone()
                result += f"\n✅ Stock updated: '{updated_book['title']}' now has {updated_book['stock']} copies in stock."
            
            logger.info(f"Created order #{order_id} for customer {customer_id} with {len(items)} items")
            return result
            
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            error_msg = "The database is currently busy. Please try again in a moment."
        else:
            error_msg = f"Database error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error creating order: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool(args_schema=RestockBookInput)
def restock_book_tool(isbn: str, quantity: int) -> str:
    """Restock a book by adding more copies to the inventory."""
    try:
        with get_db_cursor() as cursor:
            # Verify book exists
            cursor.execute("SELECT title, stock FROM books WHERE isbn = ?", (isbn,))
            book = cursor.fetchone()
            
            if not book:
                return f"Error: Book with ISBN {isbn} not found."
            
            # Update stock
            cursor.execute(
                "UPDATE books SET stock = stock + ? WHERE isbn = ?",
                (quantity, isbn)
            )
            
            # Get updated stock
            cursor.execute("SELECT stock FROM books WHERE isbn = ?", (isbn,))
            new_stock = cursor.fetchone()["stock"]
            
            result = f"✅ Successfully restocked '{book['title']}'!\n\n"
            result += f"Added {quantity} copies to inventory.\n"
            result += f"Previous stock: {book['stock']}\n"
            result += f"New stock: {new_stock}"
            
            logger.info(f"Restocked book {isbn} with {quantity} copies. New stock: {new_stock}")
            return result
            
    except Exception as e:
        error_msg = f"Error restocking book: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool(args_schema=UpdatePriceInput)
def update_price_tool(isbn: str, new_price: float) -> str:
    """Update the price of a book."""
    try:
        with get_db_cursor() as cursor:
            # Verify book exists
            cursor.execute("SELECT title, price FROM books WHERE isbn = ?", (isbn,))
            book = cursor.fetchone()
            
            if not book:
                return f"Error: Book with ISBN {isbn} not found."
            
            old_price = book["price"]
            
            # Update price
            cursor.execute(
                "UPDATE books SET price = ? WHERE isbn = ?",
                (new_price, isbn)
            )
            
            result = f"✅ Price updated successfully for '{book['title']}'!\n\n"
            result += f"Old price: ${old_price:.2f}\n"
            result += f"New price: ${new_price:.2f}\n"
            result += f"Price change: ${new_price - old_price:+.2f}"
            
            logger.info(f"Updated price for book {isbn} from ${old_price:.2f} to ${new_price:.2f}")
            return result
            
    except Exception as e:
        error_msg = f"Error updating book price: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool(args_schema=OrderStatusInput)
def order_status_tool(order_id: int) -> str:
    """Check the status and details of a specific order."""
    try:
        with get_db_cursor() as cursor:
            # First, check if order exists
            cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
            order_exists = cursor.fetchone()
            
            if not order_exists:
                # Get the maximum order ID to help the user
                cursor.execute("SELECT MAX(id) as max_id FROM orders")
                max_order = cursor.fetchone()
                max_order_id = max_order["max_id"] if max_order else 0
                
                return f"Order #{order_id} not found. The highest order ID in the system is {max_order_id}. Please check the order number and try again."
            
            # Get order details
            cursor.execute("""
                SELECT o.*, c.name as customer_name, c.email as customer_email
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = ?
            """, (order_id,))
            
            order = cursor.fetchone()
            if not order:
                return f"Error: Order #{order_id} exists but couldn't retrieve details."
            
            # Get order items
            cursor.execute("""
                SELECT oi.*, b.title as book_title, b.author as book_author
                FROM order_items oi
                JOIN books b ON oi.book_isbn = b.isbn
                WHERE oi.order_id = ?
            """, (order_id,))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            if not items:
                return f"Error: Order #{order_id} exists but has no items."
            
            # Format the response
            result = f"📦 **Order #{order_id} Status**\n\n"
            result += f"**Customer:** {order['customer_name']} ({order['customer_email']})\n"
            result += f"**Order Date:** {order['order_date']}\n"
            result += f"**Status:** {order['status'].upper()}\n"
            result += f"**Total Amount:** ${order['total_amount']:.2f}\n\n"
            
            result += f"**Items ({len(items)}):**\n"
            for item in items:
                result += f"- {item['book_title']} by {item['book_author']}\n"
                result += f"  ISBN: {item['book_isbn']}, Qty: {item['quantity']}, "
                result += f"Price: ${item['unit_price']:.2f} each\n"
            
            logger.info(f"Retrieved status for order #{order_id}")
            return result
            
    except Exception as e:
        error_msg = f"Error checking order status: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def inventory_summary_tool() -> str:
    """Get a summary of the current inventory status."""
    try:
        with get_db_cursor() as cursor:
            # Get total books and value
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_books,
                    SUM(stock) as total_copies,
                    SUM(price * stock) as total_value,
                    AVG(price) as avg_price
                FROM books
            """)
            summary = cursor.fetchone()
            
            # Get low stock books (less than 5 copies)
            cursor.execute("""
                SELECT title, isbn, stock, price
                FROM books 
                WHERE stock < 5 
                ORDER BY stock ASC
            """)
            low_stock = [dict(row) for row in cursor.fetchall()]
            
            # Get out of stock books
            cursor.execute("""
                SELECT title, isbn, price
                FROM books 
                WHERE stock = 0 
                ORDER BY title
            """)
            out_of_stock = [dict(row) for row in cursor.fetchall()]
            
            # Format the response
            result = "📊 **Inventory Summary**\n\n"
            result += f"**Total Books:** {summary['total_books']} unique titles\n"
            result += f"**Total Copies:** {summary['total_copies'] or 0} in stock\n"
            result += f"**Total Inventory Value:** ${summary['total_value'] or 0:.2f}\n"
            result += f"**Average Book Price:** ${summary['avg_price'] or 0:.2f}\n\n"
            
            if low_stock:
                result += f"⚠️ **Low Stock Alert ({len(low_stock)} books):**\n"
                for book in low_stock:
                    result += f"- {book['title']} (ISBN: {book['isbn']}) - Only {book['stock']} left!\n"
                result += "\n"
            
            if out_of_stock:
                result += f"🚫 **Out of Stock ({len(out_of_stock)} books):**\n"
                for book in out_of_stock:
                    result += f"- {book['title']} (ISBN: {book['isbn']})\n"
                result += "\n"
            
            if not low_stock and not out_of_stock:
                result += "✅ All books have sufficient stock levels."
            
            logger.info("Generated inventory summary")
            return result
            
    except Exception as e:
        error_msg = f"Error generating inventory summary: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool(args_schema=SearchKnowledgeInput)
def search_knowledge_base_tool(query: str) -> str:
    """Search through uploaded PDF documents and programming books for detailed information."""
    try:
        # This will be integrated with the RAG system
        # For now, return a placeholder response
        
        # Check if RAG system is available
        try:
            from server.rag.retriever import get_retriever
            retriever = get_retriever()
            
            if retriever:
                docs = retriever.get_relevant_documents(query)
                if docs:
                    result = f"🔍 **Found {len(docs)} relevant document(s) for: '{query}'**\n\n"
                    for i, doc in enumerate(docs, 1):
                        source = doc.metadata.get('source', 'Unknown source')
                        page = doc.metadata.get('page', 'N/A')
                        result += f"**Result {i}** (Source: {source}, Page: {page}):\n"
                        result += f"{doc.page_content}\n\n"
                    return result
        except ImportError:
            # RAG system not yet implemented
            pass
        
        # Fallback response if RAG is not available
        result = f"🔍 **Knowledge Base Search for: '{query}'**\n\n"
        result += "The RAG system is currently being set up. When fully implemented, this tool will:\n"
        result += "- Search through all uploaded PDF documents\n"
        result += "- Retrieve relevant information about programming concepts, patterns, and best practices\n"
        result += "- Provide detailed explanations from authoritative sources\n\n"
        result += "For now, I can help you with library management tasks like finding books, creating orders, and checking inventory."
        
        logger.info(f"Searched knowledge base for: {query}")
        return result
        
    except Exception as e:
        error_msg = f"Error searching knowledge base: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def list_customers_tool() -> str:
    """Get a list of all customers in the system."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, name, email FROM customers ORDER BY name")
            customers = [dict(row) for row in cursor.fetchall()]
            
            if not customers:
                return "No customers found in the system."
            
            result = "👥 **Customers List**\n\n"
            for customer in customers:
                result += f"**{customer['name']}** (ID: {customer['id']})\n"
                result += f"Email: {customer['email']}\n\n"
            
            logger.info(f"Retrieved list of {len(customers)} customers")
            return result
            
    except Exception as e:
        error_msg = f"Error listing customers: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Export all tools
__all__ = [
    'find_books_tool',
    'create_order_tool', 
    'restock_book_tool',
    'update_price_tool',
    'order_status_tool',
    'inventory_summary_tool',
    'search_knowledge_base_tool',
    'list_customers_tool'
]

# Test function to verify all tools work
def test_tools():
    """Test that all tools can be called without errors"""
    try:
        # Test each tool with safe parameters
        print("Testing find_books_tool...")
        result1 = find_books_tool.run({})
        print("✅ find_books_tool works")
        
        print("Testing inventory_summary_tool...")
        result2 = inventory_summary_tool.run({})
        print("✅ inventory_summary_tool works")
        
        print("Testing search_knowledge_base_tool...")
        result3 = search_knowledge_base_tool.run({"query": "test"})
        print("✅ search_knowledge_base_tool works")
        
        print("Testing list_customers_tool...")
        result4 = list_customers_tool.run({})
        print("✅ list_customers_tool works")
        
        print("All tools tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        return False

if __name__ == "__main__":
    test_tools()
