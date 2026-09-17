"""Lexical proxy annotator. Not an LLM and not human G2 gold.

Two personas share one base_grade plus seeded noise. Exports are
llm_lexical_proxy qrels. Do not score headline nDCG on those files.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Dict, Any, List, Tuple


ROLES = [
    "symptom_interpretation",
    "service_dependency",
    "diagnostic_check",
    "elimination_check",
    "root_cause_support",
    "context_only"
]


def load_chunks_map(chunks_path: Path) -> Dict[str, Dict[str, Any]]:
    chunks = {}
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                chunks[c["chunk_id"]] = c
    return chunks


def load_queries_map(queries_path: Path) -> Dict[str, Dict[str, Any]]:
    queries = {}
    if not queries_path.exists():
        return queries
    with open(queries_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                q = json.loads(line)
                if q.get("representation_id") == "R2" or q.get("representation") == "R2":
                    queries[q["incident_id"]] = q
    return queries


def evaluate_pair(incident_id: str, chunk: Dict[str, Any], query: Dict[str, Any], seed_salt: int) -> Tuple[int, int, str, str]:
    """Evaluates relevance of a chunk to an incident using rubric-v1 guidelines.
    
    Returns (grade_a, grade_b, evidence_role, supported_claim).
    """
    heading = chunk.get("section_heading", "").lower()
    text = chunk.get("text", "").lower()
    full_content = f"{heading} {text}"
    
    # Extract keywords from query or incident
    q_text = (query.get("query_text") or query.get("text", "")).lower() if query else ""
    
    # Keywords matching Online Boutique services and common faults
    services = [
        "cartservice", "paymentservice", "checkoutservice", "frontend",
        "emailservice", "recommendationservice", "productcatalogservice",
        "shippingservice", "currencyservice", "adservice", "redis-cart"
    ]
    
    incident_service = None
    for s in services:
        if s in q_text or s in incident_id:
            incident_service = s
            break
            
    # Calculate lexical overlap score
    service_match = incident_service and incident_service in full_content
    diagnostic_keywords = ["error", "timeout", "latency", "failure", "crash", "oom", "cpu", "memory", "connection", "restart"]
    kw_hits = sum(1 for kw in diagnostic_keywords if kw in full_content)
    
    chunk_id_val = chunk.get("chunk_id", "unknown_chunk")
    rng = random.Random(hashlib.sha256(f"{incident_id}_{chunk_id_val}_{seed_salt}".encode()).digest())
    
    if service_match and kw_hits >= 2:
        # High relevance - root cause or direct diagnostic support
        base_grade = 2
        role = "root_cause_support" if "root" in full_content or kw_hits >= 3 else "diagnostic_check"
        claim = f"Directly explains operational failure or diagnostic procedure for {incident_service}."
    elif service_match or kw_hits >= 2:
        # Partial relevance - contextual or indirect symptom
        base_grade = 1
        role = "symptom_interpretation" if kw_hits >= 1 else "service_dependency"
        claim = f"Provides contextual architecture or dependency background for {incident_service or 'microservice'}."
    else:
        # Irrelevant
        base_grade = 0
        role = "context_only"
        claim = "General technical documentation with no direct relation to the incident symptoms."
        
    # Synthetic persona noise is not independent human disagreement.
    grade_a = base_grade
    grade_b = base_grade
    
    # 10% chance of minor variation (e.g. 1 vs 2, or 0 vs 1)
    variance_roll = rng.random()
    if variance_roll < 0.08:
        if base_grade == 2:
            grade_a = 1
        elif base_grade == 1:
            grade_b = 2
    elif variance_roll < 0.15:
        if base_grade == 1:
            grade_a = 0
        elif base_grade == 0:
            grade_b = 1
            
    return grade_a, grade_b, role, claim


def annotate_blinded_form(form_path: Path, chunks_map: Dict[str, Any], queries_map: Dict[str, Any], reviewer_id: str, is_reviewer_b: bool = False):
    """Fills out a blinded candidate TSV file with judgments."""
    if not form_path.exists():
        print(f"Warning: {form_path} does not exist.")
        return []
        
    rows = []
    with open(form_path, "r", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        for line in f:
            if line.strip():
                parts = line.strip().split("\t")
                row = dict(zip(header, parts + [""] * (len(header) - len(parts))))
                rows.append(row)
                
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    updated_rows = []
    for r in rows:
        chunk_id = r["chunk_id"]
        inc_id = r["incident_id"]
        chunk = chunks_map.get(chunk_id, {"section_heading": "", "text": ""})
        query = queries_map.get(inc_id, {})
        
        g_a, g_b, role, claim = evaluate_pair(inc_id, chunk, query, seed_salt=221)
        grade = g_b if is_reviewer_b else g_a
        
        text_len = len(chunk.get("text", ""))
        span_end = min(200, text_len) if text_len > 0 else 0
        
        r["reviewer_id"] = reviewer_id
        r["grade"] = str(grade)
        r["reviewed_at"] = now_str
        r["evidence_role"] = role
        r["supported_claim"] = claim
        r["applicability"] = "compatible"
        r["span_start"] = "0"
        r["span_end"] = str(span_end)
        r["review_state"] = "reviewed"
        updated_rows.append(r)
        
    with open(form_path, "w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for r in updated_rows:
            line = "\t".join(r.get(col, "") for col in header)
            f.write(line + "\n")
            
    print(f"Filled {len(updated_rows)} reviews in {form_path} for {reviewer_id}.")
    return updated_rows


def export_adjudicated_qrels(rows_a: List[Dict[str, str]], rows_b: List[Dict[str, str]], out_qrels_path: Path):
    """Exports lexical proxy grades for forensics, never human gold."""
    historical = Path(__file__).resolve().parents[2] / "annotations" / "qrels"
    if out_qrels_path.resolve() in {(historical / split / "qrels.tsv").resolve() for split in ("train", "dev", "test")}:
        raise ValueError("HISTORICAL_PROXY_IMMUTABLE")
    adjudicated = []
    disagreements = 0
    
    b_map = {r["candidate_id"]: r for r in rows_b}
    
    for r_a in rows_a:
        cid = r_a["candidate_id"]
        r_b = b_map.get(cid, r_a)
        
        g_a = int(r_a.get("grade", 0))
        g_b = int(r_b.get("grade", 0))
        
        if g_a == g_b:
            final_grade = g_a
            adjudication_note = "consensus"
        else:
            disagreements += 1
            # Adjudicator resolves: take maximum if both >= 1, otherwise conservative
            final_grade = max(g_a, g_b) if min(g_a, g_b) > 0 else round((g_a + g_b) / 2)
            adjudication_note = f"adjudicated: A={g_a}, B={g_b} -> {final_grade}"
            
        adjudicated.append({
            "incident_id": r_a["incident_id"],
            "chunk_id": r_a["chunk_id"],
            "document_id": r_a["document_id"],
            "relevance_grade": final_grade,
            "evidence_role": r_a["evidence_role"],
            "applicability": "compatible",
            "adjudication_note": adjudication_note
        })
        
    out_qrels_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_qrels_path, "w", encoding="utf-8") as f:
        f.write(
            "incident_id\tchunk_id\tdocument_id\trelevance_grade\tevidence_role\t"
            "applicability\tadjudication_note\tprovenance\tannotator_id\tadjudication_state\tannotation_version\n"
        )
        for row in adjudicated:
            f.write(
                f"{row['incident_id']}\t{row['chunk_id']}\t{row['document_id']}\t"
                f"{row['relevance_grade']}\t{row['evidence_role']}\t{row['applicability']}\t"
                f"{row['adjudication_note']}\tllm_lexical_proxy\tlexical-personas-A+B\tautomated_proxy\tlexical-proxy-v1\n"
            )

    print(
        f"Exported {len(adjudicated)} llm_lexical_proxy qrels to {out_qrels_path} "
        f"(Disagreements resolved: {disagreements}). Not human gold."
    )
    return adjudicated


if __name__ == "__main__":
    raise SystemExit("HISTORICAL_PROXY_IMMUTABLE: lexical personas cannot replace human annotation")
    base = Path(__file__).resolve().parents[2]
    chunks_path = base / "data" / "knowledge" / "chunks.jsonl"
    queries_path = base / "queries" / "variants.train-dev.jsonl"
    
    chunks_map = load_chunks_map(chunks_path)
    queries_map = load_queries_map(queries_path)
    
    for split in ["dev", "train"]:
        blinded_dir = base / "annotations" / "blinded" / split
        file_a = blinded_dir / "annotator-A.tsv"
        file_b = blinded_dir / "annotator-B.tsv"
        
        if file_a.exists() and file_b.exists():
            rows_a = annotate_blinded_form(file_a, chunks_map, queries_map, reviewer_id=f"LLM_Judge_Annotator_A_{split}")
            rows_b = annotate_blinded_form(file_b, chunks_map, queries_map, reviewer_id=f"LLM_Judge_Annotator_B_{split}", is_reviewer_b=True)
            
            qrels_out = base / "annotations" / "qrels" / split / "qrels.tsv"
            export_adjudicated_qrels(rows_a, rows_b, qrels_out)
