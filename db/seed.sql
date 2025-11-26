-- Library Management System Seed Data
-- This file contains the initial data for the AI Library Agent

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Clear existing data (in case of re-seeding)
DELETE FROM order_items;
DELETE FROM orders;
DELETE FROM books;
DELETE FROM customers;
DELETE FROM messages;
DELETE FROM tool_calls;
DELETE FROM sessions;

-- Reset auto-increment counters
DELETE FROM sqlite_sequence WHERE name IN ('orders', 'customers', 'order_items', 'messages', 'tool_calls');

-- Insert Books (10 books as required)
INSERT INTO books (isbn, title, author, price, stock) VALUES
('9780134685991', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 47.49, 25),
('9780201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 'Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides', 54.99, 18),
('9780135957059', 'The Pragmatic Programmer: Your Journey to Mastery', 'David Thomas, Andrew Hunt', 42.50, 32),
('9780321125217', 'Domain-Driven Design: Tackling Complexity in the Heart of Software', 'Eric Evans', 56.75, 12),
('9780134757599', 'Clean Architecture: A Craftsman''s Guide to Software Structure and Design', 'Robert C. Martin', 49.99, 22),
('9780134494166', 'Accelerate: The Science of Lean Software and DevOps', 'Nicole Forsgren, Jez Humble, Gene Kim', 39.95, 15),
('9780136554828', 'Site Reliability Engineering: How Google Runs Production Systems', 'Betsy Beyer, Chris Jones, Jennifer Petoff, Niall Richard Murphy', 51.25, 8),
('9780132350884', 'Working Effectively with Legacy Code', 'Michael Feathers', 45.00, 20),
('9780321942067', 'Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation', 'Jez Humble, David Farley', 52.99, 14),
('9780137054899', 'The Clean Coder: A Code of Conduct for Professional Programmers', 'Robert C. Martin', 38.95, 28);

-- Insert Customers (6 customers as required)
INSERT INTO customers (name, email) VALUES
('Alice Johnson', 'alice.johnson@email.com'),
('Bob Smith', 'bob.smith@email.com'),
('Carol Davis', 'carol.davis@email.com'),
('David Wilson', 'david.wilson@email.com'),
('Eva Brown', 'eva.brown@email.com'),
('Frank Miller', 'frank.miller@email.com');

-- Insert Orders (4 orders as required)
INSERT INTO orders (customer_id, total_amount, status) VALUES
(1, 142.47, 'completed'),  -- Alice Johnson: 3 x Clean Code
(2, 54.99, 'completed'),   -- Bob Smith: 1 x Design Patterns
(3, 128.25, 'completed'),  -- Carol Davis: 3 x The Pragmatic Programmer
(4, 56.75, 'completed');   -- David Wilson: 1 x Domain-Driven Design

-- Insert Order Items
INSERT INTO order_items (order_id, book_isbn, quantity, unit_price) VALUES
(1, '9780134685991', 3, 47.49),   -- Order 1: 3 x Clean Code
(2, '9780201633610', 1, 54.99),   -- Order 2: 1 x Design Patterns
(3, '9780135957059', 3, 42.50),   -- Order 3: 3 x The Pragmatic Programmer
(4, '9780321125217', 1, 56.75);   -- Order 4: 1 x Domain-Driven Design

-- Update book stock to reflect the orders
UPDATE books 
SET stock = stock - (
    SELECT COALESCE(SUM(quantity), 0) 
    FROM order_items 
    WHERE order_items.book_isbn = books.isbn
);

-- Insert a sample chat session
INSERT INTO sessions (id, title) VALUES 
('sample-session-1', 'Book Inquiry Chat');

-- Insert sample messages for the chat session
INSERT INTO messages (session_id, role, content) VALUES
('sample-session-1', 'user', 'What programming books do you have available?'),
('sample-session-1', 'assistant', 'I found several programming books in our inventory. We have titles like "Clean Code", "Design Patterns", "The Pragmatic Programmer", and more. Is there a specific topic you''re interested in?');

-- Insert sample tool call (for demonstration)
INSERT INTO tool_calls (session_id, message_id, tool_name, input_args, output) VALUES
('sample-session-1', 2, 'find_books', '{"topic": "programming"}', 'Found 10 programming books in inventory');

-- Verify the data was inserted correctly
SELECT 'Books inserted: ' || COUNT(*) FROM books;
SELECT 'Customers inserted: ' || COUNT(*) FROM customers;
SELECT 'Orders inserted: ' || COUNT(*) FROM orders;
SELECT 'Order items inserted: ' || COUNT(*) FROM order_items;

-- Display current inventory summary
SELECT 'Current Inventory Summary:' as summary;
SELECT 
    title, 
    stock as current_stock,
    price
FROM books 
ORDER BY stock DESC;

-- Display order history
SELECT 'Recent Orders:' as orders;
SELECT 
    o.id as order_id,
    c.name as customer_name,
    o.total_amount,
    o.order_date
FROM orders o
JOIN customers c ON o.customer_id = c.id
ORDER BY o.order_date DESC;
