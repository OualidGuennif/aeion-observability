"""Intelligent Model Arbiter & Re-ranker for the Æion Factory.

Combines empirical multi-factor performance telemetry (cost efficiency, pass rate by domain,
latency safety margin, error penalties) with an optional Tier-1 Flue-Pi agent classifier.
Fails closed to deterministic empirical scoring if the model agent is unavailable or times out.
"""
from decimal import Decimal
import json
import os
import re
import time

from .models import DEFAULT_REVIEW_ORDER, MODELS, eligibility


class EmpiricalScorer:
    """Multi-factor empirical evaluation for candidate models."""

    @staticmethod
    def calculate_score(model, stats, purpose="review", task_context=None):
        """Compute a bounded composite score in [0.0, 1.0].
        
        Factors:
        - pass_rate: observed success rate for purpose (default 0.7 for cold start).
        - order_prior: cold-start order preference in [0.0, 0.2].
        - latency_penalty: penalize models with avg latency > 180s.
        - failure_rate_penalty: steep penalty on repeated errors.
        """
        n = stats.get("n", 0)
        success_rate = stats.get("success_rate")
        avg_cost = stats.get("avg_cost_usd")
        avg_latency = stats.get("avg_latency_ms")
        
        # Cold-start prior bonus based on documented DEFAULT_REVIEW_ORDER
        order = DEFAULT_REVIEW_ORDER.index(model) if model in DEFAULT_REVIEW_ORDER else 99
        order_bonus = max(0.0, (len(DEFAULT_REVIEW_ORDER) - order) / (len(DEFAULT_REVIEW_ORDER) * 10.0))
        
        if n == 0 or success_rate is None:
            # Unseen model: cold start baseline with order bonus
            return round(0.5 + order_bonus, 6)
            
        failure_rate = 1.0 - success_rate
        base_score = success_rate
        
        # Latency penalty: if latency is approaching the 300s socket limit (> 180s = 180000ms)
        latency_factor = 1.0
        if avg_latency is not None and avg_latency > 180000:
            latency_factor = max(0.5, 1.0 - (avg_latency - 180000) / 240000)
            
        # Cost factor: prefer economical models
        cost_factor = 1.0
        try:
            if avg_cost is not None and float(avg_cost) > 0:
                cost_factor = 1.0 / (1.0 + float(avg_cost) / 0.05)
        except (ValueError, TypeError):
            pass
            
        score = (base_score * 0.6 + cost_factor * 0.25 + order_bonus * 0.15) * latency_factor - (failure_rate * 0.3)
        return round(max(0.0001, score), 6)


class ModelArbiter:
    """Intelligent arbitration and reranking of models for factory roles."""

    def __init__(self, agent_role=None):
        self.agent_role = agent_role
        self.scorer = EmpiricalScorer()

    def arbitrate(self, candidates, purpose, statistics, task_context=None, hindsight_memories=None):
        """Select the optimal model among candidates.
        
        Returns: (selected_model, decision_metadata)
        """
        if not candidates:
            raise ValueError("no_candidates_for_arbitration")
            
        # 1. Compute empirical scores for all candidates
        empirical_scores = {}
        for m in candidates:
            stats = statistics.get(m, {})
            empirical_scores[m] = self.scorer.calculate_score(m, stats, purpose=purpose, task_context=task_context)
            
        # 2. Check if Flue-Pi Tier-1 LLM reranker is available and appropriate
        # In Tier-1 (flue-just-bash), the agent receives candidate metrics + Hindsight memories
        rerank_result = None
        if self.agent_role is not None and task_context and not task_context.get("synthetic"):
            try:
                rerank_result = self._agent_rerank(candidates, purpose, empirical_scores, statistics,
                                                   task_context, hindsight_memories)
            except Exception:
                # Strict fail-closed: fall back to empirical scores on any agent failure
                rerank_result = None

        if rerank_result and rerank_result.get("selected") in candidates:
            selected = rerank_result["selected"]
            basis = "intelligent_agent_reranked"
            decision_meta = {
                "basis": basis,
                "purpose": purpose,
                "model": selected,
                "complexity": rerank_result.get("complexity", "standard"),
                "rationale": rerank_result.get("rationale", ""),
                "scores": empirical_scores,
                "ranking": rerank_result.get("ranking", candidates),
            }
        else:
            # Highest empirical score wins (with model name tiebreaker for determinism)
            selected = max(candidates, key=lambda m: (empirical_scores[m], m))
            basis = "empirical_multi_factor"
            decision_meta = {
                "basis": basis,
                "purpose": purpose,
                "model": selected,
                "scores": empirical_scores,
                "samples": {m: statistics.get(m, {}).get("n", 0) for m in candidates},
            }
            
        return selected, decision_meta

    def _agent_rerank(self, candidates, purpose, empirical_scores, statistics, task_context, hindsight_memories):
        """Prompt a lightweight Tier-1 agent to classify task difficulty and rerank models."""
        memories_summary = ""
        if hindsight_memories:
            items = hindsight_memories[:3]
            memories_summary = "\nHistorical lessons from Hindsight:\n" + "\n".join(
                f"- {item.get('text', '')[:200]}" for item in items
            )
            
        prompt = (
            f"You are the Æion Factory Model Arbiter (Tier-1 Classifier & Reranker).\n"
            f"Task: {task_context.get('title', 'Unknown task')} (Purpose: {purpose})\n"
            f"Write scopes: {task_context.get('write_scopes', [])}\n"
            f"{memories_summary}\n\n"
            f"Candidate Models & Metrics:\n"
        )
        for m in candidates:
            stats = statistics.get(m, {})
            score = empirical_scores[m]
            prompt += (f"  * {m}: score={score}, n={stats.get('n', 0)}, "
                       f"pass_rate={stats.get('success_rate')}, avg_cost=${stats.get('avg_cost_usd')}\n")
                       
        prompt += (
            "\nAnalyze task difficulty and output JSON ONLY with schema:\n"
            '{"complexity": "LOW"|"MEDIUM"|"HIGH", "ranking": ["model1", "model2", ...], "selected": "model1", "rationale": "..."}'
        )
        
        # Invoke agent role with timeout bound (5 seconds max)
        response_text = self.agent_role(prompt, timeout=5)
        parsed = json.loads(re.search(r"\{.*\}", response_text, re.DOTALL).group(0))
        if "selected" in parsed and parsed["selected"] in candidates:
            return parsed
        return None
