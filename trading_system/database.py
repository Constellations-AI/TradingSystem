"""
Database Manager for Trading System
Handles all database operations including caching, briefings, and analytics
Supports both SQLite (local) and PostgreSQL (production)
"""
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import os

# PostgreSQL support (optional)
try:
    import psycopg2
    import psycopg2.extras
    HAS_POSTGRESQL = True
except ImportError:
    HAS_POSTGRESQL = False


class Database:
    """Central database manager for trading system data"""
    _initialized = False  # Class variable to track initialization
    
    def __init__(self, db_path: str = "trading_system.db"):
        # Check for PostgreSQL connection string
        self.database_url = os.getenv("DATABASE_URL")
        self.use_postgresql = bool(self.database_url and HAS_POSTGRESQL)
        
        # Only show debug info once
        if not Database._initialized:
            print(f"🔍 Environment debug:")
            print(f"   DATABASE_URL present: {bool(self.database_url)}")
            print(f"   DATABASE_URL value: {self.database_url[:50] + '...' if self.database_url else 'None'}")
            print(f"   PostgreSQL library available: {HAS_POSTGRESQL}")
            print(f"   Will use PostgreSQL: {self.use_postgresql}")
            
            if self.use_postgresql:
                print(f"🐘 Using PostgreSQL database")
            else:
                self.db_path = db_path
                print(f"📂 Using SQLite database at {db_path}")
                
            self.init_database()
            Database._initialized = True
        else:
            # Just set the path without reinitializing
            if not self.use_postgresql:
                self.db_path = db_path
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            print(f"🔧 Initializing database tables...")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                print(f"✅ Database connection established")
                
                # Create all tables with appropriate primary key syntax
                tables = [
                    # Raw API calls and responses
                    ("raw_api_calls", """
                        CREATE TABLE IF NOT EXISTS raw_api_calls (
                            id {id_type},
                            provider TEXT NOT NULL,
                            function_name TEXT NOT NULL,
                            parameters TEXT NOT NULL,
                            parameters_hash TEXT NOT NULL,
                            response_data TEXT NOT NULL,
                            success BOOLEAN NOT NULL,
                            error_message TEXT,
                            was_cached BOOLEAN DEFAULT FALSE,
                            cache_age_seconds INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(provider, function_name, parameters_hash)
                        )
                    """),
                    
                    # Market briefings
                    ("market_briefings", """
                        CREATE TABLE IF NOT EXISTS market_briefings (
                            id {id_type},
                            session_id TEXT NOT NULL,
                            user_query TEXT NOT NULL,
                            success_criteria TEXT NOT NULL,
                            briefing_content TEXT NOT NULL,
                            agent_type TEXT DEFAULT 'market_intelligence',
                            processing_time_ms INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """),
                    
                    # Junction table linking briefings to their data sources
                    ("briefing_data_sources", """
                        CREATE TABLE IF NOT EXISTS briefing_data_sources (
                            id {id_type},
                            briefing_id INTEGER NOT NULL,
                            api_call_id INTEGER NOT NULL,
                            data_freshness_seconds INTEGER NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (briefing_id) REFERENCES market_briefings (id),
                            FOREIGN KEY (api_call_id) REFERENCES raw_api_calls (id)
                        )
                    """),
                    
                    # User sessions and conversation history
                    ("user_sessions", """
                        CREATE TABLE IF NOT EXISTS user_sessions (
                            id {id_type},
                            session_id TEXT UNIQUE NOT NULL,
                            user_query TEXT NOT NULL,
                            success_criteria TEXT NOT NULL,
                            conversation_history TEXT,
                            debug_mode BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """),
                    
                    # Evaluator feedback and decisions
                    ("evaluator_feedback", """
                        CREATE TABLE IF NOT EXISTS evaluator_feedback (
                            id {id_type},
                            session_id TEXT NOT NULL,
                            briefing_id INTEGER,
                            feedback_text TEXT NOT NULL,
                            success_criteria_met BOOLEAN NOT NULL,
                            user_input_needed BOOLEAN NOT NULL,
                            evaluation_reasoning TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (briefing_id) REFERENCES market_briefings (id)
                        )
                    """),
                    
                    # Tool usage tracking
                    ("tool_usage", """
                        CREATE TABLE IF NOT EXISTS tool_usage (
                            id {id_type},
                            session_id TEXT NOT NULL,
                            tool_name TEXT NOT NULL,
                            tool_args TEXT NOT NULL,
                            tool_response TEXT NOT NULL,
                            execution_time_ms INTEGER,
                            success BOOLEAN NOT NULL,
                            error_message TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """),
                    
                    # Trader accounts table for account persistence
                    ("trader_accounts", """
                        CREATE TABLE IF NOT EXISTS trader_accounts (
                            trader_name TEXT PRIMARY KEY,
                            balance REAL DEFAULT 10000.0,
                            strategy TEXT DEFAULT '',
                            holdings TEXT DEFAULT '{}',
                            transactions TEXT DEFAULT '[]',
                            portfolio_history TEXT DEFAULT '[]',
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                ]
                
                # Set appropriate ID type based on database
                id_type = "SERIAL PRIMARY KEY" if self.use_postgresql else "INTEGER PRIMARY KEY AUTOINCREMENT"
                
                print(f"📊 Creating {'PostgreSQL' if self.use_postgresql else 'SQLite'} tables...")
                
                # Create each table
                for table_name, table_sql in tables:
                    print(f"  🔧 Creating table: {table_name}")
                    try:
                        # Only format if the SQL contains placeholders
                        if '{id_type}' in table_sql:
                            formatted_sql = table_sql.format(id_type=id_type)
                        else:
                            formatted_sql = table_sql
                        cursor.execute(formatted_sql)
                    except Exception as e:
                        print(f"❌ Error with table {table_name}: {e}")
                        print(f"📝 SQL preview: {table_sql[:100]}...")
                        raise
                
                # Create indexes for performance
                print(f"🔍 Creating database indexes...")
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_api_calls_hash ON raw_api_calls (provider, function_name, parameters_hash)",
                    "CREATE INDEX IF NOT EXISTS idx_api_calls_created ON raw_api_calls (created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_briefings_session ON market_briefings (session_id)",
                    "CREATE INDEX IF NOT EXISTS idx_sessions_id ON user_sessions (session_id)",
                    "CREATE INDEX IF NOT EXISTS idx_tool_usage_session ON tool_usage (session_id)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                conn.commit()
                print(f"✅ Database tables and indexes created successfully")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            print(f"📊 Database URL present: {bool(self.database_url)}")
            print(f"📊 PostgreSQL available: {HAS_POSTGRESQL}")
            print(f"📊 Using PostgreSQL: {self.use_postgresql}")
            import traceback
            traceback.print_exc()
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if self.use_postgresql:
            conn = psycopg2.connect(self.database_url)
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
            finally:
                conn.close()
    
    def generate_params_hash(self, params: Dict[str, Any]) -> str:
        """Generate consistent hash for API parameters"""
        # Sort parameters for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()
    
    def check_api_cache(self, provider: str, function_name: str, params: Dict[str, Any], 
                       cache_ttl_seconds: int = 1800) -> Optional[Tuple[Dict, int, int]]:
        """
        Check if API call exists in cache
        Returns: (response_data, cache_age_seconds, api_call_id) or None
        """
        params_hash = self.generate_params_hash(params)
        cutoff_time = datetime.now() - timedelta(seconds=cache_ttl_seconds)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, response_data, created_at FROM raw_api_calls
                WHERE provider = %s AND function_name = %s AND parameters_hash = %s
                  AND created_at > %s AND success = TRUE
                ORDER BY created_at DESC LIMIT 1
            """ if self.use_postgresql else """
                SELECT id, response_data, created_at FROM raw_api_calls
                WHERE provider = ? AND function_name = ? AND parameters_hash = ?
                  AND created_at > ? AND success = TRUE
                ORDER BY created_at DESC LIMIT 1
            """, (provider, function_name, params_hash, cutoff_time))
            result = cursor.fetchone()
            
            if result:
                # Handle both PostgreSQL datetime and SQLite string formats
                if self.use_postgresql and isinstance(result['created_at'], datetime):
                    created_at = result['created_at']
                else:
                    # SQLite stores as string
                    created_at = datetime.strptime(result['created_at'], "%Y-%m-%d %H:%M:%S")
                
                cache_age = int((datetime.utcnow() - created_at).total_seconds())
                response_data = json.loads(result['response_data'])
                return response_data, cache_age, result['id']
        
        return None
    
    def save_api_call(self, provider: str, function_name: str, params: Dict[str, Any],
                     response_data: Dict, success: bool, error_message: str = None,
                     was_cached: bool = False, cache_age: int = 0) -> int:
        """Save API call and response to database"""
        params_hash = self.generate_params_hash(params)
        
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO raw_api_calls 
                    (provider, function_name, parameters, parameters_hash, response_data, 
                     success, error_message, was_cached, cache_age_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """ if self.use_postgresql else """
                    INSERT INTO raw_api_calls 
                    (provider, function_name, parameters, parameters_hash, response_data, 
                     success, error_message, was_cached, cache_age_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    provider, function_name, json.dumps(params), params_hash,
                    json.dumps(response_data), success, error_message, was_cached, cache_age
                ))
                conn.commit()
                
                if self.use_postgresql:
                    cursor.execute("SELECT LASTVAL()")
                    return cursor.fetchone()[0]
                else:
                    return cursor.lastrowid
            except Exception as e:
                # If there's a constraint error, just return a dummy ID and continue
                print(f"⚠️ Database insert warning (continuing): {e}")
                return 1  # Return dummy ID to keep things working
    
    def save_briefing(self, session_id: str, user_query: str, success_criteria: str,
                     briefing_content: str, processing_time_ms: int = None,
                     data_source_ids: List[Tuple[int, int]] = None) -> int:
        """
        Save market briefing and link to data sources
        data_source_ids: List of (api_call_id, freshness_seconds) tuples
        """
        with self.get_connection() as conn:
            # Save briefing
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO market_briefings 
                (session_id, user_query, success_criteria, briefing_content, processing_time_ms)
                VALUES (%s, %s, %s, %s, %s)
            """ if self.use_postgresql else """
                INSERT INTO market_briefings 
                (session_id, user_query, success_criteria, briefing_content, processing_time_ms)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user_query, success_criteria, briefing_content, processing_time_ms))
            
            if self.use_postgresql:
                cursor.execute("SELECT LASTVAL()")
                briefing_id = cursor.fetchone()[0]
            else:
                briefing_id = cursor.lastrowid
            
            # Link to data sources
            if data_source_ids:
                for api_call_id, freshness_seconds in data_source_ids:
                    cursor.execute("""
                        INSERT INTO briefing_data_sources 
                        (briefing_id, api_call_id, data_freshness_seconds)
                        VALUES (%s, %s, %s)
                    """ if self.use_postgresql else """
                        INSERT INTO briefing_data_sources 
                        (briefing_id, api_call_id, data_freshness_seconds)
                        VALUES (?, ?, ?)
                    """, (briefing_id, api_call_id, freshness_seconds))
            
            conn.commit()
            return briefing_id
    
    def save_session(self, session_id: str, user_query: str, success_criteria: str,
                    conversation_history: List[Dict], debug_mode: bool = False):
        """Save or update user session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgresql:
                cursor.execute("""
                    INSERT INTO user_sessions 
                    (session_id, user_query, success_criteria, conversation_history, debug_mode, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (session_id) DO UPDATE SET
                        user_query = EXCLUDED.user_query,
                        success_criteria = EXCLUDED.success_criteria,
                        conversation_history = EXCLUDED.conversation_history,
                        debug_mode = EXCLUDED.debug_mode,
                        updated_at = CURRENT_TIMESTAMP
                """, (session_id, user_query, success_criteria, json.dumps(conversation_history), debug_mode))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO user_sessions 
                    (session_id, user_query, success_criteria, conversation_history, debug_mode, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (session_id, user_query, success_criteria, json.dumps(conversation_history), debug_mode))
            conn.commit()
    
    def save_evaluator_feedback(self, session_id: str, briefing_id: Optional[int],
                               feedback_text: str, success_criteria_met: bool,
                               user_input_needed: bool, reasoning: str = None):
        """Save evaluator feedback"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evaluator_feedback 
                (session_id, briefing_id, feedback_text, success_criteria_met, 
                 user_input_needed, evaluation_reasoning)
                VALUES (%s, %s, %s, %s, %s, %s)
            """ if self.use_postgresql else """
                INSERT INTO evaluator_feedback 
                (session_id, briefing_id, feedback_text, success_criteria_met, 
                 user_input_needed, evaluation_reasoning)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, briefing_id, feedback_text, success_criteria_met, 
                  user_input_needed, reasoning))
            conn.commit()
    
    def save_tool_usage(self, session_id: str, tool_name: str, tool_args: Dict,
                       tool_response: str, execution_time_ms: int = None,
                       success: bool = True, error_message: str = None):
        """Save tool usage tracking"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tool_usage 
                (session_id, tool_name, tool_args, tool_response, execution_time_ms, success, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """ if self.use_postgresql else """
                INSERT INTO tool_usage 
                (session_id, tool_name, tool_args, tool_response, execution_time_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, tool_name, json.dumps(tool_args), tool_response, 
                  execution_time_ms, success, error_message))
            conn.commit()
    
    def get_briefing_analytics(self) -> Dict[str, Any]:
        """Get analytics on briefing performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute("SELECT COUNT(*) as count FROM market_briefings")
            total_briefings = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM raw_api_calls")
            total_api_calls = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN was_cached THEN 1 END) * 100.0 / COUNT(*) as rate
                FROM raw_api_calls
            """)
            cache_hit_rate = cursor.fetchone()['rate']
            
            # Recent activity
            if self.use_postgresql:
                cursor.execute("""
                    SELECT COUNT(DISTINCT session_id) as count FROM user_sessions 
                    WHERE created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(DISTINCT session_id) as count FROM user_sessions 
                    WHERE created_at > datetime('now', '-24 hours')
                """)
            recent_sessions = cursor.fetchone()['count']
            
            return {
                'total_briefings': total_briefings,
                'total_api_calls': total_api_calls,
                'cache_hit_rate': round(cache_hit_rate, 2) if cache_hit_rate else 0,
                'recent_sessions_24h': recent_sessions
            }
