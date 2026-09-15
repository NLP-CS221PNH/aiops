#!/usr/bin/env python3
"""Offline historical source census; no writes unless --output-dir is supplied.

This prepares proposals, never human approvals or a released corpus. It reads
only the historical source allowlist, its raw receipts and repository metadata.
It neither opens incident labels/proposed mappings nor imports acquisition code.

Library API: audit_sources(root) -> (report, source_registry, applicability).
CLI: python 06_implementation/scripts/audit_corpus_sources.py
     python 06_implementation/scripts/audit_corpus_sources.py --output-dir
         06_implementation/data/knowledge-preparation --report-dir
         06_implementation/reports
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

VERSION = "historical-source-census-v1"
PROPOSAL_VERSION = "applicability-proposal-v1"
HISTORICAL = Path("03_collection_plan/knowledge-corpus-historical")
PREPARATION = Path("06_implementation/data/knowledge-preparation")
REPORTS = Path("06_implementation/reports")
EXPECTED_COUNTS = {"D057": 25, "D058": 14, "D059": 35}
PINNED_INPUTS = {
    "snapshot.json": "4859942b21898a0fd70ca85ebc12639b717299c1c18a19aa5f6b33dfd2351103",
    "source-manifest.jsonl": "f8f768a8ee87b25d414a954fd0b0998d167bb91c5c3f5483cdff1c23ede07391",
    "documents.jsonl": "b8373b3087de3933b6dfee2ab0aa28db6df14485f7bda913360be3a19d409ab3",
    "chunks.jsonl": "1f6c1c28f5f7bcab926509595dda5d5400600c0ea773fdb23eb09d1849a6d8ca",
    "supporting-assets.jsonl": "4a277721a0c5bc3db40cc8456e194d00b40025e941b193e71b1043cd66a68f78",
}
PINNED_SOURCES = {
    "D057": ("GoogleCloudPlatform/microservices-demo", "80bea9bfd97bec107361d4663e207aa8d3f312c6", "Apache-2.0"),
    "D058": ("kubernetes/website", "7e631d0318dc279cb2d31231d8823360e61e9304", "CC-BY-4.0"),
    "D059": ("prometheus-operator/runbooks", "f8061f3e9b3337d90107aa2f10a0111f3f6dc86f", "Apache-2.0"),
}

# These are source-scope proposals, not incident judgments. Every row remains
# pending for A to review and B to check; none asserts deployment compatibility.
EXCLUSIONS = {
    ("D057", "docs/purpose.md"): "Project purpose and contributor prioritization; no operational diagnosis or configuration reference.",
    ("D057", "docs/product-requirements.md"): "Requirements for demo simplicity and contributor changes; not incident troubleshooting evidence.",
    ("D057", "src/frontend/README.md"): "Only a local dependency vendoring command; no service behavior or diagnostic content.",
    ("D057", "src/checkoutservice/README.md"): "Only a local dependency vendoring command; no service behavior or diagnostic content.",
    ("D058", "content/en/docs/tasks/debug/debug-application/_index.md"): "Troubleshooting collection introduction only; the specific diagnostic pages are separate sources.",
    ("D059", "content/runbooks/prometheus/PrometheusOutOfOrderTimestamps.md"): "A title and external blog link only; linked content was not acquired or licensed as a local source.",
    ("D059", "content/runbooks/prometheus/PrometheusNotIngestingSamples.md"): "Brief missing-metrics description with TODO diagnosis and mitigation; no completed diagnostic procedure.",
}
D057_SCOPES = {
    "README.md": ("Upstream application overview, service table and deployment instructions", "Verify the deployed application revision, service names and enabled optional components; upstream architecture is a reference hypothesis."),
    "docs/development-guide.md": ("Local Skaffold build and development deployment workflow", "Verify a source-built deployment and compatible Skaffold/Docker/kubectl versions before using development steps."),
    "kubernetes-manifests/README.md": ("Explicit warning that source manifests require Skaffold image substitution", "Use as a qualification on source YAML; these files do not establish the deployed images or directly deployable release."),
    "src/adservice/README.md": ("Ad service context-key behavior and local Gradle/Docker build instructions", "Verify matching adservice implementation; local build commands are development context, not incident evidence."),
    "src/shippingservice/README.md": ("Shipping quote/tracking behavior plus local build and test instructions", "Verify matching shippingservice implementation and RPC behavior before applying the interface description."),
    "src/productcatalogservice/README.md": ("Optional dynamic catalog reloading and an artificial delay described by the upstream service", "Require deployed feature/environment configuration and observed behavior; do not infer this optional delay is active or caused an incident."),
    "kustomize/components/network-policies/README.md": ("Optional NetworkPolicy component and network enforcement setup", "Require the applied NetworkPolicy objects and an enforcing CNI; policy support or denial cannot be inferred from the upstream component."),
    "kustomize/components/google-cloud-operations/README.md": ("Optional Google Cloud Operations instrumentation, explicitly disabled by default", "Require evidence that the component, tracing/metrics environment options and collector are enabled; do not assume telemetry exists."),
    "protos/demo.proto": ("Upstream protobuf service/RPC and message definitions", "Require matching deployed proto/application revision before asserting an RPC edge or message contract."),
}
D058_SCOPES = {
    "debug-init-containers.md": ("Inspect init-container state, events and logs", "Verify init containers exist and kubectl/API permissions; check version-specific syntax."),
    "debug-pods.md": ("Inspect pending, waiting and crashing Pods", "Require the observed Pod state/events; treat listed causes as hypotheses to verify."),
    "debug-running-pod.md": ("Inspect running Pod resources, logs and debug containers", "Verify Kubernetes version, runtime support and debug permissions; ephemeral container steps have feature/version requirements."),
    "debug-service.md": ("Check Service reachability, endpoints, selectors and network routing", "Verify Service type, endpoints, proxy/CNI mode, DNS setup and permissions before selecting a branch."),
    "determine-reason-pod-failure.md": ("Read container termination state and termination messages", "Require actual Pod/container termination records; tutorial examples are not observations."),
    "_index.md": ("Cluster troubleshooting workflow for nodes and control-plane components", "Verify the cluster topology, provider, control-plane access and version; local examples do not identify the deployed stack."),
    "monitor-node-health.md": ("Node Problem Detector setup and node health monitoring", "Require evidence Node Problem Detector is deployed and its configured problem daemons/events are available."),
    "resource-metrics-pipeline.md": ("Kubelet, Metrics Server and the resource metrics API pipeline", "Verify Metrics Server/API availability, kubelet configuration and versions before interpreting resource metrics."),
    "resource-usage-monitoring.md": ("Monitoring approaches and full metrics pipeline overview", "Verify the selected monitoring backend, exporters and retention; a list of tools does not prove their deployment."),
    "manage-resources-containers.md": ("Container CPU/memory/storage requests, limits and enforcement", "Verify Pod requests/limits, scheduler/runtime/cgroup behavior and feature gates; version-specific storage features require evidence."),
    "dns-debugging-resolution.md": ("Inspect DNS resolver, DNS Pods, Service and CoreDNS configuration", "Require the deployed DNS provider, resolver configuration and Service endpoints; CoreDNS-specific steps are conditional."),
    "pod-lifecycle.md": ("Pod phases, container states, readiness and termination behavior", "Verify Kubernetes/runtime version and enabled features; sidecars, readiness gates and alpha/beta behaviors need configuration proof."),
    "logging.md": ("Container/node logs, kubelet rotation and logging architectures", "Verify runtime, kubelet log settings, agents and backend; sample sidecar manifests do not prove the logging deployment."),
}
RUNBOOK_PRECONDITIONS = {
    "CPUThrottlingHigh": "Require measured throttling plus application impairment and actual alert rules; source calls the alert informative and inhibited by default, so throttling alone is not a cause.",
    "TargetDown": "Require actual scrape targets, endpoint/selector/network configuration and matching alert rules; scrape failure does not establish application outage.",
    "KubeHpaMaxedOut": "Require a deployed HPA, its maxReplicas, requests and metric source; reaching the maximum can be intentional.",
    "KubeHpaReplicasMismatch": "Require a deployed HPA, desired/current replicas, scheduling capacity and resource quotas.",
    "KubePersistentVolumeErrors": "Require a bound/provisioning PersistentVolume and provider events; the upstream application redis example uses emptyDir, not proof of a PV.",
    "KubePersistentVolumeFillingUp": "Require a PersistentVolume, observed filesystem usage and service retention policy; this source explicitly does not diagnose application-specific filling causes.",
    "KubeCPUOvercommit": "Require aggregate CPU requests, node capacity and node failure tolerance assumptions; overcommit is not measured CPU saturation.",
    "KubeMemoryOvercommit": "Require aggregate memory requests and node capacity/failure tolerance; requests are not measured memory use.",
    "KubeMemoryQuotaOvercommit": "Require actual namespace memory quotas, requests and available capacity.",
    "KubeQuotaExceeded": "Require the affected namespace ResourceQuota hard limits and time-aligned usage.",
    "KubeDeploymentGenerationMismatch": "Require a Deployment generation/observedGeneration and rollout history; mismatch does not by itself prove rollback.",
    "KubeDeploymentReplicasMismatch": "Require the Deployment desired/available replicas, scheduling events and workload constraints.",
    "KubeContainerWaiting": "Require the actual container Waiting reason, Pod events and referenced configuration/volumes.",
    "KubePodCrashLooping": "Require actual restarts, termination reasons, probes, logs and resource configuration; listed causes remain hypotheses.",
    "KubePodNotReady": "Require Pod conditions, readiness probes, events and endpoint membership.",
    "KubeNodeNotReady": "Require observed node Ready condition, events and matching node identity.",
    "KubeNodeReadinessFlapping": "Require a time series of node Ready transitions and matching rule window; the source example uses a different alert name.",
    "KubeNodeUnreachable": "Require observed node reachability/status and events; distinguish control-plane network loss from node failure.",
    "KubeletDown": "Require actual kubelet scrape endpoints and node status; monitoring network failure can mimic kubelet outage.",
    "KubeletPodStartUpLatencyHigh": "Require matching startup-latency metrics and node storage observations; the source has an unresolved XX-seconds placeholder and a conditional IOPS suggestion.",
    "NodeFileDescriptorLimit": "Require Linux node descriptor limits/usage and permissions; source oc debug commands require OpenShift or an independently validated equivalent.",
    "NodeFilesystemAlmostOutOfSpace": "Require the mounted filesystem, free-space metrics and actual alert thresholds; thresholds in the source are not observed deployment settings.",
    "NodeFilesystemSpaceFillingUp": "Require mount identity, usage time series and the actual prediction rule/window; source forecasts are not incident observations.",
    "NodeHighNumberConntrackEntriesUsed": "Require node conntrack usage/limit and relevant network namespace; do not assume a conntrack bottleneck from service traffic alone.",
    "NodeNetworkReceiveErrs": "Require interface identity, receive-error counters and network/hardware observations.",
    "NodeNetworkTransmitErrs": "Require interface identity, transmit-error counters, saturation and node resource observations.",
    "NodeNetworkInterfaceFlapping": "Require observed interface state transitions and relevant node/interface identity.",
    "PrometheusBadConfig": "Require deployed Prometheus/Operator versions, reload logs and rendered configuration/monitor objects.",
    "PrometheusDuplicateTimestamps": "Require duplicate-timestamp ingestion errors, actual scrape labels and target configuration.",
    "PrometheusLabelLimitHit": "Require matching Prometheus label limits and dropped-target evidence; Diagnosis is empty and the short mitigation is not a validated remedy.",
    "PrometheusRuleFailures": "Require the deployed rule expression and evaluation error; use as telemetry/rule debugging, not an application root-cause assertion.",
    "PrometheusTargetLimitHit": "Require matching scrape target limits and dropped-target evidence; Diagnosis is empty and the short mitigation is not a validated remedy.",
    "PrometheusTargetSyncFailure": "Require actual Prometheus sync errors and namespace; source oc commands require OpenShift or a separately verified equivalent.",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def iso_time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp must have a UTC offset")
    return result.astimezone(timezone.utc)


def safe_source_path(root: Path, relative: str) -> Path:
    """Resolve only paths within the immutable historical source tree."""
    target = (root / relative).resolve()
    if not target.is_relative_to((root / HISTORICAL).resolve()):
        raise ValueError(f"Source path escapes historical allowlist: {relative}")
    return target


def evidence_span(doc: dict) -> dict:
    text = doc["text"]
    if doc["source_path"].endswith(".yaml"):
        start = text.find("apiVersion:")
    elif doc["source_path"].endswith(".proto"):
        start = text.find('syntax =')
    else:
        start = 0
        if text.startswith("---\n"):
            closing = text.find("\n---", 4)
            if closing >= 0:
                start = closing + 4
        # Keep a source excerpt and its exact codepoint span, never rewrite text.
        while start < len(text) and text[start].isspace():
            start += 1
    start = max(0, start)
    end = min(len(text), start + 600)
    return {"document_id": doc["document_id"], "offset_unit": "unicode_codepoint_in_source_document_text",
            "start_offset": start, "end_offset": end, "text_sha256": sha256(text[start:end].encode("utf-8")),
            "document_text_sha256": doc["text_hash"]}


def proposal_for(doc: dict, integrity_errors: list[str]) -> dict:
    sid, path = doc["source_id"], doc["source_path"]
    excluded_reason = EXCLUSIONS.get((sid, path))
    decision = "excluded" if excluded_reason else "unknown"
    if excluded_reason:
        reason, condition, role = excluded_reason, "Retain in source registry; excluded from candidate retrieval pending A/B review.", "non_operational_or_incomplete_source"
    elif sid == "D057":
        if path.endswith(".yaml"):
            stem = PurePosixPath(path).stem
            kinds = sorted(set(re.findall(r"^kind:\s*(.+)$", doc["text"], re.M)))
            reason = f"Upstream {stem} configuration defines {'/'.join(kinds)} objects; deployed release/configuration match is unverified."
            condition = "Require deployed workload/configuration evidence before using ports, dependencies, image names or resource values as facts; source manifests require Skaffold image substitution."
            role = "upstream_configuration_reference"
        else:
            reason, condition = D057_SCOPES[path]
            reason += "; deployed implementation/configuration match is unverified."
            role = "upstream_interface_reference" if path.endswith(".proto") else "application_reference"
    elif sid == "D058":
        reason, condition = D058_SCOPES[PurePosixPath(path).name]
        reason += "; cluster/version compatibility is unverified."
        role = "conditional_platform_diagnostic_reference"
    else:
        name = PurePosixPath(path).stem
        reason = f"The {name} runbook describes an alert/diagnostic scenario; deployed rules, telemetry and scenario occurrence are unverified."
        condition = RUNBOOK_PRECONDITIONS[name]
        role = "conditional_monitoring_diagnostic_reference" if "/prometheus/" in path else "conditional_infrastructure_diagnostic_reference"
    if integrity_errors:
        decision = "excluded"
        reason = "Quarantined by source integrity failures: " + "; ".join(integrity_errors)
        condition = "Do not index until the source integrity evidence is corrected and reviewed."
    span = evidence_span(doc)
    return {
        "document_id": doc["document_id"], "source_id": sid, "source_path": path,
        "decision": decision, "reason": reason, "review_state": "pending",
        "reviewer": "", "reviewed_at": "", "owner": "A", "check_owner": "B",
        "check_reviewer": "", "check_reviewed_at": "", "decision_version": PROPOSAL_VERSION,
        "decision_origin": "codex_proposal_not_human_review",
        "allowed_experiment_mode": "excluded" if decision == "excluded" else "candidate_conditional",
        "app_version": "unknown", "platform_version": "unknown", "deployment_compatibility": "unknown",
        "config_preconditions": condition, "evidence_role": role,
        "conditional_use": "No use until required review/release gates. For a locally authorized candidate, use only as a conditional diagnostic/reference hypothesis; never claim compatibility, causal relevance or an observed incident fact.",
        "evidence_ids": [doc["document_id"], doc["raw_path"], doc["raw_path"] + ".receipt.json"],
        "source_evidence_span": span, "source_revision": doc["version_scope"],
        "source_url": doc["source_url"], "raw_sha256": doc["raw_sha256"], "text_hash": doc["text_hash"],
        "available_at": doc["available_at"], "availability_basis": doc["availability_basis"],
        "retrieved_at": doc["retrieved_at"], "published_at": doc["published_at"], "updated_at": doc["updated_at"],
        "deployment_evidence_ids": [], "is_qrel": False,
    }


def audit_sources(root: Path | str | None = None) -> tuple[dict, list[dict], list[dict]]:
    root = Path(root or Path(__file__).resolve().parents[2]).resolve()
    findings, evidence = [], []
    check_count = 0

    def check(condition, code, context=""):
        nonlocal check_count
        check_count += 1
        if not condition:
            findings.append({"severity": "error", "code": code, "context": context})

    def read_file(relative, expected_hash=None, role="source"):
        target = safe_source_path(root, relative)
        data = target.read_bytes()
        digest = sha256(data)
        evidence.append({"path": str(relative).replace("\\", "/"), "sha256": digest, "bytes": len(data), "role": role,
                         "expected_sha256": expected_hash, "hash_matches": digest == expected_hash if expected_hash else None})
        if expected_hash:
            check(digest == expected_hash, "sha256_mismatch", str(relative))
        return data

    def read_receipted(relative, expected_hash=None, expected_url=None, expected_time=None, role="raw_document"):
        data = read_file(relative, expected_hash, role)
        receipt_path = str(relative) + ".receipt.json"
        receipt = json.loads(read_file(receipt_path, role="acquisition_receipt"))
        check(sha256(data) == receipt.get("sha256"), "receipt_sha256_mismatch", str(relative))
        check(len(data) == receipt.get("bytes"), "receipt_size_mismatch", str(relative))
        check(receipt.get("http_status") == 200, "receipt_http_status", str(relative))
        check(receipt.get("http_last_modified_is_content_publication_time") is False, "receipt_publication_time_conflation", str(relative))
        if expected_url:
            check(receipt.get("url") == expected_url, "receipt_url_mismatch", str(relative))
        if expected_time:
            check(receipt.get("retrieved_at") == expected_time, "receipt_retrieved_at_mismatch", str(relative))
        iso_time(receipt["retrieved_at"])
        return data, receipt

    inputs = {name: read_file((HISTORICAL / name).as_posix(), digest, "snapshot_contract") for name, digest in PINNED_INPUTS.items()}
    snapshot = json.loads(inputs["snapshot.json"])
    sources = [json.loads(line) for line in inputs["source-manifest.jsonl"].splitlines() if line.strip()]
    docs = [json.loads(line) for line in inputs["documents.jsonl"].splitlines() if line.strip()]
    chunks = [json.loads(line) for line in inputs["chunks.jsonl"].splitlines() if line.strip()]
    assets = [json.loads(line) for line in inputs["supporting-assets.jsonl"].splitlines() if line.strip()]
    source_map = {source["source_id"]: source for source in sources}
    doc_map = {doc["document_id"]: doc for doc in docs}
    check(set(source_map) == set(EXPECTED_COUNTS), "source_whitelist")
    check(len(sources) == len(source_map) == 3, "source_ids_not_unique")
    check(len(docs) == len(doc_map) == snapshot["document_count"] == 74, "document_count_or_duplicate_id")
    check(len(assets) == snapshot["supporting_asset_count"] == 12, "asset_count")
    check(len(chunks) == snapshot["chunk_count"] == 580, "source_chunk_count")
    check(dict(Counter(d["source_id"] for d in docs)) == EXPECTED_COUNTS == snapshot["source_counts"], "document_source_counts")
    check(sum(doc["bytes"] for doc in docs) == snapshot["raw_document_bytes"], "raw_document_total_bytes")
    check(snapshot["snapshot_id"] == "cs221-knowledge-pre2024-v1", "snapshot_id")
    for name in PINNED_INPUTS:
        if name != "snapshot.json":
            check(sha256(inputs[name]) == snapshot["hashes"][name], "snapshot_hash_contract", name)

    trees = {}
    for source in sources:
        sid = source["source_id"]
        repo, revision, license_id = PINNED_SOURCES[sid]
        check(source["release_revision"] == revision, "source_revision", sid)
        check(source["official_url"] == f"https://github.com/{repo}", "official_source_url", sid)
        check(source["canonical_release_url"] == f"https://github.com/{repo}/tree/{revision}", "source_release_url", sid)
        check(source["license_evidence_url"] == f"https://github.com/{repo}/blob/{revision}/LICENSE", "license_url", sid)
        check(source["license_data"] == license_id and bool(source["attribution"]), "license_or_attribution_metadata", sid)
        check(source["available_at"] == source["snapshot_commit_time"], "availability_basis_time", sid)
        check(source["availability_basis"] == "conservative_repository_snapshot_commit_time_not_document_publication", "availability_basis", sid)
        check(iso_time(source["available_at"]) < iso_time("2024-01-01T00:00:00Z") < iso_time(source["retrieved_at"]), "historical_time_order", sid)
        check(source["published_at"] is None and source["updated_at"] is None, "unknown_publication_times_preserved", sid)
        check(source["version_compatibility"] == "unverified", "unsupported_compatibility_claim", sid)
        base = (HISTORICAL / "raw/source-snapshots" / sid).as_posix()
        check(source["license_snapshot_path"] == base + "/LICENSE", "license_snapshot_path", sid)
        license_bytes, _ = read_receipted(source["license_snapshot_path"], source["license_snapshot_hash"],
                                         f"https://raw.githubusercontent.com/{repo}/{revision}/LICENSE",
                                         source["license_retrieved_at"], "license")
        check(bool(license_bytes.strip()), "empty_license", sid)
        commit_data, _ = read_receipted(base + "/commit.json", expected_url=f"https://api.github.com/repos/{repo}/commits/{revision}",
                                       expected_time=source["retrieved_at"], role="commit_metadata")
        commit = json.loads(commit_data)
        check(commit["sha"] == revision and commit["commit"]["committer"]["date"] == source["snapshot_commit_time"], "commit_metadata_contract", sid)
        tree_data, _ = read_receipted(base + "/repository-tree.json", expected_url=f"https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1", role="repository_tree")
        tree = json.loads(tree_data)
        check(tree.get("truncated") is False, "repository_tree_truncated", sid)
        # These saved API responses echo the requested commit in top-level sha.
        # Bind the actual root tree to commit metadata from its direct entries.
        check(tree["sha"] in (revision, commit["commit"]["tree"]["sha"]), "repository_tree_revision", sid)
        root_entries = [item for item in tree["tree"] if "/" not in item["path"]]
        root_entries.sort(key=lambda item: (item["path"] + ("/" if item["type"] == "tree" else "")).encode("utf-8"))
        root_bytes = b"".join(item["mode"].lstrip("0").encode("ascii") + b" " + item["path"].encode("utf-8") + b"\0" + bytes.fromhex(item["sha"]) for item in root_entries)
        root_hash = hashlib.sha1(b"tree " + str(len(root_bytes)).encode("ascii") + b"\0" + root_bytes).hexdigest()
        check(root_hash == commit["commit"]["tree"]["sha"], "repository_root_tree_commit_mismatch", sid)
        trees[sid] = {item["path"]: item for item in tree["tree"]}
        selected = [d["source_path"] for d in docs if d["source_id"] == sid]
        check(len(selected) == len(set(selected)) == source["selected_file_count"] == EXPECTED_COUNTS[sid], "source_selected_count", sid)
        check(sorted(selected) == sorted(source["selected_paths"]), "source_selected_paths", sid)

    registry, applicability = [], []
    doc_hashes, chunk_hashes = defaultdict(list), defaultdict(list)
    shortcode_counts, shortcode_docs = Counter(), []
    include_refs, source_warnings = [], []
    asset_map = {(asset["source_id"], asset["source_path"]): asset for asset in assets}
    check(len(asset_map) == len(assets), "duplicate_asset_paths")
    for line_number, doc in enumerate(docs, 1):
        before = len(findings)
        sid, path, did = doc["source_id"], doc["source_path"], doc["document_id"]
        source = source_map[sid]
        repo, revision, license_id = PINNED_SOURCES[sid]
        check(did == f"KBH-{sid}-{sha256(path.encode('utf-8'))[:12]}", "source_document_id", did)
        expected_raw = (HISTORICAL / "raw/source-snapshots" / sid / "files" / path).as_posix()
        check(doc["raw_path"] == expected_raw, "raw_document_path", did)
        check(doc["source_url"] == f"https://github.com/{repo}/blob/{revision}/{path}", "document_source_url", did)
        check(doc["download_url"] == f"https://raw.githubusercontent.com/{repo}/{revision}/{path}", "document_download_url", did)
        check(doc["version_scope"] == revision, "document_revision", did)
        check(doc["license"] == license_id and doc["attribution"] == source["attribution"] and doc["license_evidence_url"] == source["license_evidence_url"], "document_license_attribution", did)
        check(doc["available_at"] == source["available_at"] and doc["availability_basis"] == source["availability_basis"], "document_availability", did)
        check(doc["published_at"] is None and doc["updated_at"] is None, "document_unknown_publication_times", did)
        check(iso_time(doc["available_at"]) < iso_time(doc["retrieved_at"]), "document_time_order", did)
        check(doc["version_compatibility"] == "unverified" and doc["upstream_application_release"] is None, "document_compatibility_unknown", did)
        check(doc["derived_from_incident_ids"] == [] and doc["is_synthetic"] is False, "document_incident_or_synthetic_content", did)
        raw, receipt = read_receipted(doc["raw_path"], doc["raw_sha256"], doc["download_url"], doc["retrieved_at"])
        check(len(raw) == doc["bytes"], "raw_document_bytes", did)
        decoded = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        check(decoded == doc["text"], "raw_decoding_contract", did)
        check(sha256(doc["text"].encode("utf-8")) == doc["text_hash"], "document_text_hash", did)
        check(len(doc["text"]) == doc["characters"], "document_character_count", did)
        tree_entry = trees[sid].get(path)
        check(tree_entry is not None and tree_entry["type"] == "blob", "document_not_in_revision_tree", did)
        if tree_entry:
            git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
            check(tree_entry["sha"] == git_blob, "git_blob_hash", did)
        doc_hashes[doc["text_hash"]].append(did)
        tags = list(re.finditer(r"\{\{[<%](.*?)[>%]\}\}", doc["text"], re.S))
        check(len(tags) == doc["hugo_directive_count"], "hugo_directive_count", did)
        if tags:
            shortcode_docs.append({"document_id": did, "source_path": path, "directive_count": len(tags)})
        for tag in tags:
            body = tag.group(1).strip()
            kind = body.split()[0]
            shortcode_counts[kind] += 1
            relative = None
            if kind == "include":
                match = re.search(r'include\s+["\']([^"\']+)["\']', body)
                relative = "content/en/includes/" + match.group(1) if match else None
            elif kind == "code_sample":
                match = re.search(r'file=["\']([^"\']+)["\']', body)
                relative = "content/en/examples/" + match.group(1) if match else None
            if kind in ("include", "code_sample"):
                asset = asset_map.get((sid, relative))
                ref = {"document_id": did, "source_path": path, "directive": kind, "start_offset": tag.start(),
                       "end_offset": tag.end(), "dependency_source_path": relative, "status": "local_pinned_asset" if asset else "missing_local_include",
                       "asset_sha256": asset["sha256"] if asset else None}
                include_refs.append(ref)
                if not asset:
                    source_warnings.append({"code": "missing_local_include", **ref})
                else:
                    check(path in asset["referenced_by_source_paths"], "asset_backreference", did)
        if re.search(r"(?m)^## Diagnosis\s*\n\s*##", doc["text"]):
            source_warnings.append({"code": "empty_diagnosis_section", "document_id": did, "source_path": path})
        if re.search(r"(?m)^TODO\s*$", doc["text"]):
            source_warnings.append({"code": "unfinished_todo_content", "document_id": did, "source_path": path})
        if "XX seconds" in doc["text"]:
            source_warnings.append({"code": "unresolved_threshold_placeholder", "document_id": did, "source_path": path})
        errors = [finding["code"] for finding in findings[before:]]
        registry.append({**{key: value for key, value in doc.items() if key != "text"},
                         "record_type": "historical_source_document", "audit_version": VERSION, "snapshot_id": snapshot["snapshot_id"],
                         "source_document_jsonl_path": (HISTORICAL / "documents.jsonl").as_posix(), "source_document_jsonl_line": line_number,
                         "source_document_jsonl_sha256": PINNED_INPUTS["documents.jsonl"], "source_manifest": source,
                         "raw_receipt_path": doc["raw_path"] + ".receipt.json", "raw_receipt_sha256": evidence[-1]["sha256"],
                         "raw_verified_sha256": sha256(raw), "raw_verified_bytes": len(raw),
                         "source_integrity_state": "verified" if not errors else "quarantined", "integrity_errors": errors})
        applicability.append(proposal_for(doc, errors))

    for asset in assets:
        sid, path = asset["source_id"], asset["source_path"]
        repo, revision, license_id = PINNED_SOURCES[sid]
        check(asset["raw_path"] == (HISTORICAL / "raw/source-snapshots" / sid / "files" / path).as_posix(), "asset_raw_path", path)
        check(asset["source_url"] == f"https://github.com/{repo}/blob/{revision}/{path}", "asset_source_url", path)
        check(asset["release_revision"] == revision and asset["repository_license"] == license_id, "asset_revision_license", path)
        check(asset["execution_performed"] is False, "asset_execution_flag", path)
        raw, _ = read_receipted(asset["raw_path"], asset["sha256"], f"https://raw.githubusercontent.com/{repo}/{revision}/{path}", asset["retrieved_at"], "supporting_asset")
        check(len(raw) == asset["bytes"], "asset_bytes", path)
        check(iso_time(source_map[sid]["available_at"]) < iso_time(asset["retrieved_at"]), "asset_time_order", path)
        tree_entry = trees[sid].get(path)
        check(tree_entry is not None, "asset_not_in_revision_tree", path)
        if tree_entry:
            git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
            check(tree_entry["sha"] == git_blob, "asset_git_blob_hash", path)
        check(all(any(d["source_id"] == sid and d["source_path"] == ref for d in docs) for ref in asset["referenced_by_source_paths"]), "asset_unknown_parent", path)

    short_chunks = []
    check(len({chunk["chunk_id"] for chunk in chunks}) == len(chunks), "duplicate_source_chunk_id")
    for chunk in chunks:
        cid = chunk["chunk_id"]
        doc = doc_map.get(chunk["parent_document_id"])
        check(doc is not None, "source_chunk_unknown_document", cid)
        if doc:
            start, end = chunk["start_offset"], chunk["end_offset"]
            check(0 <= start < end <= len(doc["text"]), "source_chunk_offset_bounds", cid)
            check(doc["text"][start:end] == chunk["text"], "source_chunk_slice", cid)
            check(chunk["source_url"] == doc["source_url"] and chunk["source_id"] == doc["source_id"], "source_chunk_source_lineage", cid)
        check(chunk["offset_unit"] == "unicode_codepoint_in_document_text", "source_chunk_offset_unit", cid)
        check(sha256(chunk["text"].encode("utf-8")) == chunk["text_hash"], "source_chunk_text_hash", cid)
        chunk_hashes[chunk["text_hash"]].append(cid)
        if len(chunk["text"]) <= 40:
            short_chunks.append({"chunk_id": cid, "document_id": chunk["parent_document_id"], "characters": len(chunk["text"]),
                                 "section_heading": chunk["section_heading"], "text_hash": chunk["text_hash"]})

    duplicates = [ids for _, ids in sorted(doc_hashes.items()) if len(ids) > 1]
    check(duplicates == snapshot["exact_text_duplicate_groups"], "snapshot_duplicate_contract")
    # All proposals are review-pending even when a source is structurally excluded.
    check(len(applicability) == 74 and all(row["review_state"] == "pending" and not row["reviewer"] and not row["reviewed_at"] for row in applicability), "proposal_review_state")
    check(all(row["deployment_compatibility"] == "unknown" and row["deployment_evidence_ids"] == [] for row in applicability), "proposal_deployment_unknown")
    proposal_counts = {state: sum(row["decision"] == state for row in applicability) for state in ("allowed", "excluded", "unknown")}
    report = {
        "audit_version": VERSION, "status": "pass" if not findings else "fail", "checks_run": check_count,
        "snapshot_id": snapshot["snapshot_id"], "scope": "offline_historical_source_census_and_unreviewed_applicability_proposals",
        "source_root": HISTORICAL.as_posix(), "counts": {"sources": len(sources), "documents": len(docs), "source_chunks": len(chunks), "supporting_assets": len(assets), "licenses": len(sources), "raw_document_bytes": sum(d["bytes"] for d in docs)},
        "source_counts": dict(sorted(Counter(d["source_id"] for d in docs).items())), "sources": sources,
        "input_evidence": evidence, "findings": findings, "source_content_warnings": source_warnings,
        "applicability": {"decision_version": PROPOSAL_VERSION, "proposal_counts": proposal_counts, "human_reviewed": 0,
                          "review_pending": len(applicability), "deployment_compatibility_unknown": len(applicability),
                          "owner": "A", "check_owner": "B", "is_release_approval": False},
        "normalization_preparation": {
            "copyright_titles": [{"document_id": d["document_id"], "source_path": d["source_path"], "original_title": d["title"]} for d in docs if d["title"].startswith("Copyright")],
            "hugo_directive_counts": dict(sorted(shortcode_counts.items())), "hugo_documents": shortcode_docs,
            "literal_include_references": include_refs, "missing_literal_include_count": sum(ref["status"] == "missing_local_include" for ref in include_refs),
            "dynamic_shortcode_policy": "Source remains unrendered. param/version-check/skew/ref/glossary/figure and wrappers need explicit deterministic handling; do not fetch links or infer current values.",
            "short_source_chunks_lte_40_characters": short_chunks,
            "source_chunks_without_token_count": sum(c["token_count"] is None for c in chunks),
            "exact_document_text_duplicate_groups": duplicates,
            "exact_source_chunk_text_duplicate_groups": [ids for _, ids in sorted(chunk_hashes.items()) if len(ids) > 1],
            "lineage_note": "Original document IDs, raw/text hashes, source offsets and source chunks are retained; this audit creates no normalized documents or replacement chunks.",
        },
        "temporal_audit": {"source_available_before": "2024-01-01T00:00:00Z", "status": "source_commit_dates_verified",
                           "per_incident_cutoff_check": "not_performed_in_source_only_preparation", "deployment_compatibility": "unknown",
                           "note": "available_at is a conservative whole-repository snapshot commit time; retrieved_at is acquisition time. Neither proves per-document publication or deployment compatibility."},
        "license_audit": {"status": "metadata_and_local_license_hashes_verified", "legal_determination": False,
                          "conditions": "Preserve recorded license, attribution, source revision, original notices and derivative change notices; external links/assets have no inferred rights."},
        "source_separation": {"current_corpus_read": False, "incident_labels_read": False, "proposed_mappings_read": False,
                              "downloads_performed": False, "raw_sources_modified": False, "corpus_release_created": False},
        "not_audited": ["proposed-mappings.jsonl (snapshot-declared hash retained only; content not opened)", "per-incident temporal eligibility", "deployment evidence", "legal permission review", "human applicability", "incident coverage or qrel relevance", "tokenizer budgets or derivative chunking"],
    }
    return report, registry, applicability


def render_markdown(report: dict) -> str:
    count = report["counts"]
    prep = report["normalization_preparation"]
    proposal = report["applicability"]
    lines = ["# Historical corpus source census", "", f"Status: **{report['status']}** across {report['checks_run']} offline integrity checks. This is source preparation and an unreviewed proposal, not corpus release approval.", "",
             f"Rehashed {count['documents']} documents, {count['supporting_assets']} supporting assets and {count['licenses']} licenses; verified acquisition receipts, pinned revisions and Git blob identities against local repository trees. Source counts: D057=25, D058=14, D059=35. The existing {count['source_chunks']} chunks were inspected only to prepare normalization.", "",
             "| Source | Documents | Revision | Recorded documentation license |", "|---|---:|---|---|"]
    for source in report["sources"]:
        sid = source["source_id"]
        lines.append(f"| {sid} | {report['source_counts'][sid]} | `{source['release_revision']}` | {source['license_data']} |")
    lines += ["", "License metadata and file hashes were verified; this is not a legal determination. Preserve source attribution, LICENSE, original notices and derivative change notices. No rights are inferred for externally linked material.", "",
              f"Applicability proposals: **{proposal['proposal_counts']['allowed']} allowed, {proposal['proposal_counts']['excluded']} excluded, {proposal['proposal_counts']['unknown']} unknown**. All 74 require A review and B check; reviewer identities and review timestamps are blank. Deployment compatibility stays unknown for all 74. The excluded records remain in the source registry.", "",
              "Unknown sources may support an explicitly authorized local candidate as conditional reference hypotheses subject to the per-document preconditions. The proposals do not establish compatible deployment, incident relevance, causal evidence or human approval. Release remains gated by the project review contracts.", "",
              "## Normalization preparation", "",
              f"- {len(prep['copyright_titles'])} original titles are copyright headings; retain them as original metadata and use a source-path/configuration title for future normalized metadata.",
              f"- {sum(prep['hugo_directive_counts'].values())} Hugo directives appear in {len(prep['hugo_documents'])} documents. {len(prep['literal_include_references'])} include/code_sample occurrences resolve to pinned local assets; missing literal includes: {prep['missing_literal_include_count']}.",
              "- Dynamic shortcodes and external figure/ref/glossary links remain source text. Handle them explicitly without current-value inference, web fetching or execution.",
              f"- {len(prep['short_source_chunks_lte_40_characters'])} source chunks contain at most 40 characters; all {prep['source_chunks_without_token_count']} source token counts are null. Character estimates are not tokenizer validation.",
              f"- Exact document duplicate groups: {len(prep['exact_document_text_duplicate_groups'])}; exact source chunk duplicate groups: {len(prep['exact_source_chunk_text_duplicate_groups'])}. Repeated boilerplate is reported without deleting source evidence.", "",
              "## Content review backlog", "",
              "The proposal excludes project-purpose/product-requirement material, dependency-only frontend/checkout README files, a navigation-only troubleshooting introduction, an external-link-only out-of-order-timestamps stub and a TODO-only ingestion runbook. A/B may revise these decisions with evidence. Prometheus label/target-limit runbooks have empty diagnosis sections; the kubelet startup-latency runbook has an unresolved threshold placeholder.", "",
              "CPUThrottlingHigh explicitly describes an informative alert inhibited by default; it must not establish a cause from the title alone. Google Cloud Operations is explicitly disabled by default. Network policies, HPA, persistent volumes, OpenShift-specific commands and optional platform features require deployed configuration evidence.", "",
              "## Time and source separation", "",
              "All source available_at values match verified repository commit metadata and precede 2024-01-01 UTC. This run does not open incident data or perform per-incident cutoff checks. Per-page published_at/updated_at remain unknown; acquisition timestamps are retained separately. Current corpus text, incident labels and proposed mapping content were not opened. No downloads or raw-source changes were performed.", "",
              "## Reproduction and evidence", "",
              "Run `python 06_implementation/scripts/audit_corpus_sources.py` for read-only validation. Add `--output-dir 06_implementation/data/knowledge-preparation --report-dir 06_implementation/reports` to materialize only the designated derivative files. Output is deterministic, with no timestamp claiming a human review. An existing reviewed applicability file is never overwritten.", "",
              "The JSON report contains every exact input path, byte count and SHA-256, plus all document IDs, shortcode references, short chunks, duplicates and errors. The source registry retains all original non-text document metadata and complete source manifest/license metadata. Applicability rows cite the raw path, receipt and hashed source-text span.", "",
              "| Contract input | SHA-256 |", "|---|---|"]
    for item in report["input_evidence"]:
        if item["role"] == "snapshot_contract":
            lines.append(f"| `{item['path']}` | `{item['sha256']}` |")
    if report["findings"]:
        lines += ["", "## Integrity failures", ""] + [f"- {f['code']}: {f['context']}" for f in report["findings"]]
    return "\n".join(lines) + "\n"


def write_outputs(root: Path, output_dir: Path, report_dir: Path | None, report: dict, registry: list[dict], applicability: list[dict]) -> None:
    output_dir = output_dir.resolve()
    if not output_dir.is_relative_to((root / PREPARATION).resolve()):
        raise ValueError(f"--output-dir must be inside {PREPARATION.as_posix()}")
    if report_dir:
        report_dir = report_dir.resolve()
        if report_dir != (root / REPORTS).resolve() and not report_dir.is_relative_to(output_dir):
            raise ValueError("--report-dir must be the designated implementation reports directory or inside --output-dir")
    target = output_dir / "applicability.tsv"
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            existing = list(csv.DictReader(handle, delimiter="\t"))
        if any(row.get("review_state") != "pending" or row.get("reviewer") or row.get("reviewed_at") or row.get("check_reviewer") or row.get("check_reviewed_at") for row in existing):
            raise ValueError("Refusing to overwrite applicability with existing human review fields")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "source-registry.jsonl").write_bytes(b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8") for row in registry))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(applicability[0]), delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in applicability:
        writer.writerow({key: json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, (dict, list)) else "" if value is None else value for key, value in row.items()})
    target.write_bytes(stream.getvalue().encode("utf-8"))
    if report_dir:
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "corpus-source-audit.json").write_bytes(json_bytes(report))
        (report_dir / "corpus-source-audit.md").write_bytes(render_markdown(report).encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, help="Explicit preparation output; omitted means read only")
    parser.add_argument("--report-dir", type=Path, help="Optional derivative reports output; requires --output-dir")
    args = parser.parse_args()
    if args.report_dir and not args.output_dir:
        parser.error("--report-dir requires --output-dir")
    root = args.root.resolve()
    report, registry, applicability = audit_sources(root)
    if args.output_dir:
        write_outputs(root, root / args.output_dir, root / args.report_dir if args.report_dir else None, report, registry, applicability)
    print(json.dumps({"status": report["status"], "checks_run": report["checks_run"], "counts": report["counts"], "applicability": report["applicability"], "errors": report["findings"], "files_written": bool(args.output_dir)}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
