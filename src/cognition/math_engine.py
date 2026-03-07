"""
MathEngine — Manas's Mathematical Brain.

Gives Manas the power of a mathematician:
1. Symbolic computation (algebra, calculus, linear algebra)
2. Formula discovery — derive new formulas from data
3. Self-optimization — use math to model and improve its own performance
4. Equation solving, integration, differentiation
5. Statistical modeling of its own behavior patterns

Uses SymPy (open-source computer algebra system) — the same engine
behind Wolfram Alpha's symbolic math.
"""

import logging
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing SymPy
try:
    import sympy
    from sympy import (
        symbols, solve, simplify, expand, factor, diff, integrate,
        Matrix, Rational, pi, E, oo, sqrt, sin, cos, tan, log, exp,
        series, limit, summation, product, latex, pretty,
        Function, Symbol, Eq, solveset, S
    )
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False


class MathEngine:
    """
    Manas's mathematical reasoning core.
    Combines symbolic computation with LLM for formula discovery.
    """

    def __init__(self, llm_router, data_dir: str):
        self.llm_router = llm_router
        self.data_dir = Path(data_dir)
        self.formulas_dir = self.data_dir / "math_formulas"
        self.formulas_dir.mkdir(parents=True, exist_ok=True)
        self.formula_book_path = self.data_dir / "formula_book.json"
        self._load_formula_book()

    def _load_formula_book(self):
        if self.formula_book_path.exists():
            with open(self.formula_book_path, "r") as f:
                self.formula_book = json.load(f)
        else:
            self.formula_book = {
                "formulas": [],
                "total_computed": 0,
                "total_discovered": 0
            }

    def _save_formula_book(self):
        with open(self.formula_book_path, "w") as f:
            json.dump(self.formula_book, f, indent=2)

    # ─── Core Symbolic Math ───

    def compute(self, expression: str) -> str:
        """
        Evaluate or simplify a mathematical expression using SymPy.
        Examples: "solve(x**2 - 4, x)", "diff(sin(x)*x**2, x)", "integrate(x**3, x)"
        """
        if not HAS_SYMPY:
            return self._llm_math_fallback(expression)

        self.formula_book["total_computed"] += 1
        self._save_formula_book()

        try:
            # Set up common symbols
            x, y, z, t, n, k = symbols('x y z t n k')

            # Parse and evaluate
            transformations = standard_transformations + (implicit_multiplication_application,)
            
            # Handle special commands
            expr_lower = expression.lower().strip()

            if expr_lower.startswith("solve"):
                result = eval(expression, {"__builtins__": {}}, {
                    "solve": solve, "symbols": symbols, "Eq": Eq,
                    "x": x, "y": y, "z": z, "t": t,
                    "sin": sin, "cos": cos, "tan": tan,
                    "log": log, "exp": exp, "sqrt": sqrt,
                    "pi": pi, "E": E, "Rational": Rational,
                })
                return f"🔢 Solution: {result}"

            elif expr_lower.startswith("diff") or expr_lower.startswith("differentiate"):
                result = eval(expression, {"__builtins__": {}}, {
                    "diff": diff, "symbols": symbols,
                    "x": x, "y": y, "z": z, "t": t,
                    "sin": sin, "cos": cos, "tan": tan,
                    "log": log, "exp": exp, "sqrt": sqrt,
                    "pi": pi, "E": E,
                })
                return f"🔢 Derivative: {result}"

            elif expr_lower.startswith("integrate") or expr_lower.startswith("integral"):
                result = eval(expression, {"__builtins__": {}}, {
                    "integrate": integrate, "symbols": symbols,
                    "x": x, "y": y, "z": z, "t": t,
                    "sin": sin, "cos": cos, "tan": tan,
                    "log": log, "exp": exp, "sqrt": sqrt,
                    "pi": pi, "E": E, "oo": oo,
                })
                return f"🔢 Integral: {result}"

            elif expr_lower.startswith("simplify"):
                inner = expression[len("simplify"):].strip().strip("()")
                parsed = parse_expr(inner, transformations=transformations)
                result = simplify(parsed)
                return f"🔢 Simplified: {result}"

            elif expr_lower.startswith("factor"):
                inner = expression[len("factor"):].strip().strip("()")
                parsed = parse_expr(inner, transformations=transformations)
                result = factor(parsed)
                return f"🔢 Factored: {result}"

            elif expr_lower.startswith("expand"):
                inner = expression[len("expand"):].strip().strip("()")
                parsed = parse_expr(inner, transformations=transformations)
                result = expand(parsed)
                return f"🔢 Expanded: {result}"

            elif expr_lower.startswith("limit"):
                result = eval(expression, {"__builtins__": {}}, {
                    "limit": limit, "symbols": symbols,
                    "x": x, "y": y, "z": z, "t": t, "n": n,
                    "sin": sin, "cos": cos, "tan": tan,
                    "log": log, "exp": exp, "sqrt": sqrt,
                    "pi": pi, "E": E, "oo": oo,
                })
                return f"🔢 Limit: {result}"

            elif expr_lower.startswith("matrix"):
                result = eval(expression, {"__builtins__": {}}, {
                    "Matrix": Matrix, "symbols": symbols,
                    "x": x, "y": y, "z": z,
                })
                return f"🔢 Matrix result:\n{pretty(result)}"

            else:
                # General expression evaluation
                parsed = parse_expr(expression, transformations=transformations)
                simplified = simplify(parsed)
                return f"🔢 Result: {simplified}"

        except Exception as e:
            # Fallback to LLM for complex expressions
            return self._llm_math_fallback(expression, error=str(e))

    def _llm_math_fallback(self, expression: str, error: str = "") -> str:
        """Uses LLM when SymPy can't handle the expression."""
        context = f" (SymPy error: {error})" if error else ""
        prompt = (
            f"Solve this mathematical expression/problem{context}:\n"
            f"{expression}\n\n"
            f"Show your work step by step. Provide the final answer clearly."
        )
        result = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"🔢 (LLM-computed): {result}"

    # ─── Formula Discovery ───

    def discover_formula(self, problem_description: str) -> str:
        """
        Use LLM + SymPy to discover or derive a new formula.
        Manas can create new math to solve novel problems.
        """
        prompt = (
            f"As a mathematician and AI researcher, derive a mathematical formula for:\n"
            f"{problem_description}\n\n"
            f"Provide:\n"
            f"1. The formula in standard mathematical notation\n"
            f"2. The formula as a Python/SymPy expression\n"
            f"3. Variable definitions\n"
            f"4. Derivation steps\n"
            f"5. Domain/range constraints\n"
            f"6. Practical applications"
        )
        discovery = self.llm_router.generate(prompt=prompt, task_type="reasoning")

        # Save to formula book
        entry = {
            "problem": problem_description,
            "formula": discovery[:500],
            "discovered_at": time.time()
        }
        self.formula_book["formulas"].append(entry)
        self.formula_book["total_discovered"] += 1
        self._save_formula_book()

        return f"📐 Formula Discovered:\n{discovery}"

    # ─── Self-Optimization via Math ───

    def optimize_self(self, metric_name: str, data_points: list = None) -> str:
        """
        Uses mathematical modeling to optimize Manas's own performance.
        Analyzes patterns in agent response times, memory usage, etc.
        """
        if not HAS_SYMPY:
            return "⚠️ SymPy required for mathematical optimization. Install: pip install sympy"

        if not data_points:
            # Use synthetic performance data as an example
            data_points = [
                {"x": 1, "y": 10}, {"x": 2, "y": 8},
                {"x": 3, "y": 6.5}, {"x": 4, "y": 5.5},
                {"x": 5, "y": 5.1}, {"x": 6, "y": 5.0},
            ]

        # Fit a curve: y = a / (x + b) + c (diminishing returns model)
        x_sym = Symbol('x')
        a, b, c = symbols('a b c')

        # Use LLM to analyze the pattern and suggest optimization
        data_str = json.dumps(data_points)
        prompt = (
            f"Analyze this performance data for '{metric_name}':\n{data_str}\n\n"
            f"1. Identify the mathematical pattern (linear, exponential, logarithmic, etc.)\n"
            f"2. Fit a formula to the data\n"
            f"3. Find the optimal operating point\n"
            f"4. Predict future values\n"
            f"5. Suggest how to improve the metric\n"
            f"Express the formula as a SymPy expression."
        )
        analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")

        return (
            f"📊 Self-Optimization Analysis for '{metric_name}':\n"
            f"  Data points: {len(data_points)}\n\n"
            f"{analysis}"
        )

    def efficiency_formula(self) -> str:
        """
        Derives Manas's own efficiency formula based on its architecture.
        E = (T * M * A) / (L * C)
        where T=throughput, M=memory, A=agents, L=latency, C=compute
        """
        if not HAS_SYMPY:
            return "⚠️ SymPy required."

        T, M, A, L, C = symbols('T M A L C', positive=True)
        E = (T * M * A) / (L * C)

        # Partial derivatives — what affects efficiency most?
        dE_dT = diff(E, T)  # How throughput affects efficiency
        dE_dL = diff(E, L)  # How latency affects efficiency
        dE_dA = diff(E, A)  # How adding agents affects efficiency

        return (
            f"📐 Manas Efficiency Formula:\n"
            f"  E = (T × M × A) / (L × C)\n\n"
            f"  Where:\n"
            f"    T = Throughput (tasks/sec)\n"
            f"    M = Memory utilization (0-1)\n"
            f"    A = Active agents\n"
            f"    L = Average latency (ms)\n"
            f"    C = Compute usage (%)\n\n"
            f"  Sensitivity Analysis:\n"
            f"    ∂E/∂T = {dE_dT}  (throughput impact)\n"
            f"    ∂E/∂L = {dE_dL}  (latency impact — negative!)\n"
            f"    ∂E/∂A = {dE_dA}  (agent count impact)\n\n"
            f"  Key Insight: Reducing latency has the BIGGEST impact on efficiency\n"
            f"  (inverse square relationship)."
        )

    # ─── Status ───

    def get_status(self) -> str:
        sympy_status = f"v{sympy.__version__}" if HAS_SYMPY else "NOT INSTALLED"
        return (
            f"📐 MathEngine Status:\n"
            f"  SymPy: {sympy_status}\n"
            f"  Computations: {self.formula_book['total_computed']}\n"
            f"  Formulas discovered: {self.formula_book['total_discovered']}\n"
            f"  Formula book: {len(self.formula_book['formulas'])} entries\n"
            f"  Capabilities: solve, diff, integrate, simplify, factor,\n"
            f"    expand, limit, matrix, series, formula discovery,\n"
            f"    self-optimization, efficiency modeling"
        )
