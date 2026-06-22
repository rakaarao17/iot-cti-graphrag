"""
Neo4j Adapter -- Implements GraphPort for Neo4j database.

Wraps the Neo4j Python driver with proper connection management.
"""

from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase, Session

from src.ports.graph_port import GraphPort
from src.core.exceptions import GraphError


class Neo4jAdapter(GraphPort):
    """
    Neo4j graph database adapter.
    
    Manages connection and query execution against Neo4j.
    """
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "iot",
    ):
        """
        Initialize Neo4j adapter.
        
        Args:
            uri: Neo4j connection string (e.g., bolt://localhost:7687)
            user: Database user
            password: Database password
            database: Database name
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        
        try:
            self.driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
            )
            # Test connection
            self.driver.verify_connectivity()
        except Exception as e:
            raise GraphError(
                message=f"Failed to connect to Neo4j at {uri}",
                details={"uri": uri, "error": str(e)},
                recovery_hint="Ensure Neo4j is running and credentials are correct.",
            )
    
    def run_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a read query."""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except Exception as e:
            raise GraphError(
                message=f"Query execution failed",
                details={"query": query[:100], "error": str(e)},
            )
    
    def run_write_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a write query."""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params or {})
                summary = result.consume()
                
                return {
                    "nodes_created": summary.counters.nodes_created,
                    "relationships_created": summary.counters.relationships_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set,
                }
        except Exception as e:
            raise GraphError(
                message=f"Write query execution failed",
                details={"query": query[:100], "error": str(e)},
            )
    
    def verify_connectivity(self) -> bool:
        """Check if graph database is accessible."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        try:
            results = self.run_query("""
                MATCH (n) RETURN count(n) as node_count
            """)
            node_count = results[0]['node_count'] if results else 0
            
            rel_results = self.run_query("""
                MATCH ()-[r]->() RETURN count(r) as rel_count
            """)
            rel_count = rel_results[0]['rel_count'] if rel_results else 0
            
            return {
                "node_count": node_count,
                "relationship_count": rel_count,
                "avg_degree": (rel_count * 2 / node_count) if node_count > 0 else 0,
            }
        except Exception as e:
            raise GraphError(
                message="Failed to retrieve graph statistics",
                details={"error": str(e)},
            )
    
    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
