"""
ReasoningEngine — Tree-of-Thoughts & Chain-of-Thought Enhancement.

Elevates Manas's problem-solving from linear thinking to
multi-path deliberate reasoning. Instead of one answer,
Manas now explores multiple reasoning branches and picks the best.
"""

import logging
import json
import time
from typing import List

logger = logging.getLogger(__name__)


class ThoughtNode:
    """A single node in the Tree of Thoughts."""
    def __init__(self, content: str, score: float = 0.0, parent=None):
        self.content = content
        self.score = score
        self.parent = parent
        self.children: List['ThoughtNode'] = []
        self.depth = (parent.depth + 1) if parent else 0

    def add_child(self, content: str, score: float = 0.0) -> 'ThoughtNode':
        child = ThoughtNode(content, score, parent=self)
        self.children.append(child)
        return child

    def get_path(self) -> List[str]:
        """Trace the reasoning path from root to this node."""
        path = []
        node = self
        while node:
            path.append(node.content)
            node = node.parent
        return list(reversed(path))


class ReasoningEngine:
    """
    Advanced reasoning via Tree-of-Thoughts.
    Explores multiple reasoning paths and selects the best one.
    """

    def __init__(self, llm_router, max_depth: int = 3, branching_factor: int = 3, knowledge_graph=None, event_bus=None):
        self.llm_router = llm_router
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.knowledge_graph = knowledge_graph
        self.event_bus = event_bus
        self.total_thoughts_explored = 0

    def think_deeply(self, problem: str) -> str:
        """
        Main entry point: Applies Tree-of-Thoughts to a complex problem.
        Returns the best reasoning path found.
        """
        logger.info(f"ReasoningEngine: Deep thinking about: {problem[:80]}...")
        start_time = time.time()

        # Root node
        context_prompt = problem
        if self.knowledge_graph:
            # Try to find related entities in the graph
            # This is a simplified keyword-based lookup for demonstration
            keywords = problem.lower().split()
            related_info = ""
            for word in keywords:
                if len(word) > 4:
                    summary = self.knowledge_graph.get_context_summary(word)
                    if "No knowledge" not in summary:
                        related_info += f"\n--- Related Knowledge ({word}) ---\n{summary}\n"
            
            if related_info:
                logger.info("ReasoningEngine: Found relational context in KnowledgeGraph.")
                context_prompt = f"{problem}\n\nRELATIONAL CONTEXT FROM BRAIN:{related_info}"

        root = ThoughtNode(f"Problem: {context_prompt}")

        # BFS-style exploration
        best_leaf = self._explore(root, problem)
        elapsed = time.time() - start_time

        # Get the winning reasoning path
        path = best_leaf.get_path()
        self.total_thoughts_explored += self._count_nodes(root)

        result = (
            f"🌳 Tree-of-Thoughts Complete ({elapsed:.1f}s)\n"
            f"  Branches explored: {self._count_nodes(root)}\n"
            f"  Best path depth: {best_leaf.depth}\n"
            f"  Confidence: {best_leaf.score:.1f}/10\n\n"
            f"  Reasoning Chain:\n"
        )
        for i, step in enumerate(path[1:], 1):  # Skip the root "Problem:" node
            result += f"  Step {i}: {step[:150]}\n"

        # Phase 27: Broadcast Wisdom if highly confident
        if best_leaf.score >= 8.5 and self.event_bus:
            # The last step is usually the conclusion/insight
            insight = path[-1] if len(path) > 1 else "Complex structural insight."
            self.event_bus.emit("wisdom:generated", {
                "topic": problem[:100],
                "insight": insight,
                "confidence": best_leaf.score / 10.0
            })

        return result

    def _explore(self, node: ThoughtNode, problem: str) -> ThoughtNode:
        """Recursively explores the thought tree."""
        if node.depth >= self.max_depth:
            node.score = self._evaluate(node, problem)
            return node

        # Generate child thoughts
        children_content = self._generate_thoughts(node, problem)

        best_leaf = node
        best_score = -1

        for content in children_content[:self.branching_factor]:
            child = node.add_child(content)
            leaf = self._explore(child, problem)
            if leaf.score > best_score:
                best_score = leaf.score
                best_leaf = leaf

        if not node.children:
            node.score = self._evaluate(node, problem)
            return node

        return best_leaf

    def _generate_thoughts(self, node: ThoughtNode, problem: str) -> List[str]:
        """Generates branching thoughts from the current node."""
        path_so_far = " -> ".join(node.get_path())
        prompt = (
            f"You are solving this problem step by step:\n"
            f"Problem: {problem}\n"
            f"Reasoning so far: {path_so_far}\n\n"
            f"Generate {self.branching_factor} DIFFERENT possible next reasoning steps. "
            f"Each should be a distinct approach or angle.\n"
            f"Return as a JSON list of strings."
        )

        response = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        try:
            # Clean JSON from response
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()
            thoughts = json.loads(clean)
            if isinstance(thoughts, list):
                return [str(t) for t in thoughts]
        except (json.JSONDecodeError, IndexError):
            pass

        # Fallback: split by newlines
        return [line.strip() for line in response.split("\n") if line.strip()][:self.branching_factor]

    def _evaluate(self, node: ThoughtNode, problem: str) -> float:
        """Evaluates how good a reasoning path is (0-10 score)."""
        path = " -> ".join(node.get_path())
        prompt = (
            f"Rate this reasoning path for solving the problem on a scale of 0-10.\n"
            f"Problem: {problem}\n"
            f"Reasoning: {path}\n\n"
            f"Return ONLY a number between 0 and 10."
        )
        response = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        try:
            score = float(response.strip().split()[0])
            return min(10.0, max(0.0, score))
        except (ValueError, IndexError):
            return 5.0  # Default middle score

    def _count_nodes(self, node: ThoughtNode) -> int:
        """Counts total nodes in the tree."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def chain_of_thought(self, problem: str, steps: int = 5) -> str:
        """Simpler Chain-of-Thought reasoning (linear, no branching)."""
        prompt = (
            f"Solve this problem step by step. Show exactly {steps} reasoning steps.\n\n"
            f"Problem: {problem}\n\n"
            f"Think through each step carefully before giving your final answer."
        )
        response = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"🔗 Chain-of-Thought:\n{response}"

    def get_status(self) -> str:
        return (
            f"🌳 ReasoningEngine Status:\n"
            f"  Max depth: {self.max_depth}\n"
            f"  Branching factor: {self.branching_factor}\n"
            f"  Total thoughts explored: {self.total_thoughts_explored}"
        )
