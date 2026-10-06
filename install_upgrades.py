import sys

def patch(path, fn):
    try:
        s = open(path).read()
    except FileNotFoundError:
        print(f"MISSING {path}"); return
    new = fn(s)
    if new and new != s:
        open(path, 'w').write(new)

# ---------- NATURE: wire sterility into return ----------
def nature(s):
    if '"sterility_evaluation"' in s:
        print("nature: already wired"); return None
    i = s.find('def investigate(self')
    r = s.find('\n        return', i)
    if i == -1 or r == -1:
        print("nature: markers missing"); return None
    call = '\n        try:\n            sterility = self._check_sterility(subject, tradition)\n        except Exception:\n            sterility = {"sterility_risk_level": "unknown", "warning_message": ""}\n'
    s = s[:r] + call + s[r:]
    r2 = s.find('\n        return', i)
    b = s.find('{', r2)
    s = s[:b+1] + '\n            "sterility_evaluation": sterility,' + s[b+1:]
    print("nature: sterility wired into return")
    return s
patch('engines/nature_core/src/nature_core.py', nature)

# ---------- MATERIALS: agri-byproduct mapping ----------
def materials(s):
    changed = False
    if 'import json' not in s:
        s = 'import json\n' + s; changed = True
    if '_map_agri_byproducts' not in s:
        m = s.find('def formulate(self')
        if m != -1:
            method = '''    def _map_agri_byproducts(self, target: str) -> dict:
        """Map agricultural waste to industrial substitutes."""
        prompt = f"""You are an industrial materials expert in agricultural by-product utilization.
Target material/application: {target}
List crop-residue substitutes for conventional materials.
Output ONLY valid JSON:
{{"byproduct_substitutes": [{{"byproduct": "", "replaces": "", "processing": "", "performance": "", "availability": "", "sustainability": ""}}], "cost_comparison": ""}}"""
        try:
            raw = ask(prompt, max_tokens=1200)
            clean = raw.strip()
            for t in ("```json", "```"):
                if clean.startswith(t): clean = clean[len(t):]
            if clean.endswith("```"): clean = clean[:-3]
            return json.loads(clean.strip())
        except Exception:
            return {"byproduct_substitutes": []}

'''
            s = s[:m] + method + s[m:]; changed = True
            print("materials: method added")
    if '"agri_byproduct_substitutes"' not in s:
        i = s.find('def formulate(self')
        r = s.find('\n        return', i)
        if r != -1:
            call = '\n        try:\n            byproducts = self._map_agri_byproducts(target_material)\n        except Exception:\n            byproducts = {"byproduct_substitutes": []}\n'
            s = s[:r] + call + s[r:]
            r2 = s.find('\n        return', i)
            b = s.find('{', r2)
            s = s[:b+1] + '\n            "agri_byproduct_substitutes": byproducts,' + s[b+1:]
            changed = True
            print("materials: wired into return")
    return s if changed else None
patch('engines/materials/src/materials.py', materials)

# ---------- BUSINESS: rural detector + safety framework ----------
def business(s):
    changed = False
    if 'rural_economy_detector' not in s:
        m = s.find('def plan(self')
        if m != -1:
            le = s.find('\n', m)
            inj = '\n        # Rural economy detector (self-improvement)\n        if any(k in (situation + " " + goal).lower() for k in ["rural", "village", "low population", "small town", "countryside"]):\n            situation += " CONTEXT: rural/low-population area - prioritize value-added products, pre-payment/subscription cash-flow models, premium urban buyers, abundant local raw materials."\n'
            s = s[:le] + inj + s[le:]
            changed = True; print("business: rural detector added")
    if '_safety_framework_check' not in s:
        m = s.find('def plan(self')
        if m != -1:
            method = '''    def _safety_framework_check(self, idea: dict) -> dict:
        """Quality control + safety lens for business ideas."""
        prompt = f"""Business idea: {json.dumps(idea)[:1200]}
List quality-control requirements, regulatory compliance, safety hazards, mitigation strategies.
Output ONLY valid JSON:
{{"quality_control": [], "regulatory_compliance": [], "safety_hazards": [], "mitigation_strategies": []}}"""
        try:
            raw = ask(prompt, max_tokens=800)
            clean = raw.strip()
            for t in ("```json", "```"):
                if clean.startswith(t): clean = clean[len(t):]
            if clean.endswith("```"): clean = clean[:-3]
            return json.loads(clean.strip())
        except Exception:
            return {"quality_control": [], "safety_hazards": []}

'''
            s = s[:m] + method + s[m:]
            changed = True; print("business: safety method added")
    if '"safety_framework"' not in s:
        sort = s.find('.sort(key=lambda x: x.get("nexus_score")')
        if sort != -1:
            ls = s.rfind('\n', 0, sort)
            hook = '\n            for idea in data.get("ideas", [])[:2]:\n                try:\n                    idea["safety_framework"] = self._safety_framework_check(idea)\n                except Exception:\n                    pass\n'
            s = s[:ls] + hook + s[ls:]
            changed = True; print("business: safety hook added")
    return s if changed else None
patch('engines/business/src/business.py', business)

# ---------- API: wire cross-domain endpoint ----------
def api(s):
    changed = False
    if 'CrossDomainEngine' not in s:
        a = s.find('from engines.consolidation.src.consolidation_engine import ConsolidationEngine')
        if a != -1:
            le = s.find('\n', a)
            s = s[:le] + '\nfrom engines.cross_domain.src.cross_domain_engine import CrossDomainEngine' + s[le:]
            changed = True; print("api: import added")
    if 'cross_domain_engine =' not in s:
        a = s.find('consolidation_engine = ConsolidationEngine()')
        if a != -1:
            le = s.find('\n', a)
            s = s[:le] + '\ncross_domain_engine = CrossDomainEngine()' + s[le:]
            changed = True; print("api: init added")
    if '"/cross-domain"' not in s:
        a = s.find('@app.post("/consolidate"')
        if a != -1:
            ep = '@app.post("/cross-domain", dependencies=[Depends(require_key)])\ndef cross_domain(request: ChatRequest):\n    return cross_domain_engine.find_connections(request.message)\n\n'
            s = s[:a] + ep + s[a:]
            changed = True; print("api: endpoint added")
    return s if changed else None
patch('core/api.py', api)

print("INSTALLER DONE")
