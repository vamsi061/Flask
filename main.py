# filename: main.py

import logging
import threading
from flask import Flask, request, jsonify, render_template
from search import run_search, hardcoded_fallback_urls
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            logger.info(f"Web search request received for query: {query}")
            result = run_search(query)
    return render_template('index.html', result=result)

@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        query = data['query']
        logger.info(f"API search request received for query: {query}")
        
        # Run the search in a separate thread with a timeout
        result = None
        error = None
        
        def search_thread():
            nonlocal result
            try:
                result = run_search(query)
            except Exception as e:
                logger.error(f"Search thread error: {e}", exc_info=True)
                result = {"error": f"An error occurred: {str(e)}"}
        
        thread = threading.Thread(target=search_thread)
        thread.start()
        thread.join(timeout=60)  # Wait up to 60 seconds
        
        if thread.is_alive():
            # If the thread is still running after timeout, return a fallback response instead of an error
            logger.warning(f"Search timed out for query: {query}")
            
            # Create a fallback response with basic information
            fallback_urls = hardcoded_fallback_urls(query)
            fallback_response = {
                "query": query,
                "summary": f"Here are some general resources related to '{query}'. The search took longer than expected, so we're providing these general results.",
                "sources": fallback_urls,
                "profile_images": []
            }
            
            return jsonify(fallback_response)
        
        if result is None:
            # Create a fallback response for unexpected errors
            fallback_urls = hardcoded_fallback_urls(query)
            fallback_response = {
                "query": query,
                "summary": f"Here are some general resources that might be related to '{query}'.",
                "sources": fallback_urls,
                "profile_images": []
            }
            return jsonify(fallback_response)
            
        if "error" in result:
            logger.warning(f"Search error: {result['error']}")
            # Replace error with fallback response
            fallback_urls = hardcoded_fallback_urls(query)
            fallback_response = {
                "query": query,
                "summary": f"Here are some general resources that might be related to '{query}'.",
                "sources": fallback_urls,
                "profile_images": []
            }
            return jsonify(fallback_response)
        
        logger.info(f"Search completed successfully for: {query}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)  # Log the full exception
        # Return fallback response instead of error
        fallback_urls = hardcoded_fallback_urls(query)
        fallback_response = {
            "query": query,
            "summary": f"Here are some general resources that might be related to '{query}'.",
            "sources": fallback_urls,
            "profile_images": []
        }
        return jsonify(fallback_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render injects PORT
    app.run(host='0.0.0.0', port=port, debug=True)
