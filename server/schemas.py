from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Chat Request/Response Schemas
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User message content")

class ChatResponse(BaseModel):
    message: str = Field(..., description="Assistant response content")
    session_id: str = Field(..., description="Session identifier")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=[], description="Tool calls made during processing")

class SessionCreate(BaseModel):
    title: Optional[str] = Field("New Conversation", description="Session title")

class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ToolCallResponse(BaseModel):
    id: int
    session_id: str
    message_id: int
    tool_name: str
    input_args: str
    output: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Book Schemas
class BookBase(BaseModel):
    isbn: str = Field(..., description="International Standard Book Number")
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    price: float = Field(..., ge=0, description="Book price in USD")
    stock: int = Field(..., ge=0, description="Quantity in inventory")

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    created_at: datetime

    class Config:
        from_attributes = True

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)

# Customer Schemas
class CustomerBase(BaseModel):
    name: str = Field(..., description="Customer full name")
    email: str = Field(..., description="Customer email address")

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Order Item Schemas
class OrderItemBase(BaseModel):
    book_isbn: str = Field(..., description="ISBN of the book")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    unit_price: float = Field(..., ge=0, description="Price per unit at time of order")

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    class Config:
        from_attributes = True

# Order Schemas
class OrderBase(BaseModel):
    customer_id: int = Field(..., description="ID of the customer placing the order")
    status: str = Field("pending", description="Order status: pending, completed, cancelled")

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., description="List of order items")

class OrderResponse(OrderBase):
    id: int
    total_amount: float
    order_date: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

# Tool Input Schemas (for agent tools)
class FindBooksRequest(BaseModel):
    title: Optional[str] = Field(None, description="Book title to search for")
    author: Optional[str] = Field(None, description="Author name to search for")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    in_stock: Optional[bool] = Field(True, description="Only show books in stock")

class CreateOrderRequest(BaseModel):
    customer_id: int = Field(..., description="ID of the customer")
    items: List[Dict[str, Any]] = Field(..., description="List of items with ISBN and quantity")

class RestockBookRequest(BaseModel):
    isbn: str = Field(..., description="ISBN of the book to restock")
    quantity: int = Field(..., ge=1, description="Quantity to add to stock")

class UpdatePriceRequest(BaseModel):
    isbn: str = Field(..., description="ISBN of the book to update")
    new_price: float = Field(..., ge=0, description="New price for the book")

class OrderStatusRequest(BaseModel):
    order_id: int = Field(..., description="ID of the order to check")

class SearchKnowledgeRequest(BaseModel):
    query: str = Field(..., description="Search query for the knowledge base")

# Tool Response Schemas
class ToolResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class FindBooksResponse(ToolResponse):
    data: Optional[Dict[str, Any]] = Field(None, description="Found books and metadata")

class CreateOrderResponse(ToolResponse):
    data: Optional[Dict[str, Any]] = Field(None, description="Order details and updated stock")

class RestockBookResponse(ToolResponse):
    data: Optional[Dict[str, Any]] = Field(None, description="Updated book stock information")

class UpdatePriceResponse(ToolResponse):
    data: Optional[Dict[str, Any]] = Field(None, description="Updated book price information")

class OrderStatusResponse(ToolResponse):
    data: Optional[Dict[str, Any]] = Field(None, description="Order status and details")

class InventorySummaryResponse(ToolResponse):
    data: Optional[Dict[str, Any]] = Field(None, description="Inventory summary statistics")

class SearchKnowledgeResponse(ToolResponse):
    data: Optional[Dict[str, Any]] = Field(None, description="Search results from knowledge base")

# API Response Wrappers
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

# Database row count schemas (for health checks)
class DatabaseStats(BaseModel):
    books_count: int
    customers_count: int
    orders_count: int
    sessions_count: int
    messages_count: int
    tool_calls_count: int

# Error Schemas
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

# Health Check Schema
class HealthCheck(BaseModel):
    status: str
    database: bool
    timestamp: datetime
    version: str = "1.0.0"
