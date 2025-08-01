import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';
import NewsPanel from './NewsPanel';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fix for default markers in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons for different event types
const createEventIcon = (eventType, severity) => {
  const colors = {
    earthquake: '#FF4444',
    flood: '#4444FF',
    fire: '#FF8800',
    storm: '#8844FF',
    health_emergency: '#FF44FF',
    infrastructure_failure: '#888888',
    other: '#44FF44'
  };
  
  const intensities = {
    low: 0.6,
    medium: 0.8,
    high: 1.0,
    critical: 1.0
  };
  
  const baseColor = colors[eventType] || colors.other;
  const opacity = intensities[severity] || 0.8;
  
  return L.divIcon({
    className: 'custom-crisis-marker',
    html: `<div style="
      background-color: ${baseColor};
      opacity: ${opacity};
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: bold;
      color: white;
    ">${getEventIcon(eventType)}</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13]
  });
};

const getEventIcon = (eventType) => {
  const icons = {
    earthquake: '🌋',
    flood: '🌊',
    fire: '🔥',
    storm: '🌪️',
    health_emergency: '🏥',
    infrastructure_failure: '⚠️',
    other: '📍'
  };
  return icons[eventType] || icons.other;
};

const getSeverityColor = (severity) => {
  const colors = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#dc2626'
  };
  return colors[severity] || colors.medium;
};

const NewsArticlesList = ({ articles }) => {
  if (!articles || articles.length === 0) return null;
  
  return (
    <div className="mt-3 border-t pt-3">
      <h5 className="font-medium text-sm text-gray-700 mb-2">📰 Related News</h5>
      <div className="space-y-2 max-h-32 overflow-y-auto">
        {articles.slice(0, 3).map((article, index) => (
          <div key={index} className="text-xs">
            <a 
              href={article.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 font-medium line-clamp-2"
            >
              {article.title}
            </a>
            <div className="text-gray-500 mt-1">
              {article.source?.name || article.source} • {new Date(article.publishedAt || article.published_at).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const EventPopup = ({ event }) => (
  <div className="w-80 p-2">
    <div className="flex items-center gap-2 mb-2">
      <span className="text-2xl">{getEventIcon(event.event_type)}</span>
      <div>
        <h3 className="font-bold text-lg text-gray-800">{event.title}</h3>
        <span className={`px-2 py-1 rounded-full text-xs font-medium text-white`}
              style={{ backgroundColor: getSeverityColor(event.severity) }}>
          {event.severity.toUpperCase()}
        </span>
      </div>
    </div>
    
    <div className="mb-3">
      <p className="text-sm text-gray-600 mb-2">📍 {event.location}</p>
      <p className="text-sm text-gray-700">{event.ai_summary}</p>
    </div>
    
    {/* News Articles */}
    <NewsArticlesList articles={event.news_articles} />
    
    <div className="text-xs text-gray-500 border-t pt-2 mt-3">
      <p>Type: {event.event_type.replace('_', ' ')}</p>
      <p>Time: {new Date(event.timestamp).toLocaleString()}</p>
      <p>Status: {event.status}</p>
    </div>
  </div>
);

export default function CrisisMap() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEventType, setSelectedEventType] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [showNewsPanel, setShowNewsPanel] = useState(false);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/events`);
      setEvents(response.data);
    } catch (err) {
      console.error('Error fetching events:', err);
      setError('Failed to load crisis events');
    } finally {
      setLoading(false);
    }
  };

  const initializeSampleData = async () => {
    try {
      await axios.post(`${API}/init-sample-data`);
      await fetchEvents();
    } catch (err) {
      console.error('Error initializing sample data:', err);
    }
  };

  const filteredEvents = events.filter(event => {
    const typeMatch = selectedEventType === 'all' || event.event_type === selectedEventType;
    const severityMatch = selectedSeverity === 'all' || event.severity === selectedSeverity;
    return typeMatch && severityMatch;
  });

  const eventTypes = [...new Set(events.map(e => e.event_type))];
  const severityLevels = ['low', 'medium', 'high', 'critical'];

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading crisis intelligence data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️ {error}</div>
          <button 
            onClick={fetchEvents}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
          <button 
            onClick={initializeSampleData}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 ml-2"
          >
            Load Sample Data
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm border-b p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Nexus Crisis Intelligence</h1>
            <p className="text-gray-600">Real-time crisis monitoring for India with live news</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <span className="font-medium">{filteredEvents.length}</span> active events
            </div>
            <button 
              onClick={() => setShowNewsPanel(!showNewsPanel)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                showNewsPanel 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📰 News
            </button>
            <button 
              onClick={fetchEvents}
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex gap-4 mt-3">
          <div>
            <label className="text-sm font-medium text-gray-600">Event Type:</label>
            <select 
              value={selectedEventType} 
              onChange={(e) => setSelectedEventType(e.target.value)}
              className="ml-2 px-2 py-1 border rounded text-sm"
            >
              <option value="all">All Types</option>
              {eventTypes.map(type => (
                <option key={type} value={type}>
                  {getEventIcon(type)} {type.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="text-sm font-medium text-gray-600">Severity:</label>
            <select 
              value={selectedSeverity} 
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="ml-2 px-2 py-1 border rounded text-sm"
            >
              <option value="all">All Levels</option>
              {severityLevels.map(level => (
                <option key={level} value={level}>
                  {level.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <MapContainer
          center={[20.5937, 78.9629]} // Center of India
          zoom={5}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {filteredEvents.map((event) => (
            <Marker
              key={event.id}
              position={[event.latitude, event.longitude]}
              icon={createEventIcon(event.event_type, event.severity)}
            >
              <Popup maxWidth={320}>
                <EventPopup event={event} />
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white p-3 rounded-lg shadow-lg z-1000">
          <h4 className="font-medium text-sm mb-2">Event Types</h4>
          <div className="space-y-1 text-xs">
            {Object.entries({
              earthquake: '🌋 Earthquake',
              flood: '🌊 Flood',
              fire: '🔥 Fire',
              storm: '🌪️ Storm',
              health_emergency: '🏥 Health Emergency',
              infrastructure_failure: '⚠️ Infrastructure',
              other: '📍 Other'
            }).map(([type, label]) => (
              <div key={type} className="flex items-center gap-2">
                <span>{label}</span>
              </div>
            ))}
          </div>
          
          <h4 className="font-medium text-sm mt-3 mb-2">Severity</h4>
          <div className="space-y-1 text-xs">
            {severityLevels.map(level => (
              <div key={level} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getSeverityColor(level) }}
                ></div>
                <span>{level.toUpperCase()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Stats Panel */}
        <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-lg z-1000">
          <h4 className="font-medium text-sm mb-2">Live Statistics</h4>
          <div className="space-y-1 text-xs">
            <div>Total Events: <span className="font-medium">{events.length}</span></div>
            <div>Critical: <span className="font-medium text-red-600">
              {events.filter(e => e.severity === 'critical').length}
            </span></div>
            <div>High: <span className="font-medium text-orange-600">
              {events.filter(e => e.severity === 'high').length}
            </span></div>
            <div>Active: <span className="font-medium text-green-600">
              {events.filter(e => e.status === 'active').length}
            </span></div>
          </div>
        </div>
      </div>

      {/* News Panel */}
      <NewsPanel 
        isOpen={showNewsPanel} 
        onClose={() => setShowNewsPanel(false)} 
      />
    </div>
  );
}