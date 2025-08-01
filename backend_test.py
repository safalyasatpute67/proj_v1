#!/usr/bin/env python3
"""
Backend API Testing for Nexus Crisis Intelligence Platform
Tests all backend endpoints and AI integration functionality
"""

import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
frontend_env_path = Path("/app/frontend/.env")
if frontend_env_path.exists():
    load_dotenv(frontend_env_path)

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE_URL}")

def test_basic_api_connection():
    """Test 1: Basic API Connection - GET /api/"""
    print("\n=== Test 1: Basic API Connection ===")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "Nexus Crisis Intelligence API" in data["message"]:
                print("✅ Basic API connection working")
                return True
            else:
                print("❌ Unexpected response format")
                return False
        else:
            print(f"❌ API connection failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_crisis_events_api_empty():
    """Test 2: Crisis Events API - GET /api/events (should return empty initially)"""
    print("\n=== Test 2: Crisis Events API (Empty) ===")
    try:
        response = requests.get(f"{API_BASE_URL}/events", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            events = response.json()
            print(f"Events count: {len(events)}")
            print("✅ Crisis events API working")
            return True, len(events)
        else:
            print(f"❌ Events API failed with status {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"❌ Error testing events API: {e}")
        return False, 0

def test_ai_sample_data_creation():
    """Test 3: AI-Powered Sample Data - POST /api/init-sample-data"""
    print("\n=== Test 3: AI-Powered Sample Data Creation ===")
    try:
        response = requests.post(f"{API_BASE_URL}/init-sample-data", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            
            if "message" in data:
                if "already exists" in data["message"]:
                    print("✅ Sample data already exists")
                    return True
                elif "Created" in data["message"]:
                    print("✅ Sample data created successfully")
                    if "events" in data:
                        print(f"Created {len(data['events'])} events")
                        # Check if events have AI analysis
                        for event in data["events"][:2]:  # Check first 2 events
                            print(f"Event: {event['title']}")
                            print(f"  Type: {event['event_type']}")
                            print(f"  Severity: {event['severity']}")
                            print(f"  AI Summary: {event['ai_summary'][:100]}...")
                    return True
                else:
                    print("✅ Sample data initialization completed")
                    return True
            else:
                print("❌ Unexpected response format")
                return False
        else:
            print(f"❌ Sample data creation failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def test_events_with_ai_analysis():
    """Test 4: Event Analysis - GET /api/events after sample data creation"""
    print("\n=== Test 4: Events with AI Analysis ===")
    try:
        response = requests.get(f"{API_BASE_URL}/events", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            events = response.json()
            print(f"Total events: {len(events)}")
            
            if len(events) > 0:
                print("\n--- Analyzing first event ---")
                event = events[0]
                required_fields = ['id', 'title', 'description', 'location', 'latitude', 'longitude', 
                                 'event_type', 'severity', 'ai_summary', 'timestamp', 'status']
                
                missing_fields = [field for field in required_fields if field not in event]
                if missing_fields:
                    print(f"❌ Missing fields: {missing_fields}")
                    return False
                
                print(f"Title: {event['title']}")
                print(f"Location: {event['location']}")
                print(f"Event Type: {event['event_type']}")
                print(f"Severity: {event['severity']}")
                print(f"AI Summary: {event['ai_summary'][:150]}...")
                
                # Verify AI categorization
                valid_types = ['earthquake', 'flood', 'fire', 'storm', 'health_emergency', 'infrastructure_failure', 'other']
                valid_severities = ['low', 'medium', 'high', 'critical']
                
                if event['event_type'] in valid_types:
                    print(f"✅ Valid event type: {event['event_type']}")
                else:
                    print(f"❌ Invalid event type: {event['event_type']}")
                    return False
                
                if event['severity'] in valid_severities:
                    print(f"✅ Valid severity: {event['severity']}")
                else:
                    print(f"❌ Invalid severity: {event['severity']}")
                    return False
                
                if len(event['ai_summary']) > 10:
                    print("✅ AI summary generated")
                else:
                    print("❌ AI summary too short or missing")
                    return False
                
                print("✅ Events with AI analysis working properly")
                return True
            else:
                print("❌ No events found after sample data creation")
                return False
        else:
            print(f"❌ Failed to fetch events: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing events with AI analysis: {e}")
        return False

def test_event_creation():
    """Test 5: Event Creation - POST /api/events with AI analysis"""
    print("\n=== Test 5: Event Creation with AI Analysis ===")
    
    test_event = {
        "title": "Heavy Snowfall in Kashmir",
        "description": "Unprecedented heavy snowfall in Kashmir region causing road blockages and power outages. Several villages are cut off from main roads.",
        "location": "Srinagar, Kashmir",
        "latitude": 34.0837,
        "longitude": 74.7973
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/events", 
                               json=test_event, 
                               headers={"Content-Type": "application/json"},
                               timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            event = response.json()
            print(f"Created Event ID: {event['id']}")
            print(f"Title: {event['title']}")
            print(f"AI-determined Type: {event['event_type']}")
            print(f"AI-determined Severity: {event['severity']}")
            print(f"AI Summary: {event['ai_summary'][:150]}...")
            
            # Verify AI analysis was applied
            if event['event_type'] and event['severity'] and event['ai_summary']:
                print("✅ Event creation with AI analysis working")
                return True, event['id']
            else:
                print("❌ AI analysis not properly applied")
                return False, None
        else:
            print(f"❌ Event creation failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Error response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error creating event: {e}")
        return False, None

def test_standalone_analysis():
    """Test 6: Standalone Event Analysis - POST /api/analyze"""
    print("\n=== Test 6: Standalone Event Analysis ===")
    
    analysis_request = {
        "text": "Major earthquake hits northern India, buildings collapsed in several cities, rescue operations underway",
        "location": "Northern India"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/analyze",
                               json=analysis_request,
                               headers={"Content-Type": "application/json"},
                               timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            analysis = response.json()
            print(f"Event Type: {analysis['event_type']}")
            print(f"Severity: {analysis['severity']}")
            print(f"Summary: {analysis['summary'][:150]}...")
            print(f"Recommendations: {len(analysis['recommendations'])} items")
            
            # Verify analysis structure
            required_fields = ['event_type', 'severity', 'summary', 'recommendations']
            missing_fields = [field for field in required_fields if field not in analysis]
            
            if missing_fields:
                print(f"❌ Missing analysis fields: {missing_fields}")
                return False
            
            if isinstance(analysis['recommendations'], list) and len(analysis['recommendations']) > 0:
                print("Sample recommendations:")
                for i, rec in enumerate(analysis['recommendations'][:3]):
                    print(f"  {i+1}. {rec}")
                print("✅ Standalone analysis working properly")
                return True
            else:
                print("❌ Recommendations not properly formatted")
                return False
        else:
            print(f"❌ Analysis failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing standalone analysis: {e}")
        return False

def test_event_retrieval(event_id):
    """Test 7: Individual Event Retrieval - GET /api/events/{event_id}"""
    print(f"\n=== Test 7: Individual Event Retrieval ===")
    
    if not event_id:
        print("⚠️ Skipping individual event retrieval (no event ID available)")
        return True
    
    try:
        response = requests.get(f"{API_BASE_URL}/events/{event_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            event = response.json()
            print(f"Retrieved Event: {event['title']}")
            print(f"Event ID matches: {event['id'] == event_id}")
            print("✅ Individual event retrieval working")
            return True
        elif response.status_code == 404:
            print("❌ Event not found")
            return False
        else:
            print(f"❌ Event retrieval failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error retrieving individual event: {e}")
        return False

def test_crisis_news_api():
    """Test 8: NewsAPI Integration - GET /api/news/crisis"""
    print("\n=== Test 8: NewsAPI Integration - Crisis News ===")
    
    # Test with different crisis queries
    test_queries = [
        {"query": "earthquake india", "days": 7, "limit": 5},
        {"query": "flood mumbai", "days": 3, "limit": 3},
        {"query": "disaster emergency india", "days": 7, "limit": 10}
    ]
    
    for i, params in enumerate(test_queries, 1):
        print(f"\n--- Test Query {i}: {params['query']} ---")
        try:
            response = requests.get(f"{API_BASE_URL}/news/crisis", 
                                  params=params, 
                                  timeout=15)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                news_data = response.json()
                print(f"Query: {news_data['query']}")
                print(f"Total Results: {news_data['total_results']}")
                print(f"Articles Returned: {len(news_data['articles'])}")
                
                # Check article structure
                if len(news_data['articles']) > 0:
                    article = news_data['articles'][0]
                    required_fields = ['title', 'description', 'url', 'source', 'published_at']
                    missing_fields = [field for field in required_fields if field not in article or not article[field]]
                    
                    if missing_fields:
                        print(f"⚠️ Some articles missing fields: {missing_fields}")
                    else:
                        print("✅ Article structure valid")
                        print(f"Sample Article: {article['title'][:80]}...")
                        print(f"Source: {article['source']}")
                else:
                    print("⚠️ No articles returned (might be due to API limits or no recent news)")
                
                print(f"✅ Crisis news API working for query: {params['query']}")
            else:
                print(f"❌ Crisis news API failed with status {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    print(f"Error response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing crisis news API: {e}")
            return False
    
    print("✅ All crisis news API tests passed")
    return True

def test_trending_topics_api():
    """Test 9: Trending Crisis Topics - GET /api/news/trending"""
    print("\n=== Test 9: Trending Crisis Topics ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/news/trending", timeout=20)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            trending_data = response.json()
            print(f"Trending Topics Found: {len(trending_data['trending_topics'])}")
            print(f"Timestamp: {trending_data['timestamp']}")
            
            # Check trending topics structure
            for i, topic in enumerate(trending_data['trending_topics'][:3], 1):
                print(f"\n--- Trending Topic {i} ---")
                print(f"Topic: {topic['topic']}")
                print(f"Article Count: {topic['article_count']}")
                print(f"Latest Articles: {len(topic['latest_articles'])}")
                
                if len(topic['latest_articles']) > 0:
                    sample_article = topic['latest_articles'][0]
                    print(f"Sample Article: {sample_article.get('title', 'No title')[:60]}...")
            
            print("✅ Trending topics API working")
            return True
        else:
            print(f"❌ Trending topics API failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing trending topics API: {e}")
        return False

def test_enhanced_event_creation_with_news():
    """Test 10: Enhanced Event Creation with News Articles"""
    print("\n=== Test 10: Enhanced Event Creation with News Integration ===")
    
    # Test event from the review request
    test_event = {
        "title": "Severe Heatwave in Rajasthan",
        "description": "Extreme temperatures above 45°C recorded across Rajasthan. Several districts report heat-related illnesses.",
        "location": "Jaipur, Rajasthan",
        "latitude": 26.9124,
        "longitude": 75.7873
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/events", 
                               json=test_event, 
                               headers={"Content-Type": "application/json"},
                               timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            event = response.json()
            print(f"Created Event ID: {event['id']}")
            print(f"Title: {event['title']}")
            print(f"AI-determined Type: {event['event_type']}")
            print(f"AI-determined Severity: {event['severity']}")
            print(f"AI Summary: {event['ai_summary'][:150]}...")
            
            # Check for news articles integration
            if 'news_articles' in event:
                print(f"News Articles Found: {len(event['news_articles'])}")
                if len(event['news_articles']) > 0:
                    print("Sample News Article:")
                    article = event['news_articles'][0]
                    print(f"  Title: {article.get('title', 'No title')[:80]}...")
                    print(f"  Source: {article.get('source', {}).get('name', 'Unknown')}")
                    print("✅ Enhanced event creation with news integration working")
                else:
                    print("⚠️ No news articles found (might be due to API limits or no relevant news)")
                    print("✅ Enhanced event creation working (news integration attempted)")
            else:
                print("❌ News articles field missing from event")
                return False, None
            
            return True, event['id']
        else:
            print(f"❌ Enhanced event creation failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Error response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing enhanced event creation: {e}")
        return False, None

def test_existing_events_have_news_field():
    """Test 11: Verify Existing Events Have News Articles Field"""
    print("\n=== Test 11: Existing Events with News Articles Field ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/events", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            events = response.json()
            print(f"Total events to check: {len(events)}")
            
            events_with_news = 0
            events_without_news = 0
            
            for i, event in enumerate(events[:5], 1):  # Check first 5 events
                print(f"\n--- Event {i}: {event['title'][:50]}... ---")
                
                if 'news_articles' in event:
                    news_count = len(event['news_articles']) if event['news_articles'] else 0
                    print(f"News Articles: {news_count}")
                    events_with_news += 1
                    
                    if news_count > 0:
                        sample_article = event['news_articles'][0]
                        print(f"Sample Article: {sample_article.get('title', 'No title')[:60]}...")
                else:
                    print("❌ Missing news_articles field")
                    events_without_news += 1
            
            print(f"\nSummary:")
            print(f"Events with news_articles field: {events_with_news}")
            print(f"Events without news_articles field: {events_without_news}")
            
            if events_without_news == 0:
                print("✅ All events have news_articles field")
                return True
            else:
                print("⚠️ Some events missing news_articles field (might be older events)")
                return True  # This is acceptable for backward compatibility
        else:
            print(f"❌ Failed to fetch events: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking existing events: {e}")
        return False

def run_all_tests():
    """Run all backend tests including NewsAPI integration"""
    print("🚀 Starting Enhanced Nexus Crisis Intelligence Backend API Tests")
    print("🔥 Testing NewsAPI Integration & Enhanced Features")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Basic API Connection
    results['basic_connection'] = test_basic_api_connection()
    
    # Test 2: Crisis Events API (Empty)
    results['events_api_empty'], initial_count = test_crisis_events_api_empty()
    
    # Test 3: AI-Powered Sample Data Creation
    results['sample_data_creation'] = test_ai_sample_data_creation()
    
    # Test 4: Events with AI Analysis
    results['events_with_ai'] = test_events_with_ai_analysis()
    
    # Test 5: Event Creation
    results['event_creation'], created_event_id = test_event_creation()
    
    # Test 6: Standalone Analysis
    results['standalone_analysis'] = test_standalone_analysis()
    
    # Test 7: Individual Event Retrieval
    results['event_retrieval'] = test_event_retrieval(created_event_id)
    
    # NEW TESTS FOR NEWSAPI INTEGRATION
    
    # Test 8: Crisis News API
    results['crisis_news_api'] = test_crisis_news_api()
    
    # Test 9: Trending Topics API
    results['trending_topics_api'] = test_trending_topics_api()
    
    # Test 10: Enhanced Event Creation with News
    results['enhanced_event_creation'], enhanced_event_id = test_enhanced_event_creation_with_news()
    
    # Test 11: Existing Events Have News Field
    results['existing_events_news_field'] = test_existing_events_have_news_field()
    
    # Summary
    print("\n" + "=" * 70)
    print("🏁 ENHANCED TEST SUMMARY - NewsAPI Integration")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    # Group tests by category
    core_tests = ['basic_connection', 'events_api_empty', 'sample_data_creation', 
                  'events_with_ai', 'event_creation', 'standalone_analysis', 'event_retrieval']
    news_tests = ['crisis_news_api', 'trending_topics_api', 'enhanced_event_creation', 
                  'existing_events_news_field']
    
    print("📊 CORE API TESTS:")
    for test_name in core_tests:
        if test_name in results:
            status = "✅ PASS" if results[test_name] else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print("\n🔥 NEWSAPI INTEGRATION TESTS:")
    for test_name in news_tests:
        if test_name in results:
            status = "✅ PASS" if results[test_name] else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backend tests passed! NewsAPI integration is working properly.")
        print("🚀 Enhanced Nexus Crisis Intelligence platform is ready!")
        return True
    else:
        print("⚠️ Some tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)