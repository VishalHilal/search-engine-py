from flask import Flask, request, render_template, jsonify
from config import HOST, PORT, DEBUG
from search_history import SearchHistory


def create_app(search_engine):
    """Create and configure Flask application"""
    app = Flask(__name__)
    search_history = SearchHistory()
    
    @app.route('/', methods=['GET', 'POST'])
    def home():
        query = ''
        results = []
        page = 1
        results_per_page = 10
        total_results = 0
        total_pages = 0
        
        if request.method == 'POST':
            query = request.form.get('query', '')
            page = int(request.form.get('page', 1))
            
            if query:
                all_results = search_engine.search(query, top_k=100)  # Get more results for pagination
                total_results = len(all_results)
                total_pages = (total_results + results_per_page - 1) // results_per_page
                
                # Add to search history (only on first page, not pagination)
                if page == 1:
                    search_history.add_search(query, total_results)
                
                # Get results for current page and add highlighting
                start_idx = (page - 1) * results_per_page
                end_idx = start_idx + results_per_page
                page_results = all_results[start_idx:end_idx]
                
                # Add highlighting to snippets
                for result in page_results:
                    result['snippet'] = search_engine.highlight_terms(result['snippet'], query)
                    result['title'] = search_engine.highlight_terms(result['title'], query)
                
                results = page_results
        
        return render_template('index.html', 
                            query=query, 
                            results=results, 
                            page=page,
                            total_pages=total_pages,
                            total_results=total_results,
                            results_per_page=results_per_page,
                            recent_searches=search_history.get_recent_searches(5),
                            popular_queries=search_history.get_popular_queries(5))
    
    @app.route('/suggest')
    def suggest():
        """Provide auto-complete suggestions"""
        query = request.args.get('q', '').lower()
        if len(query) < 2:
            return jsonify([])
        
        suggestions = search_engine.get_suggestions(query, limit=10)
        return jsonify(suggestions)
    
    @app.route('/clear_history')
    def clear_history():
        """Clear search history"""
        search_history.clear_history()
        return jsonify({'status': 'success'})
    
    return app


def run_app(search_engine):
    """Run the Flask web application"""
    app = create_app(search_engine)
    print("\n=== Starting web server ===")
    print(f"Open your browser and go to: http://localhost:{PORT}")
    print("Press Ctrl+C to stop\n")
    app.run(host=HOST, port=PORT, debug=DEBUG)
