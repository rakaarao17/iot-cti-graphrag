"""
Graph Port -- Abstract interface for knowledge graph backends.

Allows swapping between Neo4j, Amazon Neptune, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class GraphPort(ABC):
    """
    Abstract graph database service.
    
    Any concrete graph implementation must inherit from this.
    """
    
    @abstractmethod
    def run_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a read query.
        
        Args:
            query: Cypher query (or equivalent language)
            params: Query parameters
            
        Returns:
            List of result records
            
        Raises:
            GraphError: If query failed
        """
        pass
    
    @abstractmethod
    def run_write_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a write query (CREATE, UPDATE, DELETE).
        
        Returns:
            Statistics (nodes created, relationships updated, etc.)
        """
        pass
    
    @abstractmethod
    def verify_connectivity(self) -> bool:
        """Check if graph database is accessible."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Return graph statistics.
        
        Example:
            {
                'node_count': 5500000,
                'relationship_count': 22000000,
                'avg_degree': 8.0
            }
        """
        pass
