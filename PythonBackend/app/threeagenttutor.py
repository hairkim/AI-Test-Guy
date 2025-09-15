import wolframalpha
import re
import math
import requests
import json

class ConversationalSATTutor:
    def __init__(self, llm_wrapper, wolfram_app_id):
        self.llm = llm_wrapper
        self.computation_tool = SATComputationEngine(wolfram_app_id, llm_wrapper)
        print(f"Wolfram App ID: {wolfram_app_id if wolfram_app_id else 'None'}")
    
    def solve(self, question: str):
        prompt = f"""
        You are a friendly SAT math tutor. Solve this step-by-step with conversational explanations.
        
        When you need to calculate something, write COMPUTE[expression or description] and I'll handle the math.

        Make sure to include step by step explanations, especially for complex problems and make sure that the student doesn't have any other questions.
        
        Examples of COMPUTE usage:
        - COMPUTE[3 + 5] for basic arithmetic
        - COMPUTE[solve 2x + 7 = 15] for equations
        - COMPUTE[sqrt(25)] for square roots
        - COMPUTE[area of circle with radius 5] for geometry
        
        Question: {question}
        
        Show your thinking process, explain why you're taking each step, and be encouraging.
        Format your response using Markdown:
        - Use ## for section headers
        - Use **bold** for key numbers and concepts  
        - Use bullet points for given information
        - Use numbered lists for solution steps
        - Use code blocks for formulas: ```formula here```
        - Add a clear "Answer" section at the end
        """
        
        # Get response with COMPUTE tags
        response = self.llm.predict(prompt)
        print(f"Response: {response}")
        
        # Process COMPUTE tags using the tool
        final_response = self.process_compute_tags(response)
        print(f"Final response: {final_response}")
        
        return final_response
    
    def process_compute_tags(self, text):
        def compute(match):
            request = match.group(1)
            result = self.computation_tool.compute(request)
            print(f"Result for compute '{request}': {result}")
            return str(result)
        
        return re.sub(r'COMPUTE\[(.*?)\]', compute, text)

class CustomWolframClient:
    def __init__(self, app_id):
        self.app_id = app_id
        self.base_url = "http://api.wolframalpha.com/v2/query"
    
    def query(self, query_string):
        """
        Query Wolfram Alpha and return a result object similar to the original library
        """
        params = {
            'input': query_string,
            'appid': self.app_id,
            'format': 'plaintext',
            'output': 'JSON'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}")
            
            data = response.json()
            return WolframResult(data)
            
        except Exception as e:
            raise Exception(f"Wolfram query failed: {e}")


class WolframResult:
    """
    Mock the structure that the original wolframalpha library returns
    """
    def __init__(self, json_data):
        self.raw_data = json_data
        self.success = json_data.get('queryresult', {}).get('success', False)
        self.pods = []
        
        if self.success:
            pods_data = json_data.get('queryresult', {}).get('pods', [])
            for pod_data in pods_data:
                self.pods.append(WolframPod(pod_data))


class WolframPod:
    """
    Mock the Pod structure from the original library
    """
    def __init__(self, pod_data):
        self.title = pod_data.get('title', '')
        self.text = self._extract_text(pod_data)
    
    def _extract_text(self, pod_data):
        """
        Extract text from subpods
        """
        subpods = pod_data.get('subpods', [])
        if not subpods:
            return ''
        
        # Get text from the first subpod
        first_subpod = subpods[0]
        return first_subpod.get('plaintext', '')


# Updated SATComputationEngine to use the custom client
class SATComputationEngine:
    def __init__(self, app_id, llm_wrapper):
        self.wolfram_client = CustomWolframClient(app_id) if app_id else None
        self.llm = llm_wrapper
    
    def compute(self, compute_request: str):
        """
        Main compute method that tries Wolfram Alpha first, then falls back to Python
        """
        print(f"Computing: {compute_request}")
        
        # Try Wolfram Alpha first
        if self.wolfram_client:
            try:
                wolfram_result = self.try_wolfram(compute_request)
                if wolfram_result and wolfram_result != "Could not extract answer":
                    return wolfram_result
            except Exception as e:
                print(f"Wolfram Alpha failed: {e}")
        
        # Fall back to Python computation
        return self.fallback_compute(compute_request)
    
    def try_wolfram(self, request: str):
        """
        Try to compute using Wolfram Alpha
        """
        try:
            # Clean and prepare the query
            wolfram_query = self.prepare_wolfram_query(request)
            print(f"Wolfram query: '{wolfram_query}'")
            
            result = self.wolfram_client.query(wolfram_query)
            
            if not result.success:
                print("Wolfram query was not successful")
                return None
                
            answer = self.extract_wolfram_answer(result)
            print(f"Wolfram result: {answer}")
            return answer
            
        except Exception as e:
            print(f"Wolfram Alpha error: {e}")
            return None
    
    def prepare_wolfram_query(self, request: str):
        """
        Prepare the request for Wolfram Alpha
        """
        request = request.strip()
        
        # If it's already a simple mathematical expression, use it directly
        if self.is_simple_math(request):
            return request
        
        # Otherwise, let the LLM help convert it
        return self.convert_to_wolfram_query(request)
    
    def is_simple_math(self, expression: str):
        """
        Check if this looks like a simple mathematical expression
        """
        # Remove spaces and check if it contains only numbers and basic operators
        cleaned = expression.replace(' ', '')
        allowed_chars = set('0123456789+-*/().^')
        return all(c in allowed_chars for c in cleaned) and any(c in '+-*/' for c in cleaned)
    
    def convert_to_wolfram_query(self, request: str):
        """
        Use LLM to convert complex requests to Wolfram queries
        """
        prompt = f"""
        Convert this computation request to a Wolfram Alpha query.
        
        Request: {request}
        
        Examples:
        "solve 2x + 7 = 15" → "solve 2x + 7 = 15"
        "area of circle with radius 5" → "area of circle radius 5"
        "expand (x + 3)^2" → "expand (x + 3)^2"
        "square root of 25" → "sqrt(25)"
        "3 + 5" → "3 + 5"
        
        Return only the Wolfram query (no quotes or extra text):
        """
        
        result = self.llm.predict(prompt).strip()
        # Remove quotes if the LLM added them
        result = result.strip('"\'')
        return result
    
    def extract_wolfram_answer(self, result):
        """
        Extract the answer from Wolfram Alpha results
        """
        try:
            # Look for pods with answers in order of preference
            preferred_titles = ["Result", "Solution", "Decimal form", "Exact result", "Value"]
            
            for title in preferred_titles:
                for pod in result.pods:
                    if pod.title == title and pod.text:
                        return pod.text.split('\n')[0]  # Take first line
            
            # If no preferred pod found, take the second pod (first is usually the input)
            if len(result.pods) > 1 and result.pods[1].text:
                return result.pods[1].text.split('\n')[0]
                
            return "Could not extract answer"
            
        except Exception as e:
            print(f"Error extracting Wolfram answer: {e}")
            return "Could not extract answer"
    
    def fallback_compute(self, request: str):
        """
        Python-based computation fallback
        """
        try:
            # Handle simple arithmetic expressions
            if self.is_simple_math(request):
                # Use eval for simple math (be careful with this in production!)
                result = eval(request.replace('^', '**'))  # Handle exponents
                return str(result)
            
            # Handle some common functions
            request_lower = request.lower()
            
            if 'sqrt' in request_lower:
                # Extract number from sqrt expression
                import re, math
                match = re.search(r'sqrt\((\d+(?:\.\d+)?)\)', request_lower)
                if match:
                    number = float(match.group(1))
                    return str(math.sqrt(number))
            
            if 'square root of' in request_lower:
                # Extract number after "square root of"
                import re, math
                match = re.search(r'square root of (\d+(?:\.\d+)?)', request_lower)
                if match:
                    number = float(match.group(1))
                    return str(math.sqrt(number))
            
            return f"Cannot compute: {request}"
            
        except Exception as e:
            print(f"Fallback computation error: {e}")
            return f"Error computing: {request}"


# class SATComputationEngine:
#     def __init__(self, wolfram_client, llm_wrapper):
#         self.wolfram_client = wolfram_client
#         self.llm = llm_wrapper
    
#     def compute(self, compute_request: str):
#         """
#         Main compute method that tries Wolfram Alpha first, then falls back to Python
#         """
#         print(f"Computing: {compute_request}")
        
#         # Try Wolfram Alpha first
#         if self.wolfram_client:
#             try:
#                 wolfram_result = self.try_wolfram(compute_request)
#                 if wolfram_result and wolfram_result != "Could not extract answer":
#                     return wolfram_result
#             except Exception as e:
#                 print(f"Wolfram Alpha failed: {e}")
        
#         # Fall back to Python computation
#         return self.fallback_compute(compute_request)
    
