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

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting Nexus Crisis Intelligence Backend API Tests")
    print("=" * 60)
    
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
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backend tests passed! AI integration is working properly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)