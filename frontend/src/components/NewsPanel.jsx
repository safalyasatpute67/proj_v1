import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NewsArticleCard = ({ article }) => (
  <div className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow">
    <div className="flex gap-3">
      {article.url_to_image && (
        <img 
          src={article.url_to_image} 
          alt={article.title}
          className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      )}
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-sm text-gray-900 line-clamp-2 mb-1">
          {article.title}
        </h4>
        <p className="text-xs text-gray-600 line-clamp-2 mb-2">
          {article.description}
        </p>
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span className="font-medium">{article.source}</span>
          <span>{new Date(article.published_at).toLocaleDateString()}</span>
        </div>
        <a 
          href={article.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-block mt-2 text-xs text-blue-600 hover:text-blue-800"
        >
          Read Full Article →
        </a>
      </div>
    </div>
  </div>
);

const NewsPanel = ({ isOpen, onClose }) => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState('disaster emergency india');
  const [trendingTopics, setTrendingTopics] = useState([]);

  const newsQueries = [
    'disaster emergency india',
    'earthquake india',
    'flood india',
    'cyclone storm india',
    'fire accident india',
    'health emergency india'
  ];

  useEffect(() => {
    if (isOpen) {
      fetchNews();
      fetchTrendingTopics();
    }
  }, [isOpen, selectedQuery]);

  const fetchNews = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/news/crisis`, {
        params: {
          query: selectedQuery,
          days: 7,
          limit: 15
        }
      });
      setNews(response.data.articles);
    } catch (error) {
      console.error('Error fetching news:', error);
      setNews([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrendingTopics = async () => {
    try {
      const response = await axios.get(`${API}/news/trending`);
      setTrendingTopics(response.data.trending_topics);
    } catch (error) {
      console.error('Error fetching trending topics:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-gray-50 shadow-xl z-50 transform transition-transform">
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-800">📰 Crisis News</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ✕
            </button>
          </div>
          
          {/* Query Selector */}
          <select
            value={selectedQuery}
            onChange={(e) => setSelectedQuery(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {newsQueries.map(query => (
              <option key={query} value={query}>
                {query.charAt(0).toUpperCase() + query.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Trending Topics */}
        {trendingTopics.length > 0 && (
          <div className="bg-white border-b p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">🔥 Trending</h4>
            <div className="flex flex-wrap gap-2">
              {trendingTopics.slice(0, 3).map((topic, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedQuery(topic.topic)}
                  className={`px-2 py-1 rounded-full text-xs font-medium transition-colors ${
                    selectedQuery === topic.topic
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {topic.topic} ({topic.article_count})
                </button>
              ))}
            </div>
          </div>
        )}

        {/* News Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">Loading news...</span>
            </div>
          ) : news.length > 0 ? (
            <div className="space-y-3">
              <div className="text-sm text-gray-600 mb-3">
                Found {news.length} recent articles
              </div>
              {news.map((article, index) => (
                <NewsArticleCard key={index} article={article} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-500 mb-2">📰</div>
              <p className="text-gray-600 text-sm">No recent news found for this topic.</p>
              <button
                onClick={fetchNews}
                className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
              >
                Try Again
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-white border-t p-3 text-center">
          <p className="text-xs text-gray-500">
            Powered by NewsAPI • Real-time crisis news
          </p>
        </div>
      </div>
    </div>
  );
};

export default NewsPanel;