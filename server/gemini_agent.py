import google.generativeai as genai
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import json

# Import the tools from your tools.py
from server.tools import (
    find_books_tool,
    create_order_tool,
    restock_book_tool,
    update_price_tool,
    order_status_tool,
    inventory_summary_tool,
    search_knowledge_base_tool,
    list_customers_tool
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiAgent:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini agent with tools."""
        api_key="AIzaSyBxP3lBmsVGj1WmiWYKTd0iujLINtohfJM"
        if api_key is None:
            api_key = "AIzaSyBxP3lBmsVGj1WmiWYKTd0iujLINtohfJM"
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Initialize the Gemini model
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Available tools
        self.tools = {
            "find_books": find_books_tool,
            "create_order": create_order_tool,
            "restock_book": restock_book_tool,
            "update_price": update_price_tool,
            "order_status": order_status_tool,
            "inventory_summary": inventory_summary_tool,
            "search_knowledge_base": search_knowledge_base_tool,
            "list_customers": list_customers_tool
        }
        
        # Tool usage history
        self.tool_usage_history = []
        
        logger.info("Gemini Agent initialized successfully")

    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze the user request to determine if tools are needed.
        """
        logger.info(f"Analyzing user request: {user_request}")

        analysis_prompt = f"""
        Analyze this library management request and determine if tools are needed.

        USER REQUEST: "{user_request}"

        AVAILABLE TOOLS:
        - find_books: Search books by title, author, price, or stock status
        - create_order: Create new orders for customers with book items
        - restock_book: Add more copies to book inventory  
        - update_price: Change book prices
        - order_status: Check order details and status
        - inventory_summary: Get inventory overview
        - search_knowledge_base: Search documentation
        - list_customers: Show all customers

        CRITICAL: You MUST use create_order tool when the user mentions:
        - Selling books to customers
        - Creating orders
        - Processing sales
        - Customer purchases

        Respond with ONLY this JSON format (no other text):
        {{
            "needs_tools": true or false,
            "tools_needed": ["tool1", "tool2"],
            "reasoning": "Brief explanation",
            "action_type": "order|search|inventory|knowledge|other"
        }}
        """

        try:
            response = self.model.generate_content(analysis_prompt)
            analysis_result = self._parse_json_response(response.text)

            # Handle case where result is a list instead of dict
            if isinstance(analysis_result, list):
                if analysis_result:
                    analysis_result = analysis_result[0]
                else:
                    analysis_result = {}

            # Ensure we have the required fields with defaults
            if not isinstance(analysis_result, dict):
                analysis_result = {}

            # Set defaults for missing fields
            analysis_result.setdefault("needs_tools", False)
            analysis_result.setdefault("tools_needed", [])
            analysis_result.setdefault("reasoning", "Analysis completed")
            analysis_result.setdefault("action_type", "other")

            logger.info(f"Request analysis completed: needs_tools={analysis_result.get('needs_tools', False)}, tools={analysis_result.get('tools_needed', [])}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing request: {str(e)}")
            return {
                "needs_tools": False,
                "tools_needed": [],
                "reasoning": f"Error during analysis: {str(e)}",
                "action_type": "error"
            }

    def execute_tools(self, tool_decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the required tools with parameter validation."""
        results = []

        for tool_decision in tool_decisions:
            tool_name = tool_decision.get("tool_name")
            parameters = tool_decision.get("parameters", {})

            if tool_name in self.tools:
                logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")

                try:
                    # Validate parameters before execution
                    if tool_name == "restock_book" and parameters.get("quantity", 0) <= 0:
                        error_msg = f"Cannot use restock_book with non-positive quantity: {parameters.get('quantity')}"
                        logger.error(error_msg)
                        results.append({
                            "tool_name": tool_name,
                            "result": error_msg,
                            "success": False
                        })
                        continue
                    
                    # Execute the tool
                    tool_result = self.tools[tool_name].run(parameters)

                    # Save tool usage
                    usage_record = {
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "result": tool_result,
                        "success": True
                    }
                    self.tool_usage_history.append(usage_record)

                    results.append({
                        "tool_name": tool_name,
                        "result": tool_result,
                        "success": True
                    })

                    logger.info(f"Tool {tool_name} executed successfully")

                except Exception as e:
                    error_msg = f"Error executing tool {tool_name}: {str(e)}"
                    logger.error(error_msg)

                    usage_record = {
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "result": error_msg,
                        "success": False
                    }
                    self.tool_usage_history.append(usage_record)

                    results.append({
                        "tool_name": tool_name,
                        "result": error_msg,
                        "success": False
                    })
            else:
                error_msg = f"Unknown tool: {tool_name}"
                logger.error(error_msg)
                results.append({
                    "tool_name": tool_name,
                    "result": error_msg,
                    "success": False
                })

        return results

    def determine_tool_parameters(self, user_request: str, tools_needed: List[str]) -> List[Dict[str, Any]]:
        """Determine the parameters for each tool needed."""
        if not tools_needed:
            return []
        
        tools_list = ", ".join(tools_needed)
        
        # Create a book title to ISBN mapping
        book_isbn_mapping = {
            "clean code": "9780134685991",
            "design patterns": "9780201633610",
            "the pragmatic programmer": "9780135957059", 
            "domain-driven design": "9780321125217",
            "clean architecture": "9780134757599",
            "accelerate": "9780134494166",
            "site reliability engineering": "9780136554828",
            "working effectively with legacy code": "9780132350884",
            "continuous delivery": "9780321942067",
            "the clean coder": "9780137054899"
        }
        
        parameter_prompt = f"""
        Based on this user request: "{user_request}"
        
        Determine parameters for these tools: {tools_list}
        
        BOOK ISBN MAPPING (USE THESE EXACT ISBNs):
        {json.dumps(book_isbn_mapping, indent=2)}
        
        TOOL DESCRIPTIONS:
        - find_books: Search books (title, author, max_price, in_stock)
        - create_order: Create order (customer_id, items list with ISBN and quantity)
        - restock_book: Add stock (isbn, quantity) - quantity must be positive
        - update_price: Change price (isbn, new_price)
        - order_status: Check order (order_id)
        - inventory_summary: No parameters
        - search_knowledge_base: Search (query)
        - list_customers: No parameters
        
        IMPORTANT: 
        - For book titles, use the EXACT ISBN from the mapping above
        - For "Clean Code" use ISBN 9780134685991
        - For "The Pragmatic Programmer" use ISBN 9780135957059
        - create_order automatically adjusts stock - no need for restock_book
        
        Return ONLY JSON array (no other text):
        [
            {{
                "tool_name": "tool_name",
                "parameters": {{ ... }},
                "reasoning": "why these parameters"
            }}
        ]
        """
        
        try:
            response = self.model.generate_content(parameter_prompt)
            tool_decisions = self._parse_json_response(response.text)
            
            # Handle case where result is not a list
            if tool_decisions is None:
                tool_decisions = []
            elif isinstance(tool_decisions, dict):
                tool_decisions = [tool_decisions]
            elif not isinstance(tool_decisions, list):
                tool_decisions = []
                
            logger.info(f"Determined parameters for {len(tool_decisions)} tools: {[t.get('tool_name') for t in tool_decisions]}")
            return tool_decisions
            
        except Exception as e:
            logger.error(f"Error determining tool parameters: {str(e)}")
            return []

    def generate_final_response(self, user_request: str, tool_results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Generate a final response to the user based on the tool results."""
        logger.info("Generating final response")

        # Check for database lock errors in tool results
        db_lock_errors = any(
            "database is locked" in str(result.get('result', '')).lower() 
            or "database is busy" in str(result.get('result', '')).lower()
            for result in tool_results
        )

        if db_lock_errors:
            return "I'm experiencing high database traffic right now. Please try your request again in a few moments. The system should be available shortly."

        # Prepare context for the final response
        tool_results_summary = "\n".join([
            f"Tool: {result['tool_name']}\nResult: {result['result']}\nSuccess: {result['success']}\n"
            for result in tool_results
        ])

        final_prompt = f"""
        You are a helpful library desk assistant. Based on the user's request and the results from the tools executed, 
        provide a clear, helpful final response to the user.

        User's original request: "{user_request}"

        Analysis of request: {analysis.get('reasoning', 'N/A')}

        Tools executed and their results:
        {tool_results_summary}

        Please provide:
        1. A natural, conversational response that directly addresses the user's request
        2. Include relevant information from the tool results
        3. If any tools failed, mention this politely and suggest alternatives
        4. Keep the response helpful and professional
        5. Don't mention the internal tools or technical details unless necessary

        Respond with just the final message to the user.
        """

        try:
            response = self.model.generate_content(final_prompt)
            final_response = response.text.strip()

            logger.info("Final response generated successfully")
            return final_response

        except Exception as e:
            error_msg = f"Error generating final response: {str(e)}"
            logger.error(error_msg)
            return "I apologize, but I encountered an error while processing your request. Please try again."
    
    def _parse_json_response(self, text: str) -> Any:
        """Parse JSON response from the model, handling potential formatting issues."""
        try:
            # Clean the response - remove markdown code blocks and extra whitespace
            cleaned_text = text.strip()

            # Remove ```json and ``` markers
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            # Try to parse the cleaned text directly first
            try:
                parsed = json.loads(cleaned_text)
                return parsed
            except json.JSONDecodeError:
                pass
            
            # If direct parsing fails, try to extract JSON
            start_idx = cleaned_text.find('[')  # Look for array start
            if start_idx == -1:
                start_idx = cleaned_text.find('{')  # Look for object start

            if start_idx != -1:
                # Find matching closing bracket/brace
                if cleaned_text[start_idx] == '[':
                    bracket_count = 0
                    for i in range(start_idx, len(cleaned_text)):
                        if cleaned_text[i] == '[':
                            bracket_count += 1
                        elif cleaned_text[i] == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_idx = i + 1
                                break
                else:  # object
                    brace_count = 0
                    for i in range(start_idx, len(cleaned_text)):
                        if cleaned_text[i] == '{':
                            brace_count += 1
                        elif cleaned_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                            
                if 'end_idx' in locals() and end_idx > start_idx:
                    json_str = cleaned_text[start_idx:end_idx]
                    return json.loads(json_str)

            # If all else fails, return empty dict
            logger.warning(f"Could not parse JSON from response: {text}")
            return {}

        except Exception as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Original text: {text}")
            return {}
    def process_request(self, user_request: str) -> Dict[str, Any]:
        """
        Main function to process a user request through the complete agentic workflow.
        """
        logger.info(f"Processing user request: {user_request}")

        try:
            # Step 1: Analyze the request
            analysis = self.analyze_request(user_request)

            # Step 2: Check if tools are needed
            needs_tools = analysis.get("needs_tools", False)
            tools_needed = analysis.get("tools_needed", [])

            tool_results = []
            tool_decisions = []

            if needs_tools and tools_needed:
                # Step 3: Determine tool parameters
                tool_decisions = self.determine_tool_parameters(user_request, tools_needed)

                # Step 4: Execute tools
                if tool_decisions:
                    tool_results = self.execute_tools(tool_decisions)

            # Step 5: Generate final response
            final_response = self.generate_final_response(user_request, tool_results, analysis)

            # Return complete execution results
            return {
                "final_response": final_response,
                "analysis": analysis,
                "tools_used": tool_decisions,
                "tool_results": tool_results,
                "needed_tools": needs_tools
            }

        except Exception as e:
            logger.error(f"Error in process_request: {str(e)}")
            return {
                "final_response": f"I encountered an error while processing your request: {str(e)}. Please try again.",
                "analysis": {"error": str(e)},
                "tools_used": [],
                "tool_results": [],
                "needed_tools": False
            }

    def get_tool_usage_history(self) -> List[Dict[str, Any]]:
        """Get the history of tool usage."""
        return self.tool_usage_history.copy()

    def clear_tool_history(self):
        """Clear the tool usage history."""
        self.tool_usage_history.clear()
        logger.info("Tool usage history cleared")


# Example usage and test function
def main():
    """Test the Gemini Agent with sample requests."""
    
    # Initialize the agent
    agent = GeminiAgent()
    
    # Test requests
    test_requests = [
        "What books do you have by George Orwell?",
        "I need to create an order for customer ID 2 for 2 copies of Clean Code",
        "Can you show me the current inventory summary?",
        "What's the status of order number 3?",
        "Tell me about Python programming best practices"
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{'='*50}")
        print(f"TEST {i}: {request}")
        print(f"{'='*50}")
        
        try:
            result = agent.process_request(request)
            print(f"FINAL RESPONSE:\n{result['final_response']}")
            print(f"\nAnalysis: {result['analysis']}")
            print(f"Tools used: {len(result['tools_used'])}")
            
        except Exception as e:
            print(f"Error processing request: {str(e)}")


if __name__ == "__main__":
    main()
