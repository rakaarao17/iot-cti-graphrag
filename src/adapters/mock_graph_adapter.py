"""
Mock Graph Adapter -- For testing without Neo4j.

Returns deterministic responses suitable for unit tests.
"""

from typing import Dict, List, Optional, Any

from src.ports.graph_port import GraphPort


class MockGraphAdapter(GraphPort):
    """
    Mock graph database for testing.
    
    Returns predictable responses without Neo4j.
    """
    
    def __init__(self):
        self.query_count = 0
        self.last_query = None
        self.connected = True
    
    def run_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute mock query."""
        self.query_count += 1
        self.last_query = query
        
        # Return mock data for common queries
        if "count(n)" in query:
            return [{"node_count": 5500000}]
        elif "count(r)" in query:
            return [{"rel_count": 22000000}]
        elif "Device" in query:
            return [
                {"ip": "192.168.1.1", "role": "gateway", "degree": 1500},
                {"ip": "192.168.1.50", "role": "iot_device", "degree": 250},
            ]
        else:
            return []
    
    def run_write_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute mock write query."""
        self.query_count += 1
        self.last_query = query
        
        return {
            "nodes_created": 100,
            "relationships_created": 500,
            "nodes_deleted": 0,
            "relationships_deleted": 0,
            "properties_set": 200,
        }
    
    def verify_connectivity(self) -> bool:
        return self.connected
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "node_count": 5500000,
            "relationship_count": 22000000,
            "avg_degree": 8.0,
        }
