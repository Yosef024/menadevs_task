# Library AI Agent - Complete Documentation
## 📚 Project Overview
The Library AI Agent is a full-stack AI-powered library management system that uses Google's Gemini AI to handle book inventory, customer orders, and database operations through natural language conversations.
## 🏗️ Architecture
```
Library-AI-Agent/
├── app/ # Frontend UI
│ └── index.html # Chat interface
├── db/
│ └── seed.sql # Database initialization
├── server/ # Backend API
│ ├── main.py # FastAPI application
│ ├── database.py # Database connection management
│ ├── gemini_agent.py # AI agent orchestration
│ ├── schemes.py # Data models & validation
│ └── tools.py # Database operation tools
├── requirements.txt # Python dependencies
└── .env # Environment configuration
```
## 🔧 Installation & Setup
### Clone the Repository
First, clone the repository from GitHub:

```bash
git clone https://github.com/your-username/Library-AI-Agent.git
cd Library-AI-Agent
```
### Prerequisites
- Python 3.8+
- Google API Key for Gemini AI
- Modern web browser
### 1. Install Dependencies
```bash
# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
# Install all dependencies
pip install -r requirements.txt
```
**requirements.txt contents:**
```txt
fastapi==0.104.1
uvicorn==0.24.0
sqlite3
python-multipart==0.0.6
pydantic==2.5.0
google-generativeai==0.3.0
langchain==0.0.350
python-dotenv==1.0.0
```
### 2. Environment Configuration
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_google_api_key_here
PORT=8000
```
### 3. Run the Application
Open **two separate terminals**:
**Terminal 1 - Backend Server:**
```bash
# Navigate to project directory
cd library-ai-agent
# Start the FastAPI server
python -m server.main
```
**Terminal 2 - Frontend Access:**
```bash
# Open the application in your browser
# On macOS:
open http://localhost:8000/app
# On Windows:
start http://localhost:8000/app
# On Linux:
xdg-open http://localhost:8000/app
```
## 📁 Code Documentation
### 1. Frontend UI (`app/index.html`)
**Purpose**: User-friendly chat interface for interacting with the AI agent.
**Key Features:**
- Real-time chat interface with message history
- Session management (create new conversations)
- Tool execution visualization
- Responsive design for desktop and mobile
**Components:**
- Chat message bubbles (user & assistant)
- Session sidebar with conversation history
- Tool call details with input/output display
- Auto-scrolling to new messages
### 2. Database Schema (`db/seed.sql`)
**Purpose**: Database initialization with sample data.
**Tables Created:**
- `books`: Book inventory with ISBN, title, author, price, stock
- `customers`: Customer information
- `orders`: Order records with status and totals
- `order_items`: Individual items within orders
- `sessions`: Chat session tracking
- `messages`: Chat message history
- `tool_calls`: AI tool execution logs
**Sample Data:**
- 10 programming books with realistic inventory
- 6 sample customers
- 4 initial orders with order items
### 3. Database Management (`server/database.py`)
**Purpose**: SQLite database connection and transaction management.
**Key Functions:**
- `init_database()`: Creates tables and seeds initial data
- `get_db_cursor()`: Context manager for safe database operations
- Connection pooling with retry logic for locked databases
**Features:**
- WAL (Write-Ahead Logging) mode for better concurrency
- Automatic transaction commit/rollback
- Row factory for dictionary-like access
- Foreign key enforcement
### 4. AI Agent Orchestration (`server/gemini_agent.py`)
**Purpose**: Processes natural language requests and coordinates tool execution.
**Core Workflow:**
1. **Analyze Request**: Determines if tools are needed
2. **Determine Parameters**: Extracts required parameters from user input
3. **Execute Tools**: Runs database operations through tools
4. **Generate Response**: Creates natural language response
**Key Methods:**
- `process_request()`: Main entry point for request processing
- `analyze_request()`: Uses Gemini to determine required actions
- `execute_tools()`: Coordinates tool execution
- `generate_final_response()`: Creates user-friendly responses
### 5. FastAPI Application (`server/main.py`)
**Purpose**: REST API server with chat endpoints and database operations.
**Key Endpoints:**
- `POST /chat`: Main chat processing endpoint
- `GET/POST /sessions`: Session management
- `GET /books,/customers,/orders`: Data exploration
- `GET /health,/stats`: System monitoring
- `GET /debug/*`: Debugging and troubleshooting
**Features:**
- CORS configuration for frontend communication
- Static file serving for UI
- Comprehensive error handling
- Real-time tool execution logging
### 6. Data Models (`server/schemes.py`)
**Purpose**: Pydantic models for request/response validation and type safety.
**Model Categories:**
- **Chat Models**: `ChatRequest`, `ChatResponse`, `MessageResponse`
- **Business Models**: `BookResponse`, `CustomerResponse`, `OrderResponse`
- **Tool Models**: Input/response schemas for each tool
- **API Models**: `APIResponse`, `HealthCheck`, `DatabaseStats`
**Benefits:**
- Automatic request validation
- Type hints throughout the codebase
- Consistent API response format
- Serialization/deserialization
### 7. Tool Functions (`server/tools.py`)
**Purpose**: Database operation tools that the AI agent can execute.
**Available Tools:**
- `find_books_tool`: Search books by title, author, price, availability
- `create_order_tool`: Create new orders with stock adjustment
- `restock_book_tool`: Add inventory to books
- `update_price_tool`: Modify book prices
- `order_status_tool`: Check order details and status
- `inventory_summary_tool`: Get inventory overview
- `search_knowledge_base_tool`: Search documentation (RAG-ready)
- `list_customers_tool`: Display all customers
**Features:**
- Input validation with Pydantic models
- Comprehensive error handling
- Transaction safety for multi-step operations
- Detailed logging for debugging
### 8. Environment Configuration (`.env`)
**Purpose**: Secure configuration management.
**Required Variables:**
- `GOOGLE_API_KEY`: API key for Gemini AI access
- `PORT`: Server port (default: 8000)
## 🧪 Valid Test Cases & Expected Responses
### Test Case 1: Inventory Management & Search
**User Input**: "Restock The Pragmatic Programmer by 10 and list all books by Andrew Hunt."
**Expected Response**:
```
I was able to add 10 copies of "The Pragmatic Programmer" to our inventory. It now has 32 copies available. I also found one book by Andrew Hunt in our catalog: "The Pragmatic Programmer: Your Journey to Mastery" by David Thomas and Andrew Hunt.
```
### Test Case 2: Order Creation
**User Input**: "We sold 3 copies of Clean Code to customer 2 today. Create the order and adjust stock."
**Expected Response**:
```
Certainly! I've created order #5 for Bob Smith, which includes 3 copies of "Clean Code: A Handbook of Agile Software Craftsmanship" at $47.49 each, for a total of $142.47. The stock has also been updated, and there are now 29 copies of "Clean Code" available.
```
### Test Case 3: Order Status Check
**User Input**: "What's the status of order 5?"
**Expected Response**:
```
Your order #5, placed by Bob Smith on November 26, 2025, has been completed! The total amount for the order was $142.47. It includes 3 copies of "Clean Code: A Handbook of Agile Software Craftsmanship."
```
### Test Case 4: Book Search
**User Input**: "What books do you have about software architecture?"
**Expected Response**:
```
I found several books about software architecture in our inventory:
- "Clean Architecture: A Craftsman's Guide to Software Structure and Design" by Robert C. Martin - $49.99 (22 in stock)
- "Domain-Driven Design: Tackling Complexity in the Heart of Software" by Eric Evans - $56.75 (12 in stock)
- "Design Patterns: Elements of Reusable Object-Oriented Software" by Erich Gamma et al. - $54.99 (18 in stock)
```
### Test Case 5: Inventory Summary
**User Input**: "Show me the current inventory status"
**Expected Response**:
```
📊 Inventory Summary
Total Books: 10 unique titles
Total Copies: 194 in stock
Total Inventory Value: $9,234.75
Average Book Price: $47.62
⚠️ Low Stock Alert (2 books):
- "Site Reliability Engineering" - Only 8 left!
- "Domain-Driven Design" - Only 12 left!
```
### Test Case 6: Price Update
**User Input**: "Update the price of Clean Code to $49.99"
**Expected Response**:
```
✅ Price updated successfully for 'Clean Code: A Handbook of Agile Software Craftsmanship'!
Old price: $47.49
New price: $49.99
Price change: +$2.50
```
### Test Case 7: Customer Management
**User Input**: "List all customers"
**Expected Response**:
```
👥 Customers List
Alice Johnson (ID: 1)
Email: alice.johnson@email.com
Bob Smith (ID: 2)
Email: bob.smith@email.com
Carol Davis (ID: 3)
Email: carol.davis@email.com
David Wilson (ID: 4)
Email: david.wilson@email.com
Eva Brown (ID: 5)
Email: eva.brown@email.com
Frank Miller (ID: 6)
Email: frank.miller@email.com
```
## 🚀 Additional Features & Capabilities
### Real-time Features
- Live chat with immediate responses
- Session persistence across browser refreshes
- Real-time inventory updates
- Order status tracking
### Error Handling
- Graceful database connection failures
- Invalid input validation
- Stock availability checks
- Customer/order existence verification
### Security Features
- SQL injection prevention through parameterized queries
- Input validation with Pydantic models
- CORS configuration for frontend security
- Environment variable protection for API keys
### Monitoring & Debugging
- Comprehensive logging throughout the system
- Health check endpoints
- Database statistics
- Tool execution history
- Debug endpoints for troubleshooting
## 🔍 Troubleshooting
### Common Issues:
1. **Database Locked**: Wait a moment and retry - the system has automatic retry logic
2. **Order Not Found**: Verify the order number exists (check order 4 as reference)
3. **Book Not Found**: Use exact book titles from the inventory
4. **API Key Issues**: Ensure GOOGLE_API_KEY is set in .env file
### Debug Endpoints:
- `GET /health` - System health check
- `GET /stats` - Database statistics
- `GET /debug/orders` - Order debugging information
- `GET /db/status` - Database connection status
This documentation provides a comprehensive guide to understanding, installing, and using the Library AI Agent system. The combination of natural language processing with robust database operations makes it a powerful tool for library management.
