from flask import Flask, request, jsonify
from flask_cors import CORS
from dijkstra import Dijkstra, create_walking_graph, create_map_visualization
import traceback

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://herdup-hackdavis.vercel.app')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'Backend is running!', 'endpoints': ['/api/test', '/api/shortest-path']})

@app.route('/api/test', methods=['GET', 'OPTIONS'])
def test_endpoint():
    if request.method == 'OPTIONS':
        return '', 200
    print("Test endpoint called!")
    return jsonify({'message': 'Backend is working!', 'status': 'ok'})

@app.route('/api/shortest-path', methods=['POST', 'OPTIONS'])
def get_shortest_path():
    if request.method == 'OPTIONS':
        return '', 200
    print("Received request to /api/shortest-path")
    try:
        data = request.get_json()
        print(f"Request data: {data}")
        
        locations = data.get('locations')
        start1 = data.get('start1')
        end1 = data.get('end1')
        start2 = data.get('start2')
        end2 = data.get('end2')

        print(f"Parsed data - locations: {locations}, start1: {start1}, end1: {end1}, start2: {start2}, end2: {end2}")

        if not all([locations, start1, end1, start2, end2]):
            print("Missing required data")
            return jsonify({'error': 'Missing required data'}), 400

        graph = create_walking_graph(locations)
        dijkstra = Dijkstra(graph)
        path1, path2, distance2 = dijkstra.find_shared_path(start1, end1, start2, end2)

        # Create map visualization
        map_obj, map_html = create_map_visualization(graph, path1, path2, locations, start1, start2)
        if map_obj:
            map_obj.save('walking_paths_map.html')

        return jsonify({
            'path1': path1,
            'path2': path2,
            'distance2': distance2,
            'map_html': map_html
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting Flask server on port {port}")
    print("Available endpoints:")
    print("  GET /api/test")
    print("  POST /api/shortest-path")
    app.run(debug=debug, host='0.0.0.0', port=port)