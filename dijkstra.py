import heapq
import folium
from geopy.geocoders import Nominatim
import requests
import json
import time
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from functools import lru_cache

class Dijkstra:
    def __init__(self, graph):
        self.graph = graph
        self.distances = {}
        self.previous = {}
        self.visited = set()
        
    def find_shortest_path(self, start, end):
        # Initialize distances
        for node in self.graph:
            self.distances[node] = float('infinity')
        self.distances[start] = 0
        
        # Priority queue
        priority_queue = [(0, start)]
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            if current_node == end:
                break
                
            if current_node in self.visited:
                continue
                
            self.visited.add(current_node)
            
            for neighbor, weight in self.graph[current_node].items():
                distance = current_distance + weight
                if distance < self.distances[neighbor]:
                    self.distances[neighbor] = distance
                    self.previous[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))
        
        # Reconstruct path
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = self.previous.get(current)
        path.reverse()
        
        return path, self.distances[end]

    def find_shared_path(self, start1, end1, start2, end2):
        # Reset state for first path finding
        self.distances = {}
        self.previous = {}
        self.visited = set()
        
        # Find first walker's path
        path1, _ = self.find_shortest_path(start1, end1)
        
        # Create a new graph that favors nodes in path1
        shared_graph = {}
        for node in self.graph:
            shared_graph[node] = {}
            for neighbor, weight in self.graph[node].items():
                # If the neighbor is in path1, reduce its weight to encourage using it
                if neighbor in path1:
                    shared_graph[node][neighbor] = weight * 0.5  # Reduce weight by half
                else:
                    shared_graph[node][neighbor] = weight
        
        # Reset state for second path finding
        self.distances = {}
        self.previous = {}
        self.visited = set()
        
        # Find second walker's path using the modified graph
        original_graph = self.graph
        self.graph = shared_graph
        path2, distance2 = self.find_shortest_path(start2, end2)
        self.graph = original_graph  # Restore original graph
        
        return path1, path2, distance2

# Cache coordinates to avoid repeated API calls
@lru_cache(maxsize=100)
def get_coordinates(location_name):
    geolocator = Nominatim(user_agent="dijkstra_path_finder", timeout=10)
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
    except (GeocoderUnavailable, GeocoderTimedOut):
        pass
    return None

# Cache walking distances
@lru_cache(maxsize=1000)
def get_walking_distance(coord1, coord2):
    # OSRM API endpoint for walking
    url = f"http://router.project-osrm.org/route/v1/foot/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['routes']:
                distance_km = data['routes'][0]['distance'] / 1000
                # Convert to miles
                distance_miles = distance_km * 0.621371
                return distance_miles
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        pass
    return float('infinity')

def create_walking_graph(locations):
    graph = {}
    coordinates = {}
    
    print("\nGetting coordinates for locations...")
    # Get coordinates for all locations
    for node, location in locations.items():
        coords = get_coordinates(location)
        if coords:
            coordinates[node] = coords
            graph[node] = {}
            print(f"✓ Found coordinates for {location}")
        else:
            print(f"✗ Could not find coordinates for {location}")
    
    print("\nCalculating walking distances...")
    # Calculate walking distances between all pairs
    total_pairs = len(coordinates) * (len(coordinates) - 1) // 2  # Only calculate each pair once
    current_pair = 0
    
    nodes = list(coordinates.keys())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            node1, node2 = nodes[i], nodes[j]
            current_pair += 1
            print(f"Calculating distance {current_pair}/{total_pairs}...")
            distance = get_walking_distance(coordinates[node1], coordinates[node2])
            # Only add edges for distances under 10 miles
            if distance <= 10:
                graph[node1][node2] = distance
                graph[node2][node1] = distance  # Add reverse edge
    
    return graph

