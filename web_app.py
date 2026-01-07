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
            
            # Extract filters
            filters = {}
            if request.form.get('domain'):
                filters['domain'] = request.form.getlist('domain')
            if request.form.get('content_type'):
                filters['content_type'] = request.form.getlist('content_type')
            if request.form.get('date'):
                filters['date'] = request.form.getlist('date')
            
            # Extract sort option
            sort_by = request.form.get('sort_by', 'relevance')
            
            if query:
                all_results = search_engine.search(query, top_k=100, filters=filters if filters else None, sort_by=sort_by)
                total_results = len(all_results)
                total_pages = (total_results + results_per_page - 1) // results_per_page
                
                # Handle spell correction
                spell_correction = None
                if all_results and 'spell_correction' in all_results[0]:
                    spell_correction = all_results[0]['spell_correction']
                    all_results = all_results[1:]  # Remove spell correction from results
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
                            popular_queries=search_history.get_popular_queries(5),
                            filter_options=search_engine.get_filter_options(),
                            current_filters=filters if 'filters' in locals() else {},
                            spell_correction=spell_correction if 'spell_correction' in locals() else None,
                            sort_by=sort_by if 'sort_by' in locals() else 'relevance')
    
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
