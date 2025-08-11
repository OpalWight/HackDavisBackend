import React, { useState } from 'react';
import { motion } from 'framer-motion';
import './styles.css';

function App() {
  const [locations, setLocations] = useState(['', '']);
  const [start1, setStart1] = useState('');
  const [end1, setEnd1] = useState('');
  const [start2, setStart2] = useState('');
  const [end2, setEnd2] = useState('');
  const [mapHtml, setMapHtml] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const testBackend = async () => {
    try {
      console.log('Testing backend connection via proxy...');
      const response = await fetch('/api/test');
      const data = await response.json();
      console.log('Backend test response:', data);
      alert('Backend is working via proxy! Check console for details.');
    } catch (err) {
      console.error('Proxy test failed:', err);
      
      // Try direct connection
      try {
        console.log('Testing direct backend connection...');
        const directResponse = await fetch('http://localhost:5000/api/test');
        const directData = await directResponse.json();
        console.log('Direct backend test response:', directData);
        alert('Backend is working but proxy failed! Using direct connection. Check console.');
      } catch (directErr) {
        console.error('Direct backend test also failed:', directErr);
        alert('Backend connection completely failed! Check if Flask server is running.');
      }
    }
  };

  const handleAddLocation = () => {
    setLocations([...locations, '']);
  };

  const handleLocationChange = (index: number, value: string) => {
    const newLocations = [...locations];
    newLocations[index] = value;
    setLocations(newLocations);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMapHtml('');
    setLoading(true);
    
    console.log('Form submitted with data:', {
      locations: locations.reduce((acc, loc, i) => ({ ...acc, [String.fromCharCode(65 + i)]: loc }), {}),
      start1,
      end1,
      start2,
      end2
    });
    
    try {
      console.log('Making request to /api/shortest-path...');
      const response = await fetch('/api/shortest-path', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          locations: locations.reduce((acc, loc, i) => ({ ...acc, [String.fromCharCode(65 + i)]: loc }), {}),
          start1,
          end1,
          start2,
          end2
        }),
      });
      
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      
      if (data.error) {
        setError(data.error + (data.traceback ? `\n\n${data.traceback}` : ''));
      } else {
        setMapHtml(data.map_html);
      }
    } catch (err) {
      console.error('Request failed:', err);
      setError(`Request failed: ${err instanceof Error ? err.message : 'An unexpected error occurred.'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      className="App"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h1>Find Shared Walking Path</h1>
      <p>This app helps two walkers find the most efficient shared path using a modified version of Dijkstra's algorithm. The system works as follows:</p>
      <ol>
        <li><b>Graph Creation:</b> First, the app creates a graph where each location is a node. The edges between the nodes are weighted by the walking distance between them, which is fetched from the OSRM (Open Source Routing Machine) API.</li>
        <li><b>Walker A's Path:</b> Dijkstra's algorithm is used to find the shortest path for Walker A from their start to end location.</li>
        <li><b>Shared Path Finding:</b> To find a path for Walker B that encourages sharing the path with Walker A, a new graph is created. In this new graph, the weights of the edges that are part of Walker A's path are reduced (multiplied by 0.5). This makes it more likely for Dijkstra's algorithm to choose these paths for Walker B.</li>
        <li><b>Walker B's Path:</b> Finally, Dijkstra's algorithm is run on the modified graph to find the shortest path for Walker B.</li>
      </ol>
      <p>Example: <br/> Location A: 1 Shields Ave, Davis, CA <br/> Location B: 500 1st St, Davis, CA <br/> Walker A Start: A <br/> Walker A End: B <br/> Walker B Start: B <br/> Walker B End: A</p>
      <form onSubmit={handleSubmit}>
        <h2>Locations</h2>
        {locations.map((location, index) => (
          <motion.div 
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
          >
            <input
              type="text"
              placeholder={`Location ${String.fromCharCode(65 + index)}`}
              value={location}
              onChange={(e) => handleLocationChange(index, e.target.value)}
            />
          </motion.div>
        ))}
        <motion.button 
          type="button" 
          onClick={handleAddLocation}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Add Location
        </motion.button>

        <motion.button 
          type="button" 
          onClick={testBackend}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{ marginLeft: '10px', backgroundColor: '#28a745' }}
        >
          Test Backend
        </motion.button>

        <h2>Walker A</h2>
        <input type="text" placeholder="Start" value={start1} onChange={(e) => setStart1(e.target.value)} />
        <input type="text" placeholder="End" value={end1} onChange={(e) => setEnd1(e.target.value)} />

        <h2>Walker B</h2>
        <input type="text" placeholder="Start" value={start2} onChange={(e) => setStart2(e.target.value)} />
        <input type="text" placeholder="End" value={end2} onChange={(e) => setEnd2(e.target.value)} />

        <motion.button 
          type="submit"
          disabled={loading}
          whileHover={{ scale: loading ? 1 : 1.05 }}
          whileTap={{ scale: loading ? 1 : 0.95 }}
          style={{ 
            opacity: loading ? 0.6 : 1,
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? (
            <span>
              <span className="loading-spinner">⏳</span> Finding Path...
            </span>
          ) : (
            'Find Path'
          )}
        </motion.button>
      </form>

      {error && 
        <motion.div 
          className="error"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <h2>Error</h2>
          <pre>{error}</pre>
        </motion.div>
      }

      {mapHtml && 
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div dangerouslySetInnerHTML={{ __html: mapHtml }} style={{ width: '100%', height: '600px' }} />
        </motion.div>
      }
    </motion.div>
  );
}

export default App;