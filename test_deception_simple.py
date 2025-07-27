#!/usr/bin/env python3
"""
Simple test script to demonstrate the deception detection system implementation.
This tests only the deception detection components without LLM dependencies.
"""

from deception_detection import DeceptionDetector, update_deception_history
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from datetime import datetime
import json

# Simplified GameState for testing
class TestGameState(BaseModel):
    round_num: int = 0
    players: List[str] = []
    alive_players: List[str] = []
    roles: Dict[str, str] = {}
    phase: str = "debate"
    deception_history: Dict[str, List[Dict]] = Field(default_factory=dict)
    deception_scores: Dict[str, Dict[str, float]] = Field(default_factory=dict)

def generate_test_deception_summary(state: TestGameState) -> Dict:
    """Generate a summary of deception patterns for testing."""
    summary = {
        "total_statements_analyzed": 0,
        "deception_by_player": {},
        "final_deception_scores": state.deception_scores,
        "deception_patterns": {}
    }
    
    for player, history in state.deception_history.items():
        player_summary = {
            "total_statements": len(history),
            "self_reported_deceptions": 0,
            "peer_detected_deceptions": 0,
            "average_suspicion": 0.0
        }
        
        total_suspicion = 0
        suspicion_count = 0
        
        for record in history:
            if record["self_analysis"].get("is_deceptive", 0) == 1:
                player_summary["self_reported_deceptions"] += 1
            
            for peer_analysis in record["other_analyses"].values():
                if peer_analysis.get("is_deceptive", 0) == 1:
                    player_summary["peer_detected_deceptions"] += 1
                
                suspicion = peer_analysis.get("suspicion_level", 0.5)
                total_suspicion += suspicion
                suspicion_count += 1
        
        if suspicion_count > 0:
            player_summary["average_suspicion"] = total_suspicion / suspicion_count
            
        summary["deception_by_player"][player] = player_summary
        summary["total_statements_analyzed"] += len(history)
    
    return summary

def mock_llm_response(prompt):
    """Mock LLM that returns realistic deception analysis responses."""
    if "Alice" in prompt and "suspect Bob" in prompt:
        return {
            "chain_of_thought": "Alice is pointing suspicion at Bob. This could be genuine concern or deflection. Her confidence seems forced, which might indicate deception.",
            "is_deceptive": 1,
            "confidence": 0.7,
            "deception_type": "misdirection", 
            "reasoning": "Statement lacks specific evidence and seems like deflection",
            "suspicion_level": 0.8
        }
    elif "Bob" in prompt and "innocent" in prompt:
        return {
            "chain_of_thought": "Bob is claiming innocence directly. This is defensive but could be genuine. His tone seems sincere.",
            "is_deceptive": 0,
            "confidence": 0.6,
            "deception_type": "none",
            "reasoning": "Direct denial seems sincere based on tone",
            "suspicion_level": 0.3
        }
    else:
        return {
            "chain_of_thought": "Standard game behavior analysis. No clear deceptive indicators.",
            "is_deceptive": 0,
            "confidence": 0.5,
            "deception_type": "none",
            "reasoning": "No clear deceptive indicators detected",
            "suspicion_level": 0.5
        }

class MockLLM:
    """Mock LLM for testing without API calls."""
    def invoke(self, prompt, **kwargs):
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        response = mock_llm_response(prompt)
        return MockResponse(json.dumps(response))

def test_deception_detection():
    """Test the deception detection system with mock data."""
    print("🔍 Testing Deception Detection System")
    print("=" * 50)
    
    # Initialize test game state
    state = TestGameState(
        round_num=1,
        players=["Alice", "Bob", "Charlie"],
        alive_players=["Alice", "Bob", "Charlie"], 
        roles={"Alice": "Villager", "Bob": "Werewolf", "Charlie": "Seer"},
        phase="debate",
        deception_history={},
        deception_scores={}
    )
    
    # Initialize deception detector with mock LLM
    detector = DeceptionDetector(MockLLM())
    
    print("📝 Initial Game State:")
    print(f"Players: {state.players}")
    print(f"Roles: {state.roles}")
    print(f"Phase: {state.phase}")
    print()
    
    # Test Case 1: Alice makes a suspicious statement
    print("🎭 Test Case 1: Alice's Statement Analysis")
    statement1 = "I suspect Bob is acting strangely"
    print(f"Statement: '{statement1}'")
    
    # Self-analysis by Alice
    self_analysis1 = detector.analyze_self_deception("Alice", statement1, "Debate phase, round 1")
    print("Self-Analysis:")
    print(f"  Chain of Thought: {self_analysis1['chain_of_thought']}")
    print(f"  Is Deceptive: {self_analysis1['is_deceptive']}")
    print(f"  Confidence: {self_analysis1['confidence']}")
    print(f"  Reasoning: {self_analysis1['reasoning']}")
    print()
    
    # Peer analyses
    other_analyses1 = {}
    for observer in ["Bob", "Charlie"]:
        analysis = detector.analyze_other_deception(observer, "Alice", statement1, "Debate phase, round 1")
        analysis["timestamp"] = datetime.utcnow().isoformat()
        other_analyses1[observer] = analysis
        print(f"{observer}'s Analysis:")
        print(f"  Chain of Thought: {analysis['chain_of_thought']}")
        print(f"  Is Deceptive: {analysis['is_deceptive']}")
        print(f"  Suspicion Level: {analysis['suspicion_level']}")
        print(f"  Reasoning: {analysis['reasoning']}")
        print()
    
    # Update deception history
    state = update_deception_history(state, "Alice", statement1, self_analysis1, other_analyses1)
    
    # Test Case 2: Bob's defensive statement
    print("🎭 Test Case 2: Bob's Statement Analysis") 
    statement2 = "I'm innocent, you have to believe me!"
    print(f"Statement: '{statement2}'")
    
    # Self-analysis by Bob
    self_analysis2 = detector.analyze_self_deception("Bob", statement2, "Debate phase, round 1")
    print("Self-Analysis:")
    print(f"  Chain of Thought: {self_analysis2['chain_of_thought']}")
    print(f"  Is Deceptive: {self_analysis2['is_deceptive']}")
    print(f"  Confidence: {self_analysis2['confidence']}")
    print(f"  Reasoning: {self_analysis2['reasoning']}")
    print()
    
    # Peer analyses  
    other_analyses2 = {}
    for observer in ["Alice", "Charlie"]:
        analysis = detector.analyze_other_deception(observer, "Bob", statement2, "Debate phase, round 1")
        analysis["timestamp"] = datetime.utcnow().isoformat()
        other_analyses2[observer] = analysis
        print(f"{observer}'s Analysis:")
        print(f"  Chain of Thought: {analysis['chain_of_thought']}")
        print(f"  Is Deceptive: {analysis['is_deceptive']}")
        print(f"  Suspicion Level: {analysis['suspicion_level']}")
        print(f"  Reasoning: {analysis['reasoning']}")
        print()
    
    # Update deception history
    state = update_deception_history(state, "Bob", statement2, self_analysis2, other_analyses2)
    
    # Display final deception summary
    print("📊 Final Deception Summary")
    print("-" * 30)
    summary = generate_test_deception_summary(state)
    
    print(f"Total statements analyzed: {summary['total_statements_analyzed']}")
    print()
    
    for player, stats in summary['deception_by_player'].items():
        print(f"{player} ({state.roles[player]}):")
        print(f"  • Statements made: {stats['total_statements']}")
        print(f"  • Self-reported deceptions: {stats['self_reported_deceptions']}")
        print(f"  • Peer-detected deceptions: {stats['peer_detected_deceptions']}")
        print(f"  • Average suspicion level: {stats['average_suspicion']:.2f}")
        print()
    
    print("🎯 Deception Scores (how each player perceives others):")
    for observer, scores in state.deception_scores.items():
        score_str = ", ".join([f"{target}={score:.2f}" for target, score in scores.items()])
        print(f"  {observer}: {score_str}")
    print()
    
    print("✅ Deception Detection System Test Complete!")
    print()
    print("🔧 System Features Demonstrated:")
    print("  ✓ Chain of Thought reasoning for deception analysis")
    print("  ✓ Self-analysis by statement makers")
    print("  ✓ Peer analysis by other players") 
    print("  ✓ JSON-formatted output")
    print("  ✓ Deception history tracking")
    print("  ✓ Dynamic suspicion score updates")
    print("  ✓ Comprehensive summary generation")
    print("  ✓ Binary deception classification (0 or 1)")

if __name__ == "__main__":
    test_deception_detection()