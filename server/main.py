from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import uuid
import os
from datetime import datetime
from typing import List
import asyncio
import json
from server.database import get_db_cursor
from server.schemas import (
    ChatRequest, ChatResponse, SessionResponse, MessageResponse,
    SessionCreate, APIResponse, DatabaseStats, HealthCheck,
    BookResponse, CustomerResponse, OrderResponse
)
from server.gemini_agent import GeminiAgent

# Initialize FastAPI app
app = FastAPI(
    title="Library AI Agent API",
    description="Full-stack AI agent for library management with RAG capabilities",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://[::1]:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the frontend
app.mount("/app", StaticFiles(directory="app", html=True), name="app")

# Global agent instance
_agent_instance = None

def get_gemini_agent() -> GeminiAgent:
    """Get or create the Gemini agent instance"""
    global _agent_instance
    if _agent_instance is None:
        try:
            _agent_instance = GeminiAgent()
            print("✅ Gemini Agent initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini Agent: {e}")
            raise
    return _agent_instance

def check_database_health():
    """Check if database is accessible and has data"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM books")
            book_count = cursor.fetchone()["count"]
            return book_count > 0
    except Exception:
        return False

def check_agent_health():
    """Check if the agent is properly initialized"""
    try:
        get_gemini_agent()
        return True
    except:
        return False

async def run_agent(session_id: str, user_message: str) -> dict:
    """
    Run the Gemini agent with the user message and save tool calls to database.
    
    Args:
        session_id: The chat session ID
        user_message: The user's message
        
    Returns:
        Dictionary with response message and tool calls
    """
    try:
        agent = get_gemini_agent()
        
        # Process the request through the agent
        result = agent.process_request(user_message)
        
        # Format response for the frontend
        tool_calls_for_response = []
        if result.get("tools_used"):
            for tool_decision in result["tools_used"]:
                tool_name = tool_decision.get("tool_name")
                tool_result = next(
                    (tr for tr in result.get("tool_results", []) 
                     if tr.get("tool_name") == tool_name),
                    {}
                )
                
                tool_calls_for_response.append({
                    "tool_name": tool_name,
                    "input_args": tool_decision.get("parameters", {}),
                    "output": tool_result.get("result", "No output"),
                    "success": tool_result.get("success", False)
                })
        
        return {
            "message": result["final_response"],
            "tool_calls": tool_calls_for_response,
            "analysis": result.get("analysis", {})
        }
        
    except Exception as e:
        error_msg = f"Agent execution error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "message": f"I encountered an error while processing your request: {str(e)}",
            "tool_calls": [],
            "analysis": {"error": error_msg}
        }

def test_agent_initialization():
    """Test function to verify agent can be initialized"""
    try:
        agent = get_gemini_agent()
        return True
    except Exception as e:
        print(f"Agent initialization test failed: {e}")
        return False

# API Routes
@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information"""
    agent_status = "initialized" if check_agent_health() else "failed"
    
    return APIResponse(
        success=True,
        message="Library AI Agent API is running",
        data={
            "name": "Library AI Agent API",
            "version": "1.0.0",
            "agent_status": agent_status,
            "endpoints": {
                "chat": "/chat",
                "sessions": "/sessions",
                "health": "/health",
                "docs": "/docs"
            }
        }
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    db_healthy = check_database_health()
    agent_healthy = check_agent_health()
    
    overall_status = "healthy" if (db_healthy and agent_healthy) else "degraded"
    
    return HealthCheck(
        status=overall_status,
        database=db_healthy,
        timestamp=datetime.now()
    )

@app.get("/stats", response_model=APIResponse)
async def get_stats():
    """Get database statistics"""
    try:
        with get_db_cursor() as cursor:
            stats = {}
            tables = ["books", "customers", "orders", "sessions", "messages", "tool_calls"]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()["count"]
            
            # Add agent status
            stats["agent_initialized"] = check_agent_health()
            
            return APIResponse(
                success=True,
                message="Database statistics retrieved",
                data=stats
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

# Session Management
@app.get("/sessions", response_model=APIResponse)
async def list_sessions():
    """Get all chat sessions with their latest message"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.*,
                    (SELECT content FROM messages 
                     WHERE session_id = s.id 
                     ORDER BY timestamp DESC 
                     LIMIT 1) as last_message,
                    (SELECT timestamp FROM messages 
                     WHERE session_id = s.id 
                     ORDER BY timestamp DESC 
                     LIMIT 1) as last_message_at
                FROM sessions s
                ORDER BY COALESCE(last_message_at, s.created_at) DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                session_data = dict(row)
                sessions.append(SessionResponse(**session_data))
            
            return APIResponse(
                success=True,
                message="Sessions retrieved successfully",
                data=sessions
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")

@app.post("/sessions", response_model=APIResponse)
async def create_session(session_data: SessionCreate):
    """Create a new chat session"""
    try:
        session_id = str(uuid.uuid4())
        
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO sessions (id, title) VALUES (?, ?)",
                (session_id, session_data.title or "New Conversation")
            )
            
            return APIResponse(
                success=True,
                message="Session created successfully",
                data={"session_id": session_id}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@app.get("/sessions/{session_id}/messages", response_model=APIResponse)
async def get_session_messages(session_id: str):
    """Get all messages for a specific session"""
    try:
        with get_db_cursor() as cursor:
            # Verify session exists
            cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Get messages
            cursor.execute("""
                SELECT * FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            """, (session_id,))
            
            messages = [MessageResponse(**dict(row)) for row in cursor.fetchall()]
            
            return APIResponse(
                success=True,
                message="Messages retrieved successfully",
                data=messages
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@app.get("/sessions/{session_id}/tool-calls", response_model=APIResponse)
async def get_session_tool_calls(session_id: str):
    """Get all tool calls for a specific session"""
    try:
        with get_db_cursor() as cursor:
            # Verify session exists
            cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Get tool calls
            cursor.execute("""
                SELECT * FROM tool_calls 
                WHERE session_id = ? 
                ORDER BY created_at ASC
            """, (session_id,))
            
            tool_calls = [dict(row) for row in cursor.fetchall()]
            
            return APIResponse(
                success=True,
                message="Tool calls retrieved successfully",
                data=tool_calls
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tool calls: {str(e)}")

# Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint - processes user messages through the AI agent"""
    try:
        # First, save user message and get agent response WITHOUT holding database connection
        user_message_id = None
        assistant_message_id = None
        
        # Step 1: Save user message and verify session
        with get_db_cursor() as cursor:
            # Verify session exists or create it
            cursor.execute("SELECT id FROM sessions WHERE id = ?", (request.session_id,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO sessions (id, title) VALUES (?, ?)",
                    (request.session_id, "New Conversation")
                )
            
            # Save user message
            cursor.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (request.session_id, "user", request.message)
            )
            user_message_id = cursor.lastrowid
        
        # Step 2: Process through Gemini agent (NO database connections during this)
        agent_response = await run_agent(request.session_id, request.message)
        
        # Step 3: Save assistant response and tool calls
        with get_db_cursor() as cursor:
            # Save assistant message
            cursor.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (request.session_id, "assistant", agent_response["message"])
            )
            assistant_message_id = cursor.lastrowid
            
            # Save tool calls
            for tool_call in agent_response.get("tool_calls", []):
                import json
                cursor.execute(
                    """INSERT INTO tool_calls 
                    (session_id, message_id, tool_name, input_args, output) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        request.session_id,
                        assistant_message_id,
                        tool_call.get("tool_name", "unknown"),
                        json.dumps(tool_call.get("input_args", {})),
                        str(tool_call.get("output", "Tool executed"))
                    )
                )
            
            # Update session title if it's the first message
            cursor.execute("""
                SELECT COUNT(*) as msg_count FROM messages 
                WHERE session_id = ? AND role = 'user'
            """, (request.session_id,))
            msg_count = cursor.fetchone()["msg_count"]
            
            if msg_count == 1:
                title = request.message[:30] + "..." if len(request.message) > 30 else request.message
                cursor.execute(
                    "UPDATE sessions SET title = ? WHERE id = ?",
                    (title, request.session_id)
                )
        
        return ChatResponse(
            message=agent_response["message"],
            session_id=request.session_id,
            tool_calls=agent_response.get("tool_calls", [])
        )
            
    except Exception as e:
        error_msg = f"Error processing chat: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    
    
# Data Exploration Endpoints (for debugging and frontend)
@app.get("/books", response_model=APIResponse)
async def get_books():
    """Get all books"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM books ORDER BY title")
            books = [BookResponse(**dict(row)) for row in cursor.fetchall()]
            
            return APIResponse(
                success=True,
                message="Books retrieved successfully",
                data=books
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving books: {str(e)}")

@app.get("/customers", response_model=APIResponse)
async def get_customers():
    """Get all customers"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM customers ORDER BY name")
            customers = [CustomerResponse(**dict(row)) for row in cursor.fetchall()]
            
            return APIResponse(
                success=True,
                message="Customers retrieved successfully",
                data=customers
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving customers: {str(e)}")

@app.get("/orders", response_model=APIResponse)
async def get_orders():
    """Get all orders with their items"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT o.*, c.name as customer_name
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                ORDER BY o.order_date DESC
            """)
            
            orders = []
            for row in cursor.fetchall():
                order_data = dict(row)
                
                # Get order items
                cursor.execute("""
                    SELECT oi.*, b.title as book_title
                    FROM order_items oi
                    JOIN books b ON oi.book_isbn = b.isbn
                    WHERE oi.order_id = ?
                """, (order_data["id"],))
                
                items = [dict(item) for item in cursor.fetchall()]
                order_data["items"] = items
                orders.append(OrderResponse(**order_data))
            
            return APIResponse(
                success=True,
                message="Orders retrieved successfully",
                data=orders
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

# Agent management endpoints
@app.post("/agent/initialize", response_model=APIResponse)
async def initialize_agent_endpoint():
    """Manually initialize the agent (for debugging)"""
    try:
        agent = get_gemini_agent()
        return APIResponse(
            success=True,
            message="Agent initialized successfully",
            data={"initialized": True}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing agent: {str(e)}")

@app.get("/agent/status", response_model=APIResponse)
async def get_agent_status():
    """Get the current agent status"""
    agent_healthy = check_agent_health()
    
    # Get tool usage history if agent is initialized
    tool_history = []
    if agent_healthy:
        try:
            agent = get_gemini_agent()
            tool_history = agent.get_tool_usage_history()
        except:
            pass
    
    return APIResponse(
        success=True,
        message="Agent status retrieved",
        data={
            "initialized": agent_healthy,
            "llm_provider": "gemini",
            "tools_available": list(get_gemini_agent().tools.keys()) if agent_healthy else [],
            "recent_tool_usage": len(tool_history)
        }
    )

@app.post("/agent/clear-history", response_model=APIResponse)
async def clear_agent_history():
    """Clear the agent's tool usage history"""
    try:
        agent = get_gemini_agent()
        agent.clear_tool_history()
        
        return APIResponse(
            success=True,
            message="Agent tool history cleared",
            data={"history_cleared": True}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing agent history: {str(e)}")

# Tools testing endpoints
@app.get("/tools/test", response_model=APIResponse)
async def test_tools():
    """Test that all tools are working properly"""
    try:
        from server.tools import test_tools
        success = test_tools()
        
        return APIResponse(
            success=success,
            message="Tools test completed",
            data={"all_tools_working": success}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing tools: {str(e)}")

@app.get("/debug/orders", response_model=APIResponse)
async def debug_orders():
    """Debug endpoint to see all orders and their items"""
    try:
        with get_db_cursor() as cursor:
            # Get all orders
            cursor.execute("""
                SELECT o.*, c.name as customer_name 
                FROM orders o 
                JOIN customers c ON o.customer_id = c.id 
                ORDER BY o.id
            """)
            orders = [dict(row) for row in cursor.fetchall()]
            
            # Get all order items
            cursor.execute("""
                SELECT oi.*, b.title as book_title 
                FROM order_items oi 
                JOIN books b ON oi.book_isbn = b.isbn 
                ORDER BY oi.order_id
            """)
            items = [dict(row) for row in cursor.fetchall()]
            
            return APIResponse(
                success=True,
                message="Debug orders info",
                data={
                    "orders": orders,
                    "order_items": items,
                    "orders_count": len(orders),
                    "items_count": len(items)
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error debugging orders: {str(e)}")
    
@app.get("/tools/list", response_model=APIResponse)
async def list_tools():
    """List all available tools"""
    try:
        agent = get_gemini_agent()
        tools_list = list(agent.tools.keys())
        
        return APIResponse(
            success=True,
            message="Tools list retrieved",
            data={"tools": tools_list}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tools: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Library AI Agent API starting up...")
    print("📚 Database initialized and ready")
    
    # Initialize the agent
    print("🤖 Initializing Gemini agent...")
    try:
        agent = get_gemini_agent()
        print("✅ Gemini agent initialized successfully")
        print(f"🛠️  Available tools: {', '.join(agent.tools.keys())}")
    except Exception as e:
        print(f"❌ Gemini agent initialization failed: {e}")
        print("💡 Make sure GOOGLE_API_KEY is set in your .env file")
    
    print("🌐 Frontend available at /app")
    print("📖 API documentation available at /docs")
    print("\n🎯 Sample requests to try:")
    print("  GET  /health")
    print("  GET  /stats") 
    print("  POST /sessions")
    print("  POST /chat with {'session_id': 'test', 'message': 'What books do you have?'}")

if __name__ == "__main__":
    import uvicorn
    
    # Set default port
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "server.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )
