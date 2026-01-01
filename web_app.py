from flask import Flask, request, render_template
from config import HOST, PORT, DEBUG


def create_app(search_engine):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    @app.route('/', methods=['GET', 'POST'])
    def home():
        query = ''
        results = []
        
        if request.method == 'POST':
            query = request.form.get('query', '')
            if query:
                results = search_engine.search(query)
        
        return render_template('index.html', query=query, results=results)
    
    return app


def run_app(search_engine):
    """Run the Flask web application"""
    app = create_app(search_engine)
    print("\n=== Starting web server ===")
    print(f"Open your browser and go to: http://localhost:{PORT}")
    print("Press Ctrl+C to stop\n")
    app.run(host=HOST, port=PORT, debug=DEBUG)
