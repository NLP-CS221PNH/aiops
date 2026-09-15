"""Acquire a fixed, passive knowledge snapshot; never execute downloaded content.

Run with Python stdlib. Network access is required only for missing immutable files.
The default is a frozen 2026 offline-reference corpus, not a historical triage claim.
"""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "03_collection_plan" / "knowledge-corpus"
RAW = OUT / "raw" / "source-snapshots"
TRANSFORM = "source-markdown-preserve-v1"
CHUNKER = "heading-char-window-2400-overlap-240-v1"
SNAPSHOT_ID = "cs221-knowledge-2026-09-12-v1"
DOCUMENT_PREFIX = "KB"
EXPERIMENT_POLICY = "offline_frozen_reference_no_historical_simulation_claim"
REPOS = {
    "D057": {"repo": "GoogleCloudPlatform/microservices-demo", "revision": "b9a978db9e01f4ad3dca9494a22cb9edc17548fe", "snapshot_commit_time": "2026-09-03T21:10:06Z", "license": "Apache-2.0", "attribution": "Google LLC and GoogleCloudPlatform/microservices-demo contributors", "system_scope": "Online Boutique upstream application; RCAEval deployment match unverified"},
    "D058": {"repo": "kubernetes/website", "revision": "76a0e90f253e924a7b55f01f92a37555bd89be68", "snapshot_commit_time": "2026-09-12T03:59:12Z", "license": "CC-BY-4.0", "attribution": "The Kubernetes Authors and kubernetes/website contributors", "system_scope": "Kubernetes platform troubleshooting; RCAEval cluster version unverified"},
    "D059": {"repo": "prometheus-operator/runbooks", "revision": "a685d14cf5128bb30e2bf935c3983decd772d885", "snapshot_commit_time": "2024-10-03T13:27:07Z", "license": "Apache-2.0", "attribution": "prometheus-operator/runbooks contributors", "system_scope": "Prometheus Operator alerts and Kubernetes/node runbooks; deployed alert rules unverified"},
}
OB_DOCS = ["README.md", "docs/development-guide.md", "docs/product-requirements.md", "docs/purpose.md", "kubernetes-manifests/README.md", "src/adservice/README.md", "src/checkoutservice/README.md", "src/frontend/README.md", "src/productcatalogservice/README.md", "src/shippingservice/README.md", "kustomize/components/network-policies/README.md", "kustomize/components/google-cloud-operations/README.md", "protos/demo.proto"]
K8S_DOCS = [
    "content/en/docs/tasks/debug/debug-application/_index.md",
    "content/en/docs/tasks/debug/debug-application/debug-init-containers.md",
    "content/en/docs/tasks/debug/debug-application/debug-pods.md",
    "content/en/docs/tasks/debug/debug-application/debug-running-pod.md",
    "content/en/docs/tasks/debug/debug-application/debug-service.md",
    "content/en/docs/tasks/debug/debug-application/determine-reason-pod-failure.md",
    "content/en/docs/tasks/debug/debug-cluster/_index.md",
    "content/en/docs/tasks/debug/debug-cluster/monitor-node-health.md",
    "content/en/docs/tasks/debug/debug-cluster/resource-metrics-pipeline.md",
    "content/en/docs/tasks/debug/debug-cluster/resource-usage-monitoring.md",
    "content/en/docs/concepts/configuration/manage-resources-containers.md",
    "content/en/docs/tasks/administer-cluster/dns-debugging-resolution.md",
    "content/en/docs/concepts/workloads/pods/pod-lifecycle.md",
    "content/en/docs/concepts/cluster-administration/logging.md",
]
RUNBOOK_NAMES = {
    "CPUThrottlingHigh", "KubeContainerWaiting", "KubeDeploymentReplicasMismatch",
    "KubeDeploymentGenerationMismatch", "KubeHpaMaxedOut", "KubeHpaReplicasMismatch",
    "KubeMemoryOvercommit", "KubeMemoryQuotaOvercommit", "KubeCPUOvercommit",
    "KubeNodeNotReady", "KubeNodeUnreachable", "KubeNodeReadinessFlapping",
    "KubePersistentVolumeErrors", "KubePersistentVolumeFillingUp",
    "KubePodCrashLooping", "KubePodNotReady", "KubeletDown",
    "KubeletPodStartUpLatencyHigh", "KubeQuotaExceeded", "TargetDown",
    "NodeNetworkReceiveErrs", "NodeNetworkTransmitErrs", "NodeFilesystemSpaceFillingUp",
    "NodeFilesystemAlmostOutOfSpace", "NodeFileDescriptorLimit",
    "NodeHighNumberConntrackEntriesUsed", "NodeNetworkInterfaceFlapping",
    "PrometheusNotIngestingSamples", "PrometheusTargetSyncFailure",
    "PrometheusRuleFailures", "PrometheusBadConfig", "PrometheusDuplicateTimestamps",
    "PrometheusOutOfOrderTimestamps", "PrometheusLabelLimitHit", "PrometheusTargetLimitHit",
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def acquire(url, path):
    """Cache bytes with retrieval provenance; reuse immutable cache on re-run."""
    receipt_path = path.with_name(path.name + ".receipt.json")
    if path.exists() and receipt_path.exists():
        data = path.read_bytes()
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt["url"] != url or receipt["sha256"] != sha256(data):
            raise ValueError(f"Cache provenance mismatch: {path}")
        return data, receipt
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CS221-AIOps-RAG-Research-Acquisition/1.0", "Accept": "application/vnd.github+json" if "api.github.com" in url else "*/*"})
            with urllib.request.urlopen(req, timeout=45) as response:
                data = response.read()
                receipt = {"url": url, "retrieved_at": now(), "sha256": sha256(data), "bytes": len(data), "http_status": response.status, "etag": response.headers.get("ETag"), "last_modified_http": response.headers.get("Last-Modified"), "http_last_modified_is_content_publication_time": False}
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            return data, receipt
        except (urllib.error.URLError, TimeoutError) as error:
            if isinstance(error, urllib.error.HTTPError) and error.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def title_for(text, path):
    match = re.search(r'^title:\s*["\']?([^\r\n"\']+)', text, re.M)
    if match:
        return match.group(1).strip()
    match = re.search(r"^#\s+(.+)$", text, re.M)
    return match.group(1).strip() if match else path


def chunk_document(doc):
    text = doc["text"]
    headings = [(m.start(), m.group(1).strip()) for m in re.finditer(r"^#{1,6}\s+(.+)$", text, re.M)]
    boundaries = sorted(set([0, len(text)] + [p for p, _ in headings]))
    index = 0
    for start, end in zip(boundaries, boundaries[1:]):
        pos = start
        while pos < end:
            stop = min(pos + 2400, end)
            if stop < end:
                newline = text.rfind("\n", pos + 1200, stop)
                if newline > pos:
                    stop = newline + 1
            content = text[pos:stop]
            heading = next((h for p, h in reversed(headings) if p <= pos), doc["title"])
            if content.strip():
                index += 1
                yield {"chunk_id": f'{doc["document_id"]}-C{index:04d}', "parent_document_id": doc["document_id"], "start_offset": pos, "end_offset": stop, "offset_unit": "unicode_codepoint_in_document_text", "section_heading": heading, "text": content, "text_hash": sha256(content.encode("utf-8")), "token_count": None, "token_estimate_chars_div_4": (len(content) + 3) // 4, "transform_version": TRANSFORM, "chunker_version": CHUNKER, "source_id": doc["source_id"], "source_url": doc["source_url"], "license": doc["license"], "available_at": doc["available_at"], "version_compatibility": "unverified", "review_state": "needs_human_review"}
            if stop == end:
                break
            pos = max(pos + 1, stop - 240)


def tags_for(doc):
    key = (doc["source_path"] + " " + doc["title"]).lower()
    rules = {
        "cpu_pressure_or_throttling": ["cpu", "manage-resources"],
        "memory_pressure_or_oom": ["memory", "manage-resources", "pod-lifecycle"],
        "pod_crash_restart_or_not_ready": ["crash", "podnotready", "pod-lifecycle", "debug-pods", "pod-failure"],
        "network_dns_or_service_unreachable": ["network", "dns", "debug-service", "targetdown", "conntrack"],
        "node_health": ["node", "kubelet"],
        "storage_or_filesystem_pressure": ["volume", "filesystem"],
        "metrics_collection_or_alert_config": ["prometheus", "metrics", "monitor", "google-cloud-operations"],
        "deployment_or_container_start": ["deployment", "containerwaiting", "init-container", "kubernetes-manifests"],
        "application_architecture_or_rpc_contract": ["demo.proto", "development-guide", "product-requirements", "purpose"],
    }
    result = [tag for tag, needles in rules.items() if any(needle in key for needle in needles)]
    if doc["source_id"] == "D057" and doc["source_path"] == "README.md":
        result.append("application_architecture_or_rpc_contract")
    return result or ["general_operational_reference"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifests, jobs, extras = [], [], []
    source_paths = {}
    for sid, source in REPOS.items():
        repo, revision = source["repo"], source["revision"]
        base = RAW / sid
        api = f"https://api.github.com/repos/{repo}"
        tree_data, tree_receipt = acquire(f"{api}/git/trees/{revision}?recursive=1", base / "repository-tree.json")
        tree = json.loads(tree_data)
        if tree.get("truncated"):
            raise ValueError(f"Repository tree truncated: {sid}")
        paths = {row["path"] for row in tree["tree"] if row["type"] == "blob"}
        source_paths[sid] = paths
        commit_data, commit_receipt = acquire(f"{api}/commits/{revision}", base / "commit.json")
        commit = json.loads(commit_data)
        if commit["sha"] != revision or commit["commit"]["committer"]["date"] != source["snapshot_commit_time"]:
            raise ValueError(f"Commit metadata mismatch: {sid}")
        license_url = f"https://raw.githubusercontent.com/{repo}/{revision}/LICENSE"
        license_data, license_receipt = acquire(license_url, base / "LICENSE")
        marker = b"Attribution 4.0 International" if source["license"] == "CC-BY-4.0" else b"Apache License"
        if marker not in license_data:
            raise ValueError(f"License marker mismatch: {sid}")
        notice_paths = [p for p in paths if p.upper() in {"NOTICE", "NOTICE.TXT", "NOTICE.MD"}]
        for notice in notice_paths:
            acquire(f"https://raw.githubusercontent.com/{repo}/{revision}/{notice}", base / notice)
        if sid == "D057":
            selected = OB_DOCS + sorted(p for p in paths if p.startswith("kubernetes-manifests/") and p.endswith(".yaml") and not p.endswith("kustomization.yaml"))
        elif sid == "D058":
            selected = K8S_DOCS
        else:
            selected = sorted(p for p in paths if p.startswith("content/runbooks/") and Path(p).stem in RUNBOOK_NAMES)
            found = {Path(p).stem for p in selected}
            if found != RUNBOOK_NAMES:
                raise ValueError(f"Missing selected runbooks: {RUNBOOK_NAMES - found}")
        for path in selected:
            if path not in paths:
                raise ValueError(f"Missing source path: {sid}:{path}")
            jobs.append((sid, path))
        manifests.append({"source_id": sid, "official_url": f"https://github.com/{repo}", "canonical_release_url": f"https://github.com/{repo}/tree/{revision}", "release_revision": revision, "snapshot_commit_time": source["snapshot_commit_time"], "retrieved_at": commit_receipt["retrieved_at"], "published_at": None, "updated_at": None, "available_at": source["snapshot_commit_time"], "availability_basis": "conservative_repository_snapshot_commit_time_not_document_publication", "license_data": source["license"], "license_code": source["license"] if sid != "D058" else "not_assessed_for_code_outside_selected_documentation", "license_evidence_url": f"https://github.com/{repo}/blob/{revision}/LICENSE", "license_snapshot_path": str((base / "LICENSE").relative_to(ROOT)).replace("\\", "/"), "license_snapshot_hash": sha256(license_data), "license_retrieved_at": license_receipt["retrieved_at"], "attribution": source["attribution"], "selected_file_count": len(selected), "scope_notes": source["system_scope"], "access_state": "downloaded_and_hash_verified", "upstream_source_ids": [], "allowed_processing": "local_copy_normalization_chunking_with_attribution_license_and_change_notice", "redistribution_conditions": "retain_license_source_attribution_and_change_notice; no rights assumed for external_linked_assets_or_trademarks", "notice_files_found": notice_paths, "version_compatibility": "unverified", "default_experiment_policy": EXPERIMENT_POLICY, "selected_paths": selected})

    def download_one(job):
        sid, path = job
        source = REPOS[sid]
        url = f'https://raw.githubusercontent.com/{source["repo"]}/{source["revision"]}/{path}'
        data, receipt = acquire(url, RAW / sid / "files" / path)
        return sid, path, data, receipt

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        acquired = list(executor.map(download_one, jobs))
    # Preserve example fragments referenced by Hugo instead of implying the
    # source Markdown is a fully rendered, self-contained page.
    dependencies = {}
    for sid, path, data, receipt in acquired:
        content = data.decode("utf-8-sig")
        refs = []
        if sid == "D058":
            refs += ["content/en/examples/" + x for x in re.findall(r'code_sample\s+file="([^"]+)"', content)]
            refs += ["content/en/includes/" + x for x in re.findall(r'include\s+"([^"]+)"', content)]
        if sid == "D057" and path == "README.md":
            refs.append("docs/img/architecture-diagram.png")
        for ref in refs:
            if ref not in source_paths[sid]:
                matches = [candidate for candidate in source_paths[sid] if candidate.endswith("/" + ref.split("/")[-1]) and (candidate.startswith("content/en/") or sid == "D057")]
                if len(matches) == 1:
                    ref = matches[0]
                else:
                    raise ValueError(f"Cannot resolve supporting fragment {sid}:{ref}")
            dependencies.setdefault((sid, ref), []).append(path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        supports = list(executor.map(download_one, dependencies))
    for sid, path, data, receipt in supports:
        source = REPOS[sid]
        extras.append({"source_id": sid, "source_path": path, "raw_path": str((RAW / sid / "files" / path).relative_to(ROOT)).replace("\\", "/"), "source_url": f'https://github.com/{source["repo"]}/blob/{source["revision"]}/{path}', "sha256": sha256(data), "bytes": len(data), "retrieved_at": receipt["retrieved_at"], "release_revision": source["revision"], "repository_license": source["license"], "referenced_by_source_paths": dependencies[(sid, path)], "role": "supporting_source_fragment_or_architecture_asset_not_separate_retrieval_document", "execution_performed": False})
    write_jsonl(OUT / "supporting-assets.jsonl", extras)
    docs = []
    for sid, path, data, receipt in acquired:
        source = REPOS[sid]
        text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        did = f'{DOCUMENT_PREFIX}-{sid}-{sha256(path.encode("utf-8"))[:12]}'
        docs.append({"document_id": did, "source_id": sid, "source_url": f'https://github.com/{source["repo"]}/blob/{source["revision"]}/{path}', "download_url": receipt["url"], "source_path": path, "raw_path": str((RAW / sid / "files" / path).relative_to(ROOT)).replace("\\", "/"), "title": title_for(text, path), "text": text, "raw_sha256": sha256(data), "text_hash": sha256(text.encode("utf-8")), "bytes": len(data), "characters": len(text), "published_at": None, "updated_at": None, "available_at": source["snapshot_commit_time"], "availability_basis": "conservative_repository_snapshot_commit_time_not_document_publication", "retrieved_at": receipt["retrieved_at"], "system_scope": source["system_scope"], "version_scope": source["revision"], "upstream_application_release": None, "version_compatibility": "unverified", "license": source["license"], "license_evidence_url": f'https://github.com/{source["repo"]}/blob/{source["revision"]}/LICENSE', "attribution": source["attribution"], "document_kind": "application_configuration_reference" if path.endswith((".yaml", ".proto")) else ("alert_runbook" if sid == "D059" else "technical_documentation"), "derived_from_incident_ids": [], "is_synthetic": False, "transform_version": TRANSFORM, "change_notice": "Original source retained; UTF-8 decoded and newlines normalized for document text. Markdown/Hugo directives preserved; chunks are derived slices.", "rendering_state": "source_markdown_not_rendered" if path.endswith(".md") else "source_text", "hugo_directive_count": len(re.findall(r"\{\{[<%]", text)), "review_state": "needs_human_review"})
    docs.sort(key=lambda d: d["document_id"])
    chunks = [chunk for doc in docs for chunk in chunk_document(doc)]
    for chunk in chunks:
        doc = next(d for d in docs if d["document_id"] == chunk["parent_document_id"])
        assert chunk["text"] == doc["text"][chunk["start_offset"]:chunk["end_offset"]]
    write_jsonl(OUT / "source-manifest.jsonl", manifests)
    write_jsonl(OUT / "documents.jsonl", docs)
    write_jsonl(OUT / "chunks.jsonl", chunks)
    mappings = []
    for doc in docs:
        service_match = re.search(r"(?:src/|kubernetes-manifests/)([a-z]+service|frontend|loadgenerator)", doc["source_path"])
        service = service_match.group(1) if service_match else ("application_wide" if doc["source_id"] == "D057" else "platform_generic")
        for symptom in tags_for(doc):
            mappings.append({"mapping_id": f'MAP-{len(mappings)+1:04d}', "document_id": doc["document_id"], "source_id": doc["source_id"], "service_scope": service, "symptom_family": symptom, "mapping_basis": "rule_based_path_title_candidate_not_incident_evidence", "review_state": "needs_human_review", "is_gold_qrel": False, "relevance_grade": None, "version_compatibility": "unverified"})
    write_jsonl(OUT / "proposed-mappings.jsonl", mappings)
    with (OUT / "proposed-mappings.tsv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(mappings[0]), delimiter="\t")
        writer.writeheader(); writer.writerows(mappings)
    hashes = {name: sha256((OUT / name).read_bytes()) for name in ["source-manifest.jsonl", "documents.jsonl", "chunks.jsonl", "proposed-mappings.jsonl", "supporting-assets.jsonl"]}
    report = {"snapshot_id": SNAPSHOT_ID, "created_at": now(), "document_count": len(docs), "chunk_count": len(chunks), "mapping_candidate_count": len(mappings), "supporting_asset_count": len(extras), "source_counts": {sid: sum(d["source_id"] == sid for d in docs) for sid in REPOS}, "raw_document_bytes": sum(d["bytes"] for d in docs), "all_chunk_offsets_verified": True, "exact_text_duplicate_groups": [[d["document_id"] for d in docs if d["text_hash"] == h] for h in sorted({d["text_hash"] for d in docs}) if sum(d["text_hash"] == h for d in docs) > 1], "human_review_completed": False, "incident_coverage_measured": False, "historical_compatibility_verified": False, "hashes": hashes}
    (OUT / "snapshot.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