#     def try_wolfram(self, request: str):
#         """
#         Try to compute using Wolfram Alpha
#         """
#         try:
#             # Check if client exists
#             if not self.wolfram_client:
#                 print("No Wolfram client available")
#                 return None
                
#             # Clean and prepare the query
#             wolfram_query = self.prepare_wolfram_query(request)
#             print(f"Wolfram query: '{wolfram_query}'")
            
#             result = self.wolfram_client.query(wolfram_query)
            
#             # Check if result is valid
#             if not result:
#                 print("Wolfram returned empty result")
#                 return None
                
#             answer = self.extract_wolfram_answer(result)
#             print(f"Wolfram result: {answer}")
#             return answer
            
#         except Exception as e:
#             print(f"Wolfram Alpha error: {repr(e)}")  # Use repr() to see the actual exception
#             print(f"Wolfram Alpha error type: {type(e)}")
#             return None
    
#     def prepare_wolfram_query(self, request: str):
#         """
#         Prepare the request for Wolfram Alpha
#         """
#         request = request.strip()
        
#         # If it's already a simple mathematical expression, use it directly
#         if self.is_simple_math(request):
#             return request
        
#         # Otherwise, let the LLM help convert it
#         return self.convert_to_wolfram_query(request)
    
#     def is_simple_math(self, expression: str):
#         """
#         Check if this looks like a simple mathematical expression
#         """
#         # Remove spaces and check if it contains only numbers and basic operators
#         cleaned = expression.replace(' ', '')
#         allowed_chars = set('0123456789+-*/().^')
#         return all(c in allowed_chars for c in cleaned) and any(c in '+-*/' for c in cleaned)
    
#     def convert_to_wolfram_query(self, request: str):
#         """
#         Use LLM to convert complex requests to Wolfram queries
#         """
#         prompt = f"""
#         Convert this computation request to a Wolfram Alpha query.
        
#         Request: {request}
        
#         Examples:
#         "solve 2x + 7 = 15" → "solve 2x + 7 = 15"
#         "area of circle with radius 5" → "area of circle radius 5"
#         "expand (x + 3)^2" → "expand (x + 3)^2"
#         "square root of 25" → "sqrt(25)"
#         "3 + 5" → "3 + 5"
        
#         Return only the Wolfram query (no quotes or extra text):
#         """
        
#         result = self.llm.predict(prompt).strip()
#         # Remove quotes if the LLM added them
#         result = result.strip('"\'')
#         return result
    
#     def extract_wolfram_answer(self, result):
#         """
#         Extract the answer from Wolfram Alpha results
#         """
#         try:
#             # Look for pods with answers in order of preference
#             preferred_titles = ["Result", "Solution", "Decimal form", "Exact result", "Value"]
            
#             for title in preferred_titles:
#                 for pod in result.pods:
#                     if pod.title == title and pod.text:
#                         return pod.text.split('\n')[0]  # Take first line
            
#             # If no preferred pod found, take the second pod (first is usually the input)
#             if len(result.pods) > 1 and result.pods[1].text:
#                 return result.pods[1].text.split('\n')[0]
                
#             return "Could not extract answer"
            
#         except Exception as e:
#             print(f"Error extracting Wolfram answer: {e}")
#             return "Could not extract answer"
    
#     def fallback_compute(self, request: str):
#         """
#         Python-based computation fallback
#         """
#         try:
#             # Handle simple arithmetic expressions
#             if self.is_simple_math(request):
#                 # Use eval for simple math (be careful with this in production!)
#                 result = eval(request.replace('^', '**'))  # Handle exponents
#                 return str(result)
            
#             # Handle some common functions
#             request_lower = request.lower()
            
#             if 'sqrt' in request_lower:
#                 # Extract number from sqrt expression
#                 match = re.search(r'sqrt\((\d+(?:\.\d+)?)\)', request_lower)
#                 if match:
#                     number = float(match.group(1))
#                     return str(math.sqrt(number))
            
#             if 'square root of' in request_lower:
#                 # Extract number after "square root of"
#                 match = re.search(r'square root of (\d+(?:\.\d+)?)', request_lower)
#                 if match:
#                     number = float(match.group(1))
#                     return str(math.sqrt(number))
            
#             # Add more mathematical operations as needed
            
#             return f"Cannot compute: {request}"
            
#         except Exception as e:
#             print(f"Fallback computation error: {e}")
#             return f"Error computing: {request}"