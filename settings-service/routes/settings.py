"""Configuration settings endpoints"""
from fastapi import APIRouter
import sqlite3
import json
from datetime import datetime
from models import TreeSettings, QuerySettings, ModelConfig, UIPreferences

router = APIRouter(prefix="/settings", tags=["settings"])


# Tree Settings Management
@router.get("/tree")
async def get_tree_settings():
    """Get tree generation settings"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    result = cursor.execute(
        "SELECT settings FROM configurations WHERE category = 'tree'"
    ).fetchone()
    conn.close()

    if result:
        return json.loads(result[0])

    # Return defaults
    return TreeSettings().dict()


@router.post("/tree")
async def update_tree_settings(settings: TreeSettings):
    """Update tree generation settings"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO configurations (category, settings, updated_at)
        VALUES (?, ?, ?)
    ''', ('tree', json.dumps(settings.dict()), datetime.now()))
    conn.commit()
    conn.close()

    return {"success": True, "settings": settings.dict()}


# Query Settings Management
@router.get("/query")
async def get_query_settings():
    """Get query settings"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    result = cursor.execute(
        "SELECT settings FROM configurations WHERE category = 'query'"
    ).fetchone()
    conn.close()

    if result:
        return json.loads(result[0])

    return QuerySettings().dict()


@router.post("/query")
async def update_query_settings(settings: QuerySettings):
    """Update query settings"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO configurations (category, settings, updated_at)
        VALUES (?, ?, ?)
    ''', ('query', json.dumps(settings.dict()), datetime.now()))
    conn.commit()
    conn.close()

    return {"success": True, "settings": settings.dict()}


# Model Configuration
@router.get("/model")
async def get_model_config():
    """Get model configuration"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    result = cursor.execute(
        "SELECT settings FROM configurations WHERE category = 'model'"
    ).fetchone()
    conn.close()

    if result:
        return json.loads(result[0])

    return ModelConfig().dict()


@router.post("/model")
async def update_model_config(config: ModelConfig):
    """Update model configuration"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO configurations (category, settings, updated_at)
        VALUES (?, ?, ?)
    ''', ('model', json.dumps(config.dict()), datetime.now()))
    conn.commit()
    conn.close()

    return {"success": True, "config": config.dict()}


# UI Preferences
@router.get("/ui")
async def get_ui_preferences():
    """Get UI preferences"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    result = cursor.execute(
        "SELECT settings FROM configurations WHERE category = 'ui'"
    ).fetchone()
    conn.close()

    if result:
        return json.loads(result[0])

    return UIPreferences().dict()


@router.post("/ui")
async def update_ui_preferences(prefs: UIPreferences):
    """Update UI preferences"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO configurations (category, settings, updated_at)
        VALUES (?, ?, ?)
    ''', ('ui', json.dumps(prefs.dict()), datetime.now()))
    conn.commit()
    conn.close()

    return {"success": True, "preferences": prefs.dict()}
