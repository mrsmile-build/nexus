"""
NEXUS Code Engine v0.1
Professional programming intelligence:
- review(): scored audit (security/performance/maintainability/modernity/portability)
- fix(): iterative RUN-VERIFY loop in a sandbox (it sees its own errors)
- scaffold(): generates a modern professional project skeleton
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from core.llm_client import ask, LLMError

class CodeEngine:
    # ---------- SANDBOX ----------
    def _run(self, code: str, timeout=10):
        try:
            with tempfile.TemporaryDirectory() as d:
                r = subprocess.run(
                    [sys.executable, "-I", "-c", code],
                    capture_output=True, text=True, timeout=timeout, cwd=d,
                    env={"PATH": os.environ.get("PATH", "")}
                )
                if r.returncode == 0:
                    return True, (r.stdout or "OK")[:2000]
                return False, (r.stderr or r.stdout)[:2000]
        except subprocess.TimeoutExpired:
            return False, "TimeoutError: code ran longer than 10s (possible infinite loop)"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    def _extract_code(self, raw: str) -> str:
        m = re.search(r"```(?:python)?\n([\s\S]*?)```", raw)
        return m.group(1).strip() if m else raw.strip()

    # ---------- FIX (run-verify loop) ----------
    def fix(self, code: str, error: str = "", max_rounds=3):
        current = code
        rounds = []
        for i in range(max_rounds):
            ok, out = self._run(current)
            if ok:
                return {"fixed": True, "rounds": rounds, "code": current, "output": out, "method": "run-verify-loop"}
            err = error if i == 0 and error else out
            rounds.append({"round": i + 1, "error_seen": err[:600]})
            try:
                raw = ask(
                    f"This Python code fails.\n\nCODE:\n{current[:6000]}\n\nERROR:\n{err[:2000]}\n\nFix it. Return ONLY the corrected complete code inside one ```python block. No explanations.",
                    system="You are a principal Python engineer. Minimal surgical fixes. Preserve behavior. Never add dependencies.",
                    max_tokens=3000
                )
                current = self._extract_code(raw)
            except LLMError as e:
                return {"fixed": False, "rounds": rounds, "code": current, "error": str(e)}
        ok, out = self._run(current)
        return {"fixed": ok, "rounds": rounds, "code": current, "output": out, "method": "run-verify-loop"}

    # ---------- REVIEW (scored audit) ----------
    def review(self, code: str, context: str = ""):
        system = """You are a principal engineer auditor (20 yrs: startups + big-tech). Audit the code like a ruthless staff-engineer code review.
Score 0-100 each: security, performance, maintainability, modernity, portability.
List issues by severity CRITICAL/HIGH/MEDIUM/LOW with line references where possible and exact fixes.
Context: """ + (context or "general production use") + """
Output ONLY valid JSON:
{"scores": {"security":0,"performance":0,"maintainability":0,"modernity":0,"portability":0}, "overall": 0, "issues": [{"severity":"","problem":"","fix":""}], "strengths": [], "verdict": ""}"""
        try:
            raw = ask(code[:8000], system=system, max_tokens=2000)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            # SymPy-verified overall = weighted mean of the five scores
            sc = data.get("scores", {})
            expr = f"0.3*{sc.get('security',0)} + 0.25*{sc.get('performance',0)} + 0.2*{sc.get('maintainability',0)} + 0.15*{sc.get('modernity',0)} + 0.1*{sc.get('portability',0)}"
            from engines.tools.src.math_tool import MathTool
            res = MathTool().calculate(expr)
            try:
                data["overall"] = round(float(res.get("result")), 1)
                data["math_verified"] = True
            except Exception:
                data["overall"] = sc.get("security", 0)
            return {"data": data, "method": "llm+math-audit"}
        except json.JSONDecodeError:
            return {"raw": raw, "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}

    # ---------- SCAFFOLD (professional skeleton) ----------
    def _salvage(self, t):
        try:
            return json.loads(t), False
        except Exception:
            pass
        for end in range(len(t) - 1, 0, -1):
            if t[end] in '}]':
                frag = t[:end + 1]
                stack = []; in_str = False; esc = False
                for ch in frag:
                    if in_str:
                        if esc: esc = False
                        elif ch == '\\': esc = True
                        elif ch == '"': in_str = False
                        continue
                    if ch == '"': in_str = True
                    elif ch in '{[': stack.append(ch)
                    elif ch in '}]':
                        if stack: stack.pop()
                if in_str:
                    continue
                closers = ''.join('}' if c == '{' else ']' for c in reversed(stack))
                try:
                    return json.loads(frag + closers), True
                except Exception:
                    continue
        return None, False

    def scaffold(self, spec: str):
        system = """You are a startup CTO generating a MODERN PROFESSIONAL project skeleton.
Every skeleton MUST include: auth/API-key gate, rate limiting, error handling, tests, CI workflow, README, .env.example, health endpoint, versioning, observability hooks, and a clean REST/JSON contract (hardware-agnostic, portable to any future CPU).
HARD LIMITS: exactly 6 files; each file content MAX 45 lines; keep JSON compact so the response finishes.
Output ONLY valid JSON:
{"stack": "", "tree": "ascii file tree", "files": [{"path": "", "content": ""}], "professional_checklist": [], "why_modern": ""}"""
        try:
            raw = ask(spec, system=system, max_tokens=7500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data, salvaged = self._salvage(clean.strip())
            if data is None:
                return {"raw": raw[:4000], "error": "parse failed"}
            out = {"data": data, "method": "scaffold" + ("+salvage" if salvaged else "")}
            if salvaged:
                out["note"] = "Output was cut by token limit; recovered the complete portion. Ask again for the remaining files."
            return out
        except LLMError as e:
            return {"error": str(e)}
