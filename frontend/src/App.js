import { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import CrisisMap from "./components/CrisisMap";
import Dashboard from "./components/Dashboard";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Navigation = () => {
  const location = useLocation();
  
  const navItems = [
    { path: "/", label: "🗺️ Crisis Map", icon: "🗺️" },
    { path: "/dashboard", label: "📊 Dashboard", icon: "📊" },
  ];

  return (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <img 
                src="https://avatars.githubusercontent.com/in/1201222?s=120&u=2686cf91179bbafbc7a71bfbc43004cf9ae1acea&v=4" 
                alt="Nexus Logo" 
                className="h-8 w-8 rounded"
              />
              <div>
                <h1 className="text-xl font-bold text-gray-800">Nexus Crisis Intelligence</h1>
                <p className="text-xs text-gray-600">Community-centric digital ecosystem for India</p>
              </div>
            </Link>
          </div>
          
          <div className="flex items-center space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === item.path
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

const Home = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  const testConnection = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log('Backend response:', response.data.message);
      setIsConnected(true);
    } catch (e) {
      console.error('Backend connection failed:', e);
      setIsConnected(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <div className="flex-1">
        <CrisisMap />
      </div>
      
      {/* Connection Status (for debugging) */}
      <div className="fixed bottom-4 right-4 z-1000">
        <div className={`px-3 py-2 rounded-lg text-sm font-medium ${
          loading ? 'bg-yellow-100 text-yellow-800' :
          isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {loading ? '🔄 Connecting...' : 
           isConnected ? '✅ Backend Connected' : '❌ Backend Disconnected'}
        </div>
      </div>
    </div>
  );
};

const DashboardPage = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <Dashboard />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;