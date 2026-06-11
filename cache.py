"""
Caching layer for TicketHub application
Improves performance by reducing redundant database queries
"""

import streamlit as st
import hashlib
from datetime import datetime, timedelta


class CacheManager:
    """Manages caching of database queries and API responses."""
    
    @staticmethod
    def get_cache_key(*args, **kwargs):
        """Generate a unique cache key from arguments."""
        cache_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    @staticmethod
    def cache_query(key, value, ttl_seconds=300):
        """Store query result in Streamlit session cache."""
        if "cache" not in st.session_state:
            st.session_state.cache = {}
        
        st.session_state.cache[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "ttl": ttl_seconds
        }
    
    @staticmethod
    def get_cache(key):
        """Retrieve cached query result if not expired."""
        if "cache" not in st.session_state:
            return None
        
        cached = st.session_state.cache.get(key)
        if not cached:
            return None
        
        # Check if expired
        age = (datetime.now() - cached["timestamp"]).total_seconds()
        if age > cached["ttl"]:
            del st.session_state.cache[key]
            return None
        
        return cached["value"]
    
    @staticmethod
    def clear_cache():
        """Clear all cached data."""
        if "cache" in st.session_state:
            st.session_state.cache = {}


@st.cache_resource
def get_db_connection():
    """Cache database connection."""
    import db
    db.init_db()
    return db


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_user_profile_cached(username):
    """Cache user profile queries."""
    import db
    return db.get_user_profile(username)


@st.cache_data(ttl=300)
def get_agency_info_cached(agency_username):
    """Cache agency info queries."""
    import db
    return db.agencies_collection.find_one({"username": agency_username})


@st.cache_data(ttl=600)
def get_available_routes_cached(source=None, destination=None):
    """Cache route queries."""
    import db
    query = {}
    if source:
        query["source"] = source
    if destination:
        query["destination"] = destination
    
    return list(db.buses_collection.find(query).limit(50))


@st.cache_data(ttl=300)
def get_user_bookings_cached(username):
    """Cache user bookings queries."""
    import db
    return list(db.bookings_collection.find({"username": username}).sort("date", -1).limit(20))


@st.cache_data(ttl=300)
def get_agency_bookings_cached(agency_username):
    """Cache agency bookings queries."""
    import db
    return list(db.bookings_collection.find({"agency_username": agency_username}).sort("date", -1).limit(100))