def create_map_visualization(graph, path1, path2, locations):
    # Create a map centered at the first location of path1
    start_coords = get_coordinates(locations[path1[0]])
    if not start_coords:
        print(f"Could not find coordinates for {locations[path1[0]]}")
        return None, None
    
    m = folium.Map(location=start_coords, zoom_start=15)
    
    # Add markers for all locations
    for node in graph:
        coords = get_coordinates(locations[node])
        if coords:
            folium.Marker(
                location=coords,
                popup=locations[node],
                icon=folium.Icon(color='blue')
            ).add_to(m)
    
    # Draw Walker A's path
    if len(path1) > 1:
        coords_str = ";".join([f"{get_coordinates(locations[node])[1]},{get_coordinates(locations[node])[0]}" for node in path1])
        url = f"http://router.project-osrm.org/route/v1/foot/{coords_str}?geometries=geojson"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['routes']:
                    route = data['routes'][0]['geometry']['coordinates']
                    route = [[coord[1], coord[0]] for coord in route]
                    folium.PolyLine(
                        route,
                        weight=2,
                        color='red',
                        opacity=0.8,
                        popup="Walker A's Path"
                    ).add_to(m)
        except requests.exceptions.RequestException:
            pass
    
    # Draw Walker B's path
    if len(path2) > 1:
        coords_str = ";".join([f"{get_coordinates(locations[node])[1]},{get_coordinates(locations[node])[0]}" for node in path2])
        url = f"http://router.project-osrm.org/route/v1/foot/{coords_str}?geometries=geojson"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['routes']:
                    route = data['routes'][0]['geometry']['coordinates']
                    route = [[coord[1], coord[0]] for coord in route]
                    folium.PolyLine(
                        route,
                        weight=2,
                        color='green',
                        opacity=0.8,
                        popup="Walker B's Path"
                    ).add_to(m)
        except requests.exceptions.RequestException:
            pass
    
    # Return both the map object and its HTML representation
    return m, m._repr_html_()

def get_user_input():
    locations = {}
    print("\nEnter the addresses (press Enter twice to finish):")
    print("Format: Street Address, City, State")
    print("\nExample addresses in Davis:")
    print("A: 1 Shields Ave, Davis, CA (UC Davis)")
    print("B: 500 1st St, Davis, CA (Downtown)")
    print("C: 2191 Cowell Blvd, Davis, CA (Trader Joe's)")
    print("D: 2001 2nd St, Davis, CA (Davis Commons)")
    print("E: 500 1st St, Davis, CA (Davis Farmers Market)")
    
    while True:
        address = input("\nEnter an address (or press Enter to finish): ").strip()
        if not address:
            break
        locations[chr(65 + len(locations))] = address
    
    if len(locations) < 4:  # Need at least 4 points for two walkers
        print("Please enter at least 4 addresses (2 for each walker)")
        return None
    
    return locations

# Main program
if __name__ == "__main__":
    locations = get_user_input()
    if not locations:
        exit()
    
    # Create graph with walking distances
    print("\nCalculating walking distances... (this may take a moment)")
    graph = create_walking_graph(locations)
    
    # Create Dijkstra instance
    dijkstra = Dijkstra(graph)
    
    # Find shortest path between all pairs
    print("\nAvailable locations:")
    for node, location in locations.items():
        print(f"{node}: {location}")
    
    print("\nEnter Walker A's locations:")
    start1 = input("Start location (A, B, C, etc.): ").upper()
    end1 = input("End location (A, B, C, etc.): ").upper()
    
    print("\nEnter Walker B's locations:")
    start2 = input("Start location (A, B, C, etc.): ").upper()
    end2 = input("End location (A, B, C, etc.): ").upper()
    
    if not all(node in locations for node in [start1, end1, start2, end2]):
        print("Invalid locations. Please try again.")
        exit()
    
    path1, path2, distance2 = dijkstra.find_shared_path(start1, end1, start2, end2)
    
    print(f"\nWalker A's path from {locations[start1]} to {locations[end1]}:")
    for node in path1:
        print(f"- {locations[node]}")
    
    print(f"\nWalker B's path from {locations[start2]} to {locations[end2]}:")
    for node in path2:
        print(f"- {locations[node]}")
    print(f"Total distance: {distance2:.1f} miles")
    
    # Create and display the map
    m, map_html = create_map_visualization(graph, path1, path2, locations)
    if m:
        m.save('walking_paths_map.html')
        print("\nMap saved as 'walking_paths_map.html'") 