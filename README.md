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
git clone https://github.com/Yosef024/menadevs_task.git
cd menadevs_task
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
aiohappyeyeballs==2.6.1
aiohttp==3.13.2
aiosignal==1.4.0
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.11.0
attrs==25.4.0
cachetools==6.2.2
certifi==2025.11.12
cffi==2.0.0
charset-normalizer==3.4.4
click==8.3.1
colorama==0.4.6
cryptography==46.0.3
dataclasses-json==0.6.7
faiss-cpu==1.13.0
fastapi==0.122.0
filelock==3.20.0
filetype==1.2.0
frozenlist==1.8.0
fsspec==2025.10.0
google-ai-generativelanguage==0.9.0
google-api-core==2.28.1
google-api-python-client==2.187.0
google-auth==2.43.0
google-auth-httplib2==0.2.1
google-genai==1.52.0
google-generativeai==0.8.5
googleapis-common-protos==1.72.0
greenlet==3.2.4
grpcio==1.76.0
grpcio-status==1.71.2
h11==0.16.0
httpcore==1.0.9
httplib2==0.31.0
httpx==0.28.1
httpx-sse==0.4.3
huggingface-hub==0.36.0
idna==3.11
Jinja2==3.1.6
joblib==1.5.2
jsonpatch==1.33
jsonpointer==3.0.0
langchain==1.1.0
langchain-classic==1.0.0
langchain-community==0.4.1
langchain-core==1.1.0
langchain-google-genai==3.2.0
langchain-text-splitters==1.0.0
langgraph==1.0.3
langgraph-checkpoint==3.0.1
langgraph-prebuilt==1.0.5
langgraph-sdk==0.2.10
langsmith==0.4.47
MarkupSafe==3.0.3
marshmallow==3.26.1
mpmath==1.3.0
multidict==6.7.0
mypy_extensions==1.1.0
networkx==3.6
numpy==2.3.5
orjson==3.11.4
ormsgpack==1.12.0
packaging==25.0
pdfminer.six==20251107
pdfplumber==0.11.8
pillow==12.0.0
propcache==0.4.1
proto-plus==1.26.1
protobuf==5.29.5
pyasn1==0.6.1
pyasn1_modules==0.4.2
pycparser==2.23
pydantic==2.12.4
pydantic-settings==2.12.0
pydantic_core==2.41.5
pyparsing==3.2.5
PyPDF2==3.0.1
pypdfium2==5.1.0
python-dotenv==1.2.1
python-multipart==0.0.20
PyYAML==6.0.3
regex==2025.11.3
requests==2.32.5
requests-toolbelt==1.0.0
rsa==4.9.1
safetensors==0.7.0
scikit-learn==1.7.2
scipy==1.16.3
sentence-transformers==5.1.2
setuptools==80.9.0
sniffio==1.3.1
SQLAlchemy==2.0.44
starlette==0.50.0
sympy==1.14.0
tenacity==9.1.2
threadpoolctl==3.6.0
tokenizers==0.22.1
torch==2.9.1
tqdm==4.67.1
transformers==4.57.2
typing-inspect==0.9.0
typing-inspection==0.4.2
typing_extensions==4.15.0
uritemplate==4.2.0
urllib3==2.5.0
uvicorn==0.38.0
websockets==15.0.1
xxhash==3.6.0
yarl==1.22.0
zstandard==0.25.0

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
uvicorn server.main:app --reload --port 8000 --host 0.0.0.0
# Start the user interface
python -m http.server 3000
important note: each command will be running on seperate terminal
```
**Terminal 2 - Frontend Access:**
```bash
# Open the application in your browser
# On macOS:
open http://localhost:3000/app
# On Windows:
start http://localhost:3000/app
# On Linux:
xdg-open http://localhost:3000/app
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
