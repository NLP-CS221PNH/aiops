import os
import json
import hashlib

def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES_DIR = os.path.join(BASE_DIR, "tests", "fixtures", "demo")
os.makedirs(FIXTURES_DIR, exist_ok=True)

# 1. fixture:case_01_success (GH Redis)
# Incident: inc_0f782051d78bc07a
def create_fixture_01():
    run_dir = os.path.join(FIXTURES_DIR, "run_gh_redis")
    os.makedirs(run_dir, exist_ok=True)
    
    context_items = [
        {
            "evidence_id": "know_redis_manifest_01",
            "source_kind": "doc",
            "document_id": "KBH-D057-0ad6299a6f1d",
            "chunk_id": "KBC-D057-6e2368f1d4cff56ab472ce58",
            "text": "redis Kubernetes manifest\n\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: redis-cart\nspec:\n  template:\n    spec:\n      containers:\n      - name: redis\n        resources:\n          limits:\n            memory: 256Mi\n            cpu: 125m\n          requests:\n            cpu: 70m\n            memory: 200Mi\n        volumeMounts:\n        - mountPath: /data\n          name: redis-data",
            "start_codepoint": 0,
            "end_codepoint": 380,
            "source_revision": "80bea9bfd97bec107361d4663e207aa8d3f312c6",
            "rank": 1
        },
        {
            "evidence_id": "know_redis_tuning_02",
            "source_kind": "doc",
            "document_id": "KBH-D057-0df08c03749a",
            "chunk_id": "KBC-D057-50dfee9359a0fb8b0f8fcce4",
            "text": "Redis persistence and socket configuration:\nWhen cart service experiences rapid session churn, appendonly fsync can saturate IOPS limits if redis-data volume exceeds disk throughput thresholds.",
            "start_codepoint": 0,
            "end_codepoint": 195,
            "source_revision": "80bea9bfd97bec107361d4663e207aa8d3f312c6",
            "rank": 2
        }
    ]
    
    ctx_raw = json.dumps(context_items, indent=2)
    ctx_hash = compute_sha256(ctx_raw)
    with open(os.path.join(run_dir, "context.jsonl"), "w", encoding="utf-8") as f:
        for item in context_items:
            f.write(json.dumps(item) + "\n")
            
    payload = {
        "incident_id": "inc_0f782051d78bc07a",
        "candidate_causes": [
            {
                "service_id": "redis",
                "fault_type": "diskio_saturation",
                "reason": "Redis cartridge disk IO saturation leading to socket backlog and cascading latency to recommendationservice."
            }
        ],
        "supported_claims": [
            {
                "claim_id": "claim_01",
                "text": "Redis deployment defines a 256Mi memory limit and mounts /data volume on redis-data emptyDir.",
                "type": "observation",
                "evidence_ids": ["know_redis_manifest_01"]
            },
            {
                "claim_id": "claim_02",
                "text": "Disk IO saturation during high write spikes on redis-data causes socket timeouts for callers.",
                "type": "inference",
                "evidence_ids": ["know_redis_tuning_02"]
            }
        ],
        "missing_information": [
            "Current IOPS utilization metrics on node storage volume"
        ],
        "next_checks": [
            "Inspect redis pod iostat logs",
            "Check cartservice connection retry backoff metrics"
        ],
        "abstain": False,
        "confidence_label": "high"
    }
    
    raw_response = json.dumps(payload, indent=2)
    record = {
        "raw_response": raw_response,
        "parsed_payload": payload,
        "actual_context_ids": ["know_redis_manifest_01", "know_redis_tuning_02"],
        "actual_context_hash": ctx_hash,
        "model_requested": "fixture-model-v1",
        "model_returned": "fixture-model-v1",
        "provider_epoch": "1",
        "status": "success",
        "error": None,
        "attempts": 1,
        "usage": {"prompt_tokens": 420, "completion_tokens": 160},
        "UTC": "2026-09-13T10:15:00Z",
        "request_id": "run_gh_redis_inc_0f782051d78bc07a"
    }
    
    with open(os.path.join(run_dir, "responses.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        
    manifest = {
        "cohort": "run_gh_redis",
        "condition": "GH",
        "config_hash": "cfg_hash_gh_redis_fixture",
        "planned": 1,
        "attempted": 1,
        "failed": 0,
        "stopped": 0,
        "source_snapshot_hash": ctx_hash
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

# 2. fixture:case_02_weak_diagnosis (GB Email)
# Incident: inc_08457c0fbff4700e
def create_fixture_02():
    run_dir = os.path.join(FIXTURES_DIR, "run_gb_email")
    os.makedirs(run_dir, exist_ok=True)
    
    context_items = [
        {
            "evidence_id": "know_generic_service_01",
            "source_kind": "doc",
            "document_id": "KBH-D057-generic",
            "chunk_id": "KBC-D057-gen01",
            "text": "General microservices overview: Emailservice receives notification requests from checkoutservice and sends confirmation emails asynchronously.",
            "start_codepoint": 0,
            "end_codepoint": 140,
            "source_revision": "80bea9bfd97bec107361d4663e207aa8d3f312c6",
            "rank": 1
        }
    ]
    ctx_raw = json.dumps(context_items, indent=2)
    ctx_hash = compute_sha256(ctx_raw)
    with open(os.path.join(run_dir, "context.jsonl"), "w", encoding="utf-8") as f:
        for item in context_items:
            f.write(json.dumps(item) + "\n")
            
    payload = {
        "incident_id": "inc_08457c0fbff4700e",
        "candidate_causes": [
            {
                "service_id": "emailservice",
                "fault_type": "cpu_spike_suspect",
                "reason": "BM25 retrieved only general high-level service description; CPU/diskio anomaly detected in observation metrics but lacking specific queue configuration."
            }
        ],
        "supported_claims": [
            {
                "claim_id": "claim_weak_01",
                "text": "Emailservice processes notification events asynchronously from checkout.",
                "type": "observation",
                "evidence_ids": ["know_generic_service_01"]
            }
        ],
        "missing_information": [
            "Detailed thread pool configuration for email worker",
            "SMTP socket timeout metrics and spool directory stats"
        ],
        "next_checks": [
            "Examine email worker spool queue depth",
            "Verify thread dump for lock contention"
        ],
        "abstain": False,
        "confidence_label": "low"
    }
    
    raw_response = json.dumps(payload, indent=2)
    record = {
        "raw_response": raw_response,
        "parsed_payload": payload,
        "actual_context_ids": ["know_generic_service_01"],
        "actual_context_hash": ctx_hash,
        "model_requested": "fixture-model-v1",
        "model_returned": "fixture-model-v1",
        "provider_epoch": "1",
        "status": "weak_diagnosis",
        "error": "Low diagnostic confidence due to insufficient specific knowledge retrieval (BM25 only)",
        "attempts": 1,
        "usage": {"prompt_tokens": 280, "completion_tokens": 140},
        "UTC": "2026-09-13T10:20:00Z",
        "request_id": "run_gb_email_inc_08457c0fbff4700e"
    }
    with open(os.path.join(run_dir, "responses.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        
    manifest = {
        "cohort": "run_gb_email",
        "condition": "GB",
        "config_hash": "cfg_hash_gb_email_fixture",
        "planned": 1,
        "attempted": 1,
        "failed": 0,
        "stopped": 0,
        "source_snapshot_hash": ctx_hash
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

# 3. fixture:case_03_missing_evidence (G0 Recommendation)
# Incident: inc_00f82e5883a2163d
def create_fixture_03():
    run_dir = os.path.join(FIXTURES_DIR, "run_g0_recommendation")
    os.makedirs(run_dir, exist_ok=True)
    
    context_items = []
    ctx_hash = compute_sha256("[]")
    with open(os.path.join(run_dir, "context.jsonl"), "w", encoding="utf-8") as f:
        pass
        
    payload = {
        "incident_id": "inc_00f82e5883a2163d",
        "candidate_causes": [],
        "supported_claims": [],
        "missing_information": [
            "No domain knowledge or architecture documentation provided (Condition G0 baseline)",
            "Observed recommendationservice latency-90 spike without internal grpc pool telemetry"
        ],
        "next_checks": [
            "Retrieve knowledge chunks for recommendationservice GRPC and productcatalog socket limits",
            "Inspect productcatalogservice connection timeouts"
        ],
        "abstain": True,
        "confidence_label": "abstain"
    }
    raw_response = json.dumps(payload, indent=2)
    record = {
        "raw_response": raw_response,
        "parsed_payload": payload,
        "actual_context_ids": [],
        "actual_context_hash": ctx_hash,
        "model_requested": "fixture-model-v1",
        "model_returned": "fixture-model-v1",
        "provider_epoch": "1",
        "status": "abstained",
        "error": None,
        "attempts": 1,
        "usage": {"prompt_tokens": 150, "completion_tokens": 90},
        "UTC": "2026-09-13T10:25:00Z",
        "request_id": "run_g0_rec_inc_00f82e5883a2163d"
    }
    with open(os.path.join(run_dir, "responses.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        
    manifest = {
        "cohort": "run_g0_recommendation",
        "condition": "G0",
        "config_hash": "cfg_hash_g0_rec_fixture",
        "planned": 1,
        "attempted": 1,
        "failed": 0,
        "stopped": 0,
        "source_snapshot_hash": ctx_hash
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

# 4. fixture:case_04_invalid_citation (GD Checkout)
# Incident: inc_0991de462f9a6c05
def create_fixture_04():
    run_dir = os.path.join(FIXTURES_DIR, "run_gd_invalid_citation")
    os.makedirs(run_dir, exist_ok=True)
    
    context_items = [
        {
            "evidence_id": "know_valid_checkout_01",
            "source_kind": "doc",
            "document_id": "KBH-D057-checkout",
            "chunk_id": "KBC-D057-chk01",
            "text": "Checkoutservice interacts with paymentservice, emailservice, and cartservice to complete purchase orders.",
            "start_codepoint": 0,
            "end_codepoint": 110,
            "source_revision": "80bea9bfd97bec107361d4663e207aa8d3f312c6",
            "rank": 1
        }
    ]
    ctx_raw = json.dumps(context_items, indent=2)
    ctx_hash = compute_sha256(ctx_raw)
    with open(os.path.join(run_dir, "context.jsonl"), "w", encoding="utf-8") as f:
        for item in context_items:
            f.write(json.dumps(item) + "\n")
            
    raw_payload_str = json.dumps({
        "incident_id": "inc_0991de462f9a6c05",
        "candidate_causes": [
            {
                "service_id": "checkoutservice",
                "fault_type": "memory_leak",
                "reason": "Checkout service memory escalation causes socket drops."
            }
        ],
        "supported_claims": [
            {
                "claim_id": "claim_invalid_01",
                "text": "The service connects to third party payment gateway at https://external-bank.com/api",
                "type": "inference",
                "evidence_ids": ["hallucinated_evidence_external_99"]
            }
        ],
        "missing_information": [],
        "next_checks": [],
        "abstain": False,
        "confidence_label": "high"
    }, indent=2)
    
    record = {
        "raw_response": raw_payload_str,
        "parsed_payload": None,
        "actual_context_ids": ["know_valid_checkout_01"],
        "actual_context_hash": ctx_hash,
        "model_requested": "fixture-model-v1",
        "model_returned": "fixture-model-v1",
        "provider_epoch": "1",
        "status": "invalid_citation",
        "error": "Citation hallucinated_evidence_external_99 not found in actual context",
        "attempts": 1,
        "usage": {"prompt_tokens": 310, "completion_tokens": 120},
        "UTC": "2026-09-13T10:30:00Z",
        "request_id": "run_gd_inv_inc_0991de462f9a6c05"
    }
    with open(os.path.join(run_dir, "responses.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        
    manifest = {
        "cohort": "run_gd_invalid_citation",
        "condition": "GD",
        "config_hash": "cfg_hash_gd_inv_fixture",
        "planned": 1,
        "attempted": 1,
        "failed": 1,
        "stopped": 0,
        "source_snapshot_hash": ctx_hash
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

# 5. fixture:case_05_compare_gb_redis (for comparison with case 01 GH Redis)
# Incident: inc_0f782051d78bc07a
def create_fixture_05():
    run_dir = os.path.join(FIXTURES_DIR, "run_gb_redis")
    os.makedirs(run_dir, exist_ok=True)
    
    context_items = [
        {
            "evidence_id": "know_redis_bm25_generic",
            "source_kind": "doc",
            "document_id": "KBH-D057-generic",
            "chunk_id": "KBC-D057-redis-bm25",
            "text": "Redis cache container deployment notes: Redis is used as in-memory data store for cart items.",
            "start_codepoint": 0,
            "end_codepoint": 95,
            "source_revision": "80bea9bfd97bec107361d4663e207aa8d3f312c6",
            "rank": 1
        }
    ]
    ctx_raw = json.dumps(context_items, indent=2)
    ctx_hash = compute_sha256(ctx_raw)
    with open(os.path.join(run_dir, "context.jsonl"), "w", encoding="utf-8") as f:
        for item in context_items:
            f.write(json.dumps(item) + "\n")
            
    payload = {
        "incident_id": "inc_0f782051d78bc07a",
        "candidate_causes": [
            {
                "service_id": "redis",
                "fault_type": "suspected_overload",
                "reason": "Redis cache has high latency observed, but BM25 retrieval did not return specific IO/resource configuration limits."
            }
        ],
        "supported_claims": [
            {
                "claim_id": "claim_gb_01",
                "text": "Redis is used as in-memory cache for shopping cart.",
                "type": "observation",
                "evidence_ids": ["know_redis_bm25_generic"]
            }
        ],
        "missing_information": [
            "Volume mount config and IOPS saturation details"
        ],
        "next_checks": [
            "Run disk throughput benchmarks"
        ],
        "abstain": False,
        "confidence_label": "medium"
    }
    raw_response = json.dumps(payload, indent=2)
    record = {
        "raw_response": raw_response,
        "parsed_payload": payload,
        "actual_context_ids": ["know_redis_bm25_generic"],
        "actual_context_hash": ctx_hash,
        "model_requested": "fixture-model-v1",
        "model_returned": "fixture-model-v1",
        "provider_epoch": "1",
        "status": "success",
        "error": None,
        "attempts": 1,
        "usage": {"prompt_tokens": 250, "completion_tokens": 110},
        "UTC": "2026-09-13T10:14:00Z",
        "request_id": "run_gb_redis_inc_0f782051d78bc07a"
    }
    with open(os.path.join(run_dir, "responses.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        
    manifest = {
        "cohort": "run_gb_redis",
        "condition": "GB",
        "config_hash": "cfg_hash_gb_redis_fixture",
        "planned": 1,
        "attempted": 1,
        "failed": 0,
        "stopped": 0,
        "source_snapshot_hash": ctx_hash
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    create_fixture_01()
    create_fixture_02()
    create_fixture_03()
    create_fixture_04()
    create_fixture_05()
    print("All demo fixtures created successfully.")
