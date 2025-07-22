"""
Point d'entrée principal pour l'API LangGraph.
Exporte le graph depuis graph2.py pour que l'API puisse le charger.
"""

from graph2 import graph

# Exporter le graph pour l'API LangGraph
__all__ = ["graph"] 