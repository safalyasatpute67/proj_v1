from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import openai
from openai import OpenAI
import json
import requests
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# NewsAPI configuration
NEWSAPI_KEY = os.environ['NEWSAPI_KEY']
NEWSAPI_BASE_URL = "https://newsapi.org/v2"

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class CrisisEventCreate(BaseModel):
    title: str
    description: str
    location: str
    latitude: float
    longitude: float
    event_type: Optional[str] = None
    severity: Optional[str] = None

class CrisisEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    location: str
    latitude: float
    longitude: float
    event_type: str
    severity: str
    ai_summary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"
    news_articles: Optional[List[Dict]] = []

class EventAnalysisRequest(BaseModel):
    text: str
    location: Optional[str] = None

class EventAnalysisResponse(BaseModel):
    event_type: str
    severity: str
    summary: str
    recommendations: List[str]

class NewsArticle(BaseModel):
    title: str
    description: str
    url: str
    source: str
    published_at: str
    url_to_image: Optional[str] = None

class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    total_results: int
    query: str

# NewsAPI integration functions
async def fetch_crisis_news(query: str, days_back: int = 7, page_size: int = 10) -> Dict[str, Any]:
    """Fetch crisis-related news from NewsAPI"""
    try:
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        params = {
            'q': query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'pageSize': page_size,
            'apiKey': NEWSAPI_KEY
        }
        
        response = requests.get(f"{NEWSAPI_BASE_URL}/everything", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'articles': data.get('articles', []),
                'total_results': data.get('totalResults', 0),
                'query': query
            }
        else:
            logger.error(f"NewsAPI error: {response.status_code} - {response.text}")
            return {
                'status': 'error',
                'articles': [],
                'total_results': 0,
                'query': query,
                'error': f"API returned {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        return {
            'status': 'error',
            'articles': [],
            'total_results': 0,
            'query': query,
            'error': str(e)
        }

async def get_relevant_news_for_event(event_type: str, location: str) -> List[Dict]:
    """Get relevant news articles for a specific crisis event"""
    # Map event types to search queries
    event_queries = {
        'earthquake': f'earthquake {location} india',
        'flood': f'flood {location} india',
        'fire': f'fire {location} india',
        'storm': f'storm cyclone {location} india',
        'health_emergency': f'health emergency {location} india',
        'infrastructure_failure': f'infrastructure failure {location} india',
        'other': f'crisis emergency {location} india'
    }
    
    query = event_queries.get(event_type, f'{event_type} {location} india')
    news_data = await fetch_crisis_news(query, days_back=3, page_size=5)
    
    return news_data.get('articles', [])[:3]  # Return top 3 articles

# AI-powered event analysis (enhanced with news context)
async def analyze_crisis_event(title: str, description: str, location: str = "") -> Dict[str, Any]:
    """Analyze crisis event using OpenAI"""
    try:
        prompt = f"""
        Analyze this crisis event and provide structured information:
        
        Title: {title}
        Description: {description}
        Location: {location}
        
        Please analyze and return:
        1. Event Type (earthquake, flood, fire, storm, health_emergency, infrastructure_failure, other)
        2. Severity Level (low, medium, high, critical)
        3. Brief Summary (max 150 words)
        4. Safety Recommendations (list of 3-5 actionable items)
        
        Respond in JSON format with keys: event_type, severity, summary, recommendations
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a crisis management expert. Analyze events and provide structured, actionable information for public safety."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        # Fallback analysis
        return {
            "event_type": "other",
            "severity": "medium",
            "summary": f"Crisis event reported in {location}: {title}. {description[:100]}...",
            "recommendations": [
                "Stay informed through official channels",
                "Follow local authorities' instructions",
                "Keep emergency supplies ready",
                "Stay connected with family and community"
            ]
        }

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Nexus Crisis Intelligence API with Real-time News Integration"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Crisis Intelligence Routes
@api_router.post("/events", response_model=CrisisEvent)
async def create_crisis_event(event_data: CrisisEventCreate):
    """Create a new crisis event with AI analysis and news context"""
    try:
        # Get AI analysis
        analysis = await analyze_crisis_event(
            event_data.title, 
            event_data.description, 
            event_data.location
        )
        
        # Get relevant news articles
        news_articles = await get_relevant_news_for_event(
            analysis['event_type'], 
            event_data.location
        )
        
        # Create event object
        event_dict = event_data.dict()
        event_dict['event_type'] = analysis['event_type']
        event_dict['severity'] = analysis['severity']
        event_dict['ai_summary'] = analysis['summary']
        event_dict['news_articles'] = news_articles
        
        event_obj = CrisisEvent(**event_dict)
        
        # Store in database
        await db.crisis_events.insert_one(event_obj.dict())
        
        return event_obj
        
    except Exception as e:
        logger.error(f"Error creating crisis event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create crisis event")

@api_router.get("/events", response_model=List[CrisisEvent])
async def get_crisis_events():
    """Get all crisis events"""
    try:
        events = await db.crisis_events.find().sort("timestamp", -1).to_list(100)
        return [CrisisEvent(**event) for event in events]
    except Exception as e:
        logger.error(f"Error fetching events: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch events")

@api_router.get("/events/{event_id}", response_model=CrisisEvent)
async def get_crisis_event(event_id: str):
    """Get specific crisis event"""
    try:
        event = await db.crisis_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return CrisisEvent(**event)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch event")

@api_router.post("/analyze", response_model=EventAnalysisResponse)
async def analyze_event_text(request: EventAnalysisRequest):
    """Analyze event text using AI"""
    try:
        analysis = await analyze_crisis_event("", request.text, request.location or "")
        return EventAnalysisResponse(
            event_type=analysis['event_type'],
            severity=analysis['severity'],
            summary=analysis['summary'],
            recommendations=analysis['recommendations']
        )
    except Exception as e:
        logger.error(f"Error analyzing event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze event")

@api_router.get("/events/location/{latitude}/{longitude}")
async def get_events_near_location(latitude: float, longitude: float, radius: float = 50.0):
    """Get events near a specific location (simplified distance calculation)"""
    try:
        # Simple bounding box calculation (for demo - in production use proper geospatial queries)
        lat_range = radius / 111.0  # Rough conversion: 1 degree ≈ 111 km
        lon_range = radius / (111.0 * abs(latitude) / 90.0) if latitude != 0 else radius / 111.0
        
        events = await db.crisis_events.find({
            "latitude": {"$gte": latitude - lat_range, "$lte": latitude + lat_range},
            "longitude": {"$gte": longitude - lon_range, "$lte": longitude + lon_range}
        }).to_list(50)
        
        return [CrisisEvent(**event) for event in events]
    except Exception as e:
        logger.error(f"Error fetching location events: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch location events")

# News API Routes
@api_router.get("/news/crisis", response_model=NewsResponse)
async def get_crisis_news(
    query: str = Query(default="disaster emergency india", description="Search query for crisis news"),
    days: int = Query(default=7, description="Number of days to search back"),
    limit: int = Query(default=20, description="Number of articles to return")
):
    """Get crisis-related news from NewsAPI"""
    try:
        news_data = await fetch_crisis_news(query, days_back=days, page_size=limit)
        
        if news_data['status'] == 'success':
            articles = [
                NewsArticle(
                    title=article.get('title', ''),
                    description=article.get('description', ''),
                    url=article.get('url', ''),
                    source=article.get('source', {}).get('name', 'Unknown'),
                    published_at=article.get('publishedAt', ''),
                    url_to_image=article.get('urlToImage')
                )
                for article in news_data['articles']
                if article.get('title') and article.get('url')
            ]
            
            return NewsResponse(
                articles=articles,
                total_results=news_data['total_results'],
                query=query
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to fetch news: {news_data.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching crisis news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch crisis news")

@api_router.get("/news/trending")
async def get_trending_crisis_topics():
    """Get trending crisis-related topics from multiple news queries"""
    try:
        crisis_queries = [
            "earthquake india",
            "flood india", 
            "cyclone india",
            "fire india",
            "emergency india"
        ]
        
        trending_topics = []
        
        for query in crisis_queries:
            news_data = await fetch_crisis_news(query, days_back=2, page_size=5)
            if news_data['status'] == 'success' and news_data['total_results'] > 0:
                trending_topics.append({
                    'topic': query,
                    'article_count': news_data['total_results'],
                    'latest_articles': news_data['articles'][:2]
                })
        
        return {
            'trending_topics': trending_topics,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching trending topics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending topics")

# Initialize with sample data (enhanced with news)
@api_router.post("/init-sample-data")
async def initialize_sample_data():
    """Initialize with sample crisis events for India with news context"""
    try:
        # Check if data already exists
        existing_count = await db.crisis_events.count_documents({})
        if existing_count > 0:
            return {"message": f"Sample data already exists ({existing_count} events)"}
        
        sample_events = [
            CrisisEventCreate(
                title="Earthquake Alert in Delhi NCR",
                description="A moderate earthquake of magnitude 4.2 was felt in Delhi NCR region. Buildings swayed for about 10 seconds. No major damage reported yet, but authorities are assessing the situation.",
                location="Delhi, India",
                latitude=28.6139,
                longitude=77.2090
            ),
            CrisisEventCreate(
                title="Heavy Rainfall Warning - Mumbai",
                description="IMD has issued a red alert for Mumbai with predictions of extremely heavy rainfall. Waterlogging expected in low-lying areas. Citizens advised to stay indoors unless emergency.",
                location="Mumbai, Maharashtra",
                latitude=19.0760,
                longitude=72.8777
            ),
            CrisisEventCreate(
                title="Forest Fire in Western Ghats",
                description="A large forest fire has been reported in the Western Ghats near Pune. Fire department and forest officials are working to contain the blaze. Nearby villages have been alerted.",
                location="Western Ghats, Maharashtra",
                latitude=18.5204,
                longitude=73.8567
            ),
            CrisisEventCreate(
                title="Cyclone Alert - Odisha Coast",
                description="A cyclonic storm is approaching the Odisha coast. Wind speeds expected to reach 80-90 km/h. Evacuation of coastal areas has begun. Fishermen advised not to venture into the sea.",
                location="Bhubaneswar, Odisha",
                latitude=20.2961,
                longitude=85.8245
            ),
            CrisisEventCreate(
                title="Industrial Accident - Ahmedabad",
                description="A chemical leak has been reported at an industrial facility in Ahmedabad. Emergency teams are on site. Area within 2km radius has been evacuated as a precautionary measure.",
                location="Ahmedabad, Gujarat",
                latitude=23.0225,
                longitude=72.5714
            )
        ]
        
        # Create events with AI analysis and news context
        created_events = []
        for event_data in sample_events:
            analysis = await analyze_crisis_event(
                event_data.title,
                event_data.description,
                event_data.location
            )
            
            # Get relevant news articles
            news_articles = await get_relevant_news_for_event(
                analysis['event_type'],
                event_data.location
            )
            
            event_dict = event_data.dict()
            event_dict['event_type'] = analysis['event_type']
            event_dict['severity'] = analysis['severity']
            event_dict['ai_summary'] = analysis['summary']
            event_dict['news_articles'] = news_articles
            
            event_obj = CrisisEvent(**event_dict)
            await db.crisis_events.insert_one(event_obj.dict())
            created_events.append(event_obj)
        
        return {"message": f"Created {len(created_events)} sample events with news context", "events": created_events}
        
    except Exception as e:
        logger.error(f"Error initializing sample data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize sample data")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()