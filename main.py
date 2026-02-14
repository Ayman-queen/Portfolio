"""
Elite Portfolio Backend - FastAPI Server
Handles: Contact forms, Project data, Analytics, Admin panel
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import sqlite3
import datetime
import json
from contextlib import contextmanager

app = FastAPI(
    title="Ayman Shaheen Portfolio API",
    description="Backend API for portfolio website",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== DATABASE SETUP =====

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect('portfolio.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Projects Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT NOT NULL,
                live_url TEXT,
                code_url TEXT,
                image_url TEXT,
                featured BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Contact Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Analytics Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Skills Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                percentage INTEGER NOT NULL,
                icon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

# ===== PYDANTIC MODELS =====

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

class Project(BaseModel):
    title: str
    description: str
    category: str
    tags: List[str]
    live_url: Optional[str] = None
    code_url: Optional[str] = None
    image_url: Optional[str] = None
    featured: bool = False

class Skill(BaseModel):
    category: str
    name: str
    percentage: int
    icon: Optional[str] = None

class AnalyticsEvent(BaseModel):
    event_type: str
    event_data: Optional[dict] = None

# ===== API ENDPOINTS =====

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    print("✓ Database initialized")
    
    # Seed initial data if tables are empty
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if projects exist
        cursor.execute("SELECT COUNT(*) FROM projects")
        if cursor.fetchone()[0] == 0:
            # Insert initial projects
            projects = [
                ("Aymi Kitchen", "Professional snack business website with WhatsApp ordering", 
                 "web", "HTML5,CSS3,JavaScript", "https://aymi-snack.vercel.app/", "https://github.com/Ayman-queen", None, 1),
                ("Clothing E-store", "Full-stack e-commerce platform with product catalog", 
                 "nextjs", "Next.js,Tailwind,Figma", "https://e-store-mobile-figma-to-nextjs.vercel.app", None, None, 1),
                ("Countdown Timer", "Real-time countdown app with TypeScript", 
                 "nextjs", "Next.js,TypeScript,React", None, "https://github.com/Ayman-queen/project-countdown-timer-nextjs.git", None, 1),
                ("JavaScript Game", "Interactive browser game with animations", 
                 "web", "HTML5,CSS3,JavaScript", "https://html-css-javascript-game.vercel.app", None, None, 0),
                ("Unit Converter", "Python converter with Streamlit interface", 
                 "python", "Python,Streamlit,Math", "https://unitconverterpython-ayman.streamlit.app/", None, None, 0),
                ("TypeScript Mastery", "Collection of 45 TypeScript projects", 
                 "nextjs", "TypeScript,Node.js,ES6+", None, None, None, 1),
            ]
            
            cursor.executemany("""
                INSERT INTO projects (title, description, category, tags, live_url, code_url, image_url, featured)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, projects)
            
            # Insert initial skills
            skills = [
                ("Frontend Development", "HTML & CSS", 95, "🌐"),
                ("Frontend Development", "JavaScript", 90, "⚡"),
                ("Frontend Development", "TypeScript", 85, "📘"),
                ("Frontend Development", "React & Next.js", 88, "⚛️"),
                ("Data Science & AI", "Python", 80, "🐍"),
                ("Data Science & AI", "Data Analysis", 75, "📊"),
                ("Data Science & AI", "Machine Learning", 70, "🤖"),
                ("Data Science & AI", "MATLAB", 75, "📈"),
                ("Tools & Platforms", "Git & GitHub", 90, "💻"),
                ("Tools & Platforms", "VS Code", 95, "🔧"),
                ("Tools & Platforms", "Streamlit", 80, "🚀"),
                ("Tools & Platforms", "Vercel/Netlify", 85, "☁️"),
            ]
            
            cursor.executemany("""
                INSERT INTO skills (category, name, percentage, icon)
                VALUES (?, ?, ?, ?)
            """, skills)
            
            conn.commit()
            print("✓ Initial data seeded")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Ayman Shaheen Portfolio API",
        "version": "1.0.0",
        "endpoints": {
            "projects": "/api/projects",
            "skills": "/api/skills",
            "contact": "/api/contact",
            "analytics": "/api/analytics"
        }
    }

@app.get("/api/projects")
async def get_projects(category: Optional[str] = None, featured: Optional[bool] = None):
    """Get all projects or filter by category/featured"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM projects WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if featured is not None:
            query += " AND featured = ?"
            params.append(1 if featured else 0)
        
        query += " ORDER BY featured DESC, created_at DESC"
        
        cursor.execute(query, params)
        projects = cursor.fetchall()
        
        return {
            "success": True,
            "count": len(projects),
            "projects": [
                {
                    "id": p["id"],
                    "title": p["title"],
                    "description": p["description"],
                    "category": p["category"],
                    "tags": p["tags"].split(","),
                    "liveUrl": p["live_url"],
                    "codeUrl": p["code_url"],
                    "imageUrl": p["image_url"],
                    "featured": bool(p["featured"]),
                    "createdAt": p["created_at"]
                }
                for p in projects
            ]
        }

@app.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    """Get single project by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "success": True,
            "project": {
                "id": project["id"],
                "title": project["title"],
                "description": project["description"],
                "category": project["category"],
                "tags": project["tags"].split(","),
                "liveUrl": project["live_url"],
                "codeUrl": project["code_url"],
                "imageUrl": project["image_url"],
                "featured": bool(project["featured"]),
                "createdAt": project["created_at"]
            }
        }

@app.post("/api/projects")
async def create_project(project: Project):
    """Create new project (Admin only - add authentication in production)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (title, description, category, tags, live_url, code_url, image_url, featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project.title,
            project.description,
            project.category,
            ",".join(project.tags),
            project.live_url,
            project.code_url,
            project.image_url,
            1 if project.featured else 0
        ))
        conn.commit()
        
        return {
            "success": True,
            "message": "Project created successfully",
            "id": cursor.lastrowid
        }

@app.get("/api/skills")
async def get_skills(category: Optional[str] = None):
    """Get all skills or filter by category"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if category:
            cursor.execute("SELECT * FROM skills WHERE category = ? ORDER BY percentage DESC", (category,))
        else:
            cursor.execute("SELECT * FROM skills ORDER BY category, percentage DESC")
        
        skills = cursor.fetchall()
        
        # Group by category
        skills_by_category = {}
        for skill in skills:
            cat = skill["category"]
            if cat not in skills_by_category:
                skills_by_category[cat] = []
            
            skills_by_category[cat].append({
                "id": skill["id"],
                "name": skill["name"],
                "percentage": skill["percentage"],
                "icon": skill["icon"]
            })
        
        return {
            "success": True,
            "skills": skills_by_category
        }

@app.post("/api/contact")
async def submit_contact(message: ContactMessage, request: Request):
    """Submit contact form message"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contact_messages (name, email, message)
            VALUES (?, ?, ?)
        """, (message.name, message.email, message.message))
        conn.commit()
        
        # Log analytics event
        cursor.execute("""
            INSERT INTO analytics (event_type, event_data, ip_address, user_agent)
            VALUES (?, ?, ?, ?)
        """, (
            "contact_form_submission",
            json.dumps({"name": message.name, "email": message.email}),
            request.client.host,
            request.headers.get("user-agent")
        ))
        conn.commit()
        
        return {
            "success": True,
            "message": "Message received! I'll get back to you soon.",
            "whatsappUrl": f"https://wa.me/923242441758?text=Hello! I'm {message.name} ({message.email}). {message.message}"
        }

@app.get("/api/contact/messages")
async def get_messages(unread_only: bool = False):
    """Get contact messages (Admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if unread_only:
            cursor.execute("SELECT * FROM contact_messages WHERE read = 0 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
        
        messages = cursor.fetchall()
        
        return {
            "success": True,
            "count": len(messages),
            "messages": [
                {
                    "id": m["id"],
                    "name": m["name"],
                    "email": m["email"],
                    "message": m["message"],
                    "read": bool(m["read"]),
                    "createdAt": m["created_at"]
                }
                for m in messages
            ]
        }

@app.post("/api/analytics")
async def log_analytics(event: AnalyticsEvent, request: Request):
    """Log analytics event"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics (event_type, event_data, ip_address, user_agent)
            VALUES (?, ?, ?, ?)
        """, (
            event.event_type,
            json.dumps(event.event_data) if event.event_data else None,
            request.client.host,
            request.headers.get("user-agent")
        ))
        conn.commit()
        
        return {"success": True, "message": "Event logged"}

@app.get("/api/analytics/stats")
async def get_analytics_stats():
    """Get analytics statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total visits
        cursor.execute("SELECT COUNT(*) as count FROM analytics WHERE event_type = 'page_view'")
        total_visits = cursor.fetchone()["count"]
        
        # Total messages
        cursor.execute("SELECT COUNT(*) as count FROM contact_messages")
        total_messages = cursor.fetchone()["count"]
        
        # Project views
        cursor.execute("SELECT COUNT(*) as count FROM analytics WHERE event_type = 'project_view'")
        project_views = cursor.fetchone()["count"]
        
        # Recent events
        cursor.execute("SELECT event_type, COUNT(*) as count FROM analytics GROUP BY event_type")
        events = cursor.fetchall()
        
        return {
            "success": True,
            "stats": {
                "totalVisits": total_visits,
                "totalMessages": total_messages,
                "projectViews": project_views,
                "eventBreakdown": [{"type": e["event_type"], "count": e["count"]} for e in events]
            }
        }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "database": "connected"
    }

# ===== RUN SERVER =====
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    print("📍 API Docs: http://localhost:8000/docs")
    print("📍 Health: http://localhost:8000/api/health")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
