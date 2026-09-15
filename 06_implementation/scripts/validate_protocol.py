"""Validate the Plan 01 draft and its G0 receipt without changing input files.

Run from any directory: python validate_protocol.py --root PACK_ROOT.
Normal validation accepts a truthful draft; --require-g0 requires valid acceptance.
Human review is the default. Automated acceptance needs explicit user authorization.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit

try:
    import yaml
except ImportError:
    yaml = None


IMPL = "06_implementation"
PROTOCOL = f"{IMPL}/configs/protocol.yaml"
DECISIONS = f"{IMPL}/configs/decisions.json"
MANIFEST = f"{IMPL}/freezes/G0/manifest.json"
DOC = f"{IMPL}/docs/research-protocol.md"
LITERATURE = f"{IMPL}/docs/literature-matrix.tsv"
AUTH = f"{IMPL}/configs/acceptance-authorization.json"
REVIEW = f"{IMPL}/reports/plan01-autonomous-review.json"
AMENDMENT = f"{IMPL}/docs/acceptance-amendment.md"
AUTO_SCOPES = {"data_boundary", "design_metrics", "resources_handoff", "literature"}
PENDING_PERMISSIONS = {"api": "pending", "api_payload": "pending", "local_model": "pending", "data_sharing": "pending", "budget_usd": None}
SPLIT = "02_datasets/processed/split-map.tsv"
ANNOTATION = "03_collection_plan/annotation-kit/status.json"
ROLES = {"A", "B", "C"}
PERMISSION_KEYS = {"api", "api_payload", "local_model", "data_sharing", "budget_usd"}
METRIC_CONTRACT = {
    "primary_metric": "passage_ndcg_at_5",
    "primary_selection": "stronger_dev_single",
    "tie_break": "BM25",
    "required_conditions": ["G0", "GB", "GD", "GH"],
    "optional_conditions": ["GR"],
    "test_tuning": False,
    "qrels_core": {"train": 20, "dev": 18, "test": 18},
    "unjudged_is_zero": False,
    "no_relevant_policy": "undefined_report_separately",
    "freeze_sequence": ["F1", "test_input", "test_pool", "F2", "test_scoring"],
}
REQUIRED_ARTIFACTS = {
    PROTOCOL, DECISIONS, DOC,
    f"{IMPL}/docs/project-charter.md",
    f"{IMPL}/docs/decision-log.md",
    f"{IMPL}/docs/literature-matrix.tsv",
    f"{IMPL}/docs/team-working-agreement.md",
    f"{IMPL}/docs/instructor-questions-draft.md",
    f"{IMPL}/docs/protocol-review.md",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def utc_timestamp(value) -> bool:
    if not nonempty(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0
    except ValueError:
        return False


def human_name(value) -> bool:
    if not nonempty(value):
        return False
    normalized = value.strip().casefold()
    return normalized not in {"a", "b", "c", "tbd", "pending", "unknown", "null"} and not re.search(
        r"codex|chatgpt|assistant|agent|placeholder|<|>", normalized
    )


class Validator:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.errors = []
        self.blockers = []
        self.warnings = []
        self.protocol = {}
        self.manifest = {}
        self.decisions = []

    def error(self, code, location, message):
        self.errors.append({"code": code, "location": location, "message": message})

    def block(self, code, location, message):
        self.blockers.append({"code": code, "location": location, "message": message})

    def check(self, condition, code, location, message):
        if not condition:
            self.error(code, location, message)
        return bool(condition)

    def safe_path(self, value, location):
        # Reject Windows drives, backslashes, traversal and links outside the pack.
        if not nonempty(value):
            self.error("unsafe_path", location, "Expected a nonempty root-relative POSIX path.")
            return None
        parts = PurePosixPath(value).parts
        if value.startswith("/") or "\\" in value or ":" in value or ".." in parts or not parts:
            self.error("unsafe_path", location, "Absolute or traversing paths are forbidden.")
            return None
        path = (self.root / value).resolve()
        if not path.is_relative_to(self.root):
            self.error("unsafe_path", location, "Resolved path escapes the pack root.")
            return None
        if not path.is_file():
            self.error("missing_file", location, f"File not found: {value}")
            return None
        return path

    def load(self, relative, kind="json"):
        path = self.safe_path(relative, relative)
        if path is None:
            return {}
        try:
            content = path.read_text(encoding="utf-8-sig")
            if kind == "yaml":
                if yaml is None:
                    self.error("dependency", relative, "PyYAML is required; install 06_implementation/requirements-validation.txt.")
                    return {}
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("Top-level value must be an object.")
            return data
        except (ValueError, OSError, UnicodeError) as exc:
            self.error("parse_error", relative, str(exc))
        except Exception as exc:
            # PyYAML exceptions are unavailable when the optional import failed.
            if yaml is not None and isinstance(exc, yaml.YAMLError):
                self.error("parse_error", relative, str(exc))
            else:
                raise
        return {}

    def exact(self, record, expected, location):
        for key, value in expected.items():
            # bool/int must not compare equal in a contract (False is not 0).
            actual = record.get(key)
            self.check(type(actual) is type(value) and actual == value,
                       "contract_mismatch", f"{location}.{key}", f"Expected {value!r}; found {actual!r}.")

    def inventory(self):
        p = self.protocol
        self.exact(p, {"split_source": SPLIT, "annotation_status_source": ANNOTATION}, PROTOCOL)
        path = self.safe_path(SPLIT, "split_source")
        if path is None:
            return
        self.check(p.get("split_sha256") == sha256(path), "split_hash", PROTOCOL, "Split source hash differs from its exact bytes.")
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                required = {"incident_id", "scenario_family_id", "split", "split_version"}
                if not required.issubset(reader.fieldnames or []):
                    raise ValueError("Split map is missing required columns.")
                rows = list(reader)
        except (ValueError, OSError, UnicodeError, csv.Error) as exc:
            self.error("split_parse", SPLIT, str(exc))
            return
        incident_ids = [row["incident_id"] for row in rows]
        self.check(all(incident_ids) and len(set(incident_ids)) == len(rows), "split_duplicates", SPLIT, "Incident IDs must be nonempty and unique.")
        family_splits = defaultdict(set)
        family_repetitions = Counter()
        for row in rows:
            family_splits[row["scenario_family_id"]].add(row["split"])
            family_repetitions[row["scenario_family_id"]] += 1
        self.check(all(family_splits) and all(len(s) == 1 for s in family_splits.values()), "family_leakage", SPLIT, "Every nonempty family must belong to exactly one split.")
        split_counts = dict(Counter(row["split"] for row in rows))
        family_counts = dict(Counter(next(iter(s)) for s in family_splits.values() if len(s) == 1))
        observed = {"incidents": len(rows), "families": len(family_splits), "split": split_counts,
                    "family_split": family_counts, "repetitions_per_family": 3}
        expected = {"incidents": 90, "families": 30, "split": {"train": 54, "dev": 18, "test": 18},
                    "family_split": {"train": 18, "dev": 6, "test": 6}, "repetitions_per_family": 3}
        self.exact(observed, expected, SPLIT)
        self.check(set(family_repetitions.values()) == {3}, "family_repetitions", SPLIT, "Each family must have three repetitions.")
        dataset = p.get("dataset", {})
        if not isinstance(dataset, dict):
            self.error("schema", f"{PROTOCOL}.dataset", "Expected an object.")
        else:
            self.exact(dataset, observed, f"{PROTOCOL}.dataset")
        self.check({row["split_version"] for row in rows} == {p.get("split_version")}, "split_version", PROTOCOL, "Every split row must match the protocol split_version.")
        annotation = self.load(ANNOTATION)
        self.exact(annotation, {"human_judgments_completed": 0, "gold_qrels_available": False,
                                "reference_answers_available": False}, ANNOTATION)
        self.exact(p, {"human_judgments_current": 0}, PROTOCOL)

    def document_summary(self):
        path = self.safe_path(DOC, DOC)
        if path is None:
            return
        content = path.read_text(encoding="utf-8-sig")
        match = re.search(r"<!-- protocol-summary:start -->\s*```ya?ml\s*\n(.*?)\n```\s*<!-- protocol-summary:end -->", content, re.S)
        if not self.check(match is not None, "document_summary", DOC, "Missing protocol-summary YAML block."):
            return
        if yaml is None:
            return
        try:
            summary = yaml.safe_load(match.group(1))
            if not isinstance(summary, dict):
                raise ValueError("Summary must be an object.")
            # The public summary is deliberately small; richer policy remains in YAML.
            keys = {"primary_metric", "primary_selection", "tie_break", "required_conditions",
                    "optional_conditions", "qrels_core", "test_tuning", "freeze_sequence"}
            self.exact(summary, {key: self.protocol.get(key) for key in keys}, DOC)
        except (ValueError, yaml.YAMLError) as exc:
            self.error("document_summary", DOC, str(exc))

    def decision_log(self):
        data = self.load(DECISIONS)
        self.exact(data, {"schema_version": 1, "protocol_id": self.protocol.get("protocol_id"),
                          "version": self.protocol.get("version")}, DECISIONS)
        records = data.get("decisions")
        if not self.check(isinstance(records, list) and bool(records), "decision_schema", DECISIONS, "Expected a nonempty decisions list."):
            return
        identifiers = set()
        for index, decision in enumerate(records):
            location = f"{DECISIONS}.decisions[{index}]"
            if not self.check(isinstance(decision, dict), "decision_schema", location, "Expected an object."):
                continue
            self.decisions.append(decision)
            identity = decision.get("decision_id")
            if self.check(nonempty(identity), "decision_id", location, "Missing decision_id."):
                self.check(identity not in identifiers, "decision_id", location, "Duplicate decision_id.")
                identifiers.add(identity)
            self.check(nonempty(decision.get("topic")), "decision_schema", location, "Missing topic.")
            options = decision.get("options")
            self.check(isinstance(options, list) and len(options) >= 2 and all(nonempty(v) for v in options), "decision_options", location, "Expected at least two explicit options.")
            owner, reviewer = decision.get("owner"), decision.get("reviewer")
            self.check(owner in ROLES and reviewer in ROLES and owner != reviewer, "decision_ownership", location, "Owner and independent reviewer must be different A/B/C roles.")
            due = decision.get("due_relative_week")
            self.check(type(due) is int and 1 <= due <= 8, "decision_deadline", location, "Deadline must be a relative week from 1 through 8.")
            status = decision.get("status")
            self.check(status in {"pending", "confirmed", "rejected"}, "decision_status", location, "Unknown decision status.")
            if status == "pending":
                self.check(decision.get("chosen") is None and decision.get("decided_at_utc") is None, "false_decision", location, "Pending decisions cannot claim an outcome or decision timestamp.")
            elif status in {"confirmed", "rejected"}:
                self.check(nonempty(decision.get("source_ref")) and utc_timestamp(decision.get("decided_at_utc")), "decision_evidence", location, "Resolved decisions need source_ref and a UTC ISO timestamp.")
                self.check(nonempty(decision.get("chosen")), "decision_outcome", location, "Resolved decisions need an explicit outcome.")
                self.check(isinstance(options, list) and decision.get("chosen") in options, "decision_outcome", location, "Resolved chosen must be one of the recorded options.")

    def literature(self):
        path = self.safe_path(LITERATURE, LITERATURE)
        if path is None:
            return
        required = {"paper_id", "title", "primary_url", "read_depth", "reader", "task_match",
                    "method_decision", "limitations", "verified_at", "read_sections", "source_kind",
                    "source_local_path", "source_sha256", "human_reader_assigned",
                    "human_reviewer_assigned", "human_read_status", "human_review_status"}
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                if not required.issubset(reader.fieldnames or []):
                    raise ValueError("Literature matrix is missing required provenance/review columns.")
                rows = list(reader)
        except (ValueError, OSError, UnicodeError, csv.Error) as exc:
            self.error("literature_schema", LITERATURE, str(exc))
            return
        self.check(8 <= len(rows) <= 12, "literature_count", LITERATURE, "Expected 8–12 core papers.")
        identifiers = set()
        for index, row in enumerate(rows):
            location = f"{LITERATURE}:row{index + 2}"
            identity = row["paper_id"]
            self.check(nonempty(identity) and identity not in identifiers, "literature_id", location, "Paper IDs must be nonempty and unique.")
            identifiers.add(identity)
            self.check(all(nonempty(row[key]) for key in ("title", "reader", "task_match", "method_decision", "limitations", "source_kind")), "literature_fields", location, "Missing substantive literature fields.")
            url = urlsplit(row["primary_url"] or "")
            self.check(url.scheme in {"http", "https"} and bool(url.netloc), "literature_url", location, "Primary URL must be an HTTP(S) source URL.")
            self.check(row["read_depth"] in {"metadata", "abstract", "selected_sections", "full_text"}, "literature_depth", location, "Unknown read_depth.")
            self.check(utc_timestamp(row["verified_at"]), "literature_timestamp", location, "Verification requires a UTC ISO timestamp.")
            if row["read_depth"] in {"selected_sections", "full_text"}:
                self.check(nonempty(row["read_sections"]), "literature_sections", location, "Section/full-text reading needs an explicit reading scope.")
            source = row["source_local_path"]
            if source not in (None, "", "null"):
                source_path = self.safe_path(source, location)
                if source_path is not None:
                    self.check(row["source_sha256"] == sha256(source_path), "literature_source_hash", location, "Literature source hash differs from its exact file bytes.")
            else:
                self.check(row["source_sha256"] in (None, "", "null"), "literature_source_hash", location, "A web-only record cannot claim a local source hash.")
            owner, reviewer = row["human_reader_assigned"], row["human_reviewer_assigned"]
            self.check(owner in ROLES and reviewer in ROLES and owner != reviewer, "literature_ownership", location, "Assign different A/B/C reader and reviewer roles.")
            for activity in ("read", "review"):
                status = row[f"human_{activity}_status"]
                self.check(status in {"pending", "completed"}, "literature_human_status", location, "Human activity must be pending or completed.")
                if status == "completed":
                    self.check(human_name(row.get(f"human_{activity}_by")) and utc_timestamp(row.get(f"human_{activity}_at")) and nonempty(row.get(f"human_{activity}_evidence_ref")), "literature_human_evidence", location, "Completed human reading/review requires a human name, UTC time, and evidence reference.")

    def permissions(self):
        p_perms = self.protocol.get("permissions")
        m_perms = self.manifest.get("permissions")
        if not self.check(isinstance(p_perms, dict) and isinstance(m_perms, dict), "permission_schema", MANIFEST, "Protocol and manifest need permissions objects."):
            return
        self.check(p_perms == m_perms, "permission_mismatch", MANIFEST, "Manifest permissions differ from the protocol.")
        keyed = defaultdict(list)
        for decision in self.decisions:
            if "permission_key" in decision:
                key = decision["permission_key"]
                if isinstance(key, str) and key in PERMISSION_KEYS:
                    keyed[key].append(decision)
                else:
                    self.error("permission_key", DECISIONS, "Unrecognized permission_key.")
        for key in sorted(PERMISSION_KEYS):
            self.check(len(keyed[key]) == 1, "permission_decision", DECISIONS, f"Expected exactly one decision for {key}.")
            state = p_perms.get(key)
            if key == "budget_usd":
                valid = state is None or (type(state) in (int, float) and 0 <= state < float("inf"))
                self.check(valid, "permission_budget", PROTOCOL, "Budget must be null or a finite nonnegative number.")
                resolved = state is not None
            else:
                self.check(state in {"pending", "approved", "rejected"}, "permission_status", PROTOCOL, f"Invalid {key} permission.")
                resolved = state in {"approved", "rejected"}
            if len(keyed[key]) == 1:
                decision = keyed[key][0]
                expected_status = "rejected" if state == "rejected" else ("confirmed" if resolved else "pending")
                self.check(decision.get("status") == expected_status, "false_permission", DECISIONS, f"Permission {key} contradicts its decision status.")
                if resolved:
                    self.check(nonempty(decision.get("source_ref")) and utc_timestamp(decision.get("decided_at_utc")), "permission_evidence", DECISIONS, f"Resolved {key} needs an approval/rejection evidence reference and UTC timestamp.")
                    value = decision.get("permission_value")
                    valid_value = (type(value) in (int, float) and value == state) if key == "budget_usd" else value == state
                    self.check(valid_value, "permission_value", DECISIONS, f"Resolved {key} needs permission_value matching the published permission/budget.")
                    if key != "budget_usd":
                        self.check(decision.get("chosen") == value, "permission_outcome", DECISIONS, f"Resolved {key} chosen outcome must match permission_value.")
                else:
                    self.check(decision.get("permission_value") is None, "false_permission", DECISIONS, f"Pending {key} cannot claim permission_value.")
        allowed = self.manifest.get("allowed_work")
        known_work = {"data", "corpus", "representation", "retrieval", "annotation_preparation", "api_generation", "local_generation", "data_sharing"}
        if not self.check(isinstance(allowed, list) and all(isinstance(v, str) and v in known_work for v in allowed) and len(allowed) == len(set(allowed)), "allowed_work", MANIFEST, "Allowed work must be a unique list of recognized work types."):
            return
        if "api_generation" in allowed:
            self.check(p_perms.get("api") == "approved" and p_perms.get("api_payload") == "approved" and type(p_perms.get("budget_usd")) in (int, float), "api_not_authorized", MANIFEST, "API generation needs approved model and payload permissions plus a confirmed budget.")
        if "local_generation" in allowed:
            self.check(p_perms.get("local_model") == "approved", "local_not_authorized", MANIFEST, "Local generation requires approved local_model permission.")
        if "data_sharing" in allowed:
            self.check(p_perms.get("data_sharing") == "approved", "sharing_not_authorized", MANIFEST, "Data sharing requires approved data_sharing permission.")

    def manifest_files(self):
        manifest = self.manifest
        self.exact(manifest, {"schema_version": 1, "gate_id": "G0", "gate_kind": "project_start",
                              "protocol_id": self.protocol.get("protocol_id"), "version": self.protocol.get("version")}, MANIFEST)
        self.check(utc_timestamp(manifest.get("created_at_utc")), "manifest_timestamp", MANIFEST, "created_at_utc must be a UTC ISO timestamp.")
        seen = set()
        artifact_paths = set()
        source_paths = set()
        for section in ("artifacts", "sources"):
            records = manifest.get(section)
            if not self.check(isinstance(records, list) and bool(records), "manifest_schema", MANIFEST, f"Expected nonempty {section} list."):
                continue
            for index, entry in enumerate(records):
                location = f"{MANIFEST}.{section}[{index}]"
                if not self.check(isinstance(entry, dict), "manifest_schema", location, "Expected an object."):
                    continue
                relative = entry.get("path")
                path = self.safe_path(relative, location)
                if path is None:
                    continue
                self.check(path not in seen, "manifest_duplicate", location, "A file may appear only once in the manifest.")
                seen.add(path)
                (artifact_paths if section == "artifacts" else source_paths).add(relative)
                self.check(relative != MANIFEST, "manifest_self_hash", location, "A manifest cannot hash itself.")
                actual_hash = entry.get("sha256")
                self.check(isinstance(actual_hash, str) and bool(re.fullmatch(r"[0-9a-f]{64}", actual_hash)) and actual_hash == sha256(path), "artifact_hash", location, "SHA-256 differs from exact file bytes or has invalid encoding.")
                if section == "artifacts":
                    self.check(relative.startswith(f"{IMPL}/"), "artifact_location", location, "Derivative artifacts must be inside 06_implementation.")
                    self.check(entry.get("version") == self.protocol.get("version"), "artifact_version", location, "Artifact version differs from the protocol version.")
        self.check(REQUIRED_ARTIFACTS.issubset(artifact_paths), "manifest_coverage", MANIFEST, "Manifest does not cover every required Plan 01 artifact.")
        if self.manifest.get("review_mode") == "automated":
            self.check({AUTH, REVIEW, AMENDMENT}.issubset(artifact_paths), "manifest_coverage", MANIFEST, "Automated acceptance must hash authorization, review receipt, and amendment.")
        self.check({SPLIT, ANNOTATION}.issubset(source_paths), "source_coverage", MANIFEST, "Manifest must record exact split and annotation-status source hashes.")
        pending = {d["decision_id"] for d in self.decisions if d.get("status") == "pending" and nonempty(d.get("decision_id"))}
        recorded = manifest.get("open_decisions")
        self.check(isinstance(recorded, list) and all(nonempty(v) for v in recorded) and len(recorded) == len(set(recorded)) and set(recorded) == pending, "open_decisions", MANIFEST, "open_decisions must exactly list all pending decision IDs.")

    def human_reviews(self):
        p, m = self.protocol, self.manifest
        gate = p.get("gate")
        if self.check(isinstance(gate, dict), "gate_schema", PROTOCOL, "Protocol must declare its project_start gate."):
            self.exact(gate, {"gate_id": "G0", "gate_kind": "project_start", "status": m.get("gate_status")}, f"{PROTOCOL}.gate")
        team = p.get("team")
        roster = {}
        if self.check(isinstance(team, list) and len(team) == 3, "team_schema", PROTOCOL, "Expected a three-role team."):
            for member in team:
                if not self.check(isinstance(member, dict), "team_schema", PROTOCOL, "Team members must be objects."):
                    continue
                role, reviewer = member.get("role"), member.get("reviewer")
                if not self.check(isinstance(role, str) and role in ROLES and role not in roster and reviewer in ROLES and role != reviewer, "team_roles", PROTOCOL, "Team roles must be unique A/B/C with independent reviewers."):
                    continue
                roster[role] = member.get("person")
                self.check(member.get("person") is None or human_name(member.get("person")), "team_person", PROTOCOL, "Person must be null or a human name, never Codex/a role placeholder.")
        mode = gate.get("review_mode", "human") if isinstance(gate, dict) else "human"
        self.check(mode in {"human", "automated"} and m.get("review_mode", "human") == mode, "review_mode", MANIFEST, "Protocol and manifest must agree on human/automated review mode.")
        if mode == "automated":
            self.automated_reviews()
            return
        records = m.get("reviewers")
        complete = set()
        people = set()
        if self.check(isinstance(records, list), "review_schema", MANIFEST, "reviewers must be a list."):
            for record in records:
                if not self.check(isinstance(record, dict), "review_schema", MANIFEST, "Reviewer must be an object."):
                    continue
                role, person = record.get("role"), record.get("person")
                valid = isinstance(role, str) and role in ROLES and role not in complete and human_name(person) and person == roster.get(role) and person not in people and nonempty(record.get("scope")) and utc_timestamp(record.get("reviewed_at"))
                if self.check(valid, "human_review", MANIFEST, "Completed reviews need a unique roster role, matching human name, scope, and signed UTC time."):
                    complete.add(role)
                    people.add(person)
        gate_status = m.get("gate_status")
        self.check(gate_status in {"awaiting_human_review", "accepted"}, "gate_status", MANIFEST, "G0 must be awaiting_human_review or accepted.")
        ready = complete == ROLES and p.get("status") in {"reviewed", "frozen"}
        if gate_status == "accepted":
            self.check(ready, "false_g0", MANIFEST, "Accepted G0 requires three completed human reviews and reviewed/frozen protocol.")
        else:
            self.check(m.get("allowed_work_mode") == "preparation_only_until_G0", "draft_work_mode", MANIFEST, "An unsigned draft must label allowed work preparation_only_until_G0.")
            pending_reviews = m.get("pending_reviews")
            pending_roles = set()
            if self.check(isinstance(pending_reviews, list), "pending_reviews", MANIFEST, "Unsigned G0 needs explicit pending review records."):
                for record in pending_reviews:
                    if not isinstance(record, dict):
                        self.error("pending_reviews", MANIFEST, "Pending review must be an object.")
                        continue
                    role = record.get("role")
                    valid = isinstance(role, str) and role in ROLES and role not in pending_roles and record.get("reviewed_at") is None and nonempty(record.get("scope"))
                    if self.check(valid, "pending_reviews", MANIFEST, "Pending review needs unique role, scope, and null reviewed_at."):
                        pending_roles.add(role)
                self.check(pending_roles == ROLES - complete, "pending_reviews", MANIFEST, "Pending review roles must match the unfinished human reviews.")
        if complete != ROLES:
            self.block("human_review_required", MANIFEST, f"Human reviews remain required for roles {', '.join(sorted(ROLES - complete))}.")
        if p.get("status") not in {"reviewed", "frozen"}:
            self.block("protocol_not_reviewed", PROTOCOL, "Protocol remains a draft pending human acceptance.")
        if gate_status != "accepted":
            self.block("g0_not_accepted", MANIFEST, "G0 has not been accepted by the team.")

    def automated_reviews(self):
        """Check this explicit user-authorized amendment without inventing humans."""
        p, m = self.protocol, self.manifest
        self.exact(p.get("gate", {}), {"authorization_ref": AUTH, "status": "accepted"}, f"{PROTOCOL}.gate")
        self.exact(m, {"authorization_ref": AUTH, "reviewers": [], "pending_reviews": [],
                       "gate_status": "accepted", "allowed_work_mode": "accepted_under_explicit_user_authorization"}, MANIFEST)
        self.check(p.get("status") in {"reviewed", "frozen"}, "automated_protocol_status", PROTOCOL, "Automated acceptance requires reviewed/frozen protocol status.")
        self.exact(p, {"permissions": PENDING_PERMISSIONS}, PROTOCOL)
        authorization = self.load(AUTH)
        self.exact(authorization, {
            "source_kind": "user_message", "instruction": "tự check mọi thứ, không cần human input",
            "scope": "plan01_g0_self_review", "human_review_required": False, "permissions_unchanged": True,
        }, AUTH)
        self.check(nonempty(authorization.get("authorization_id")), "authorization_id", AUTH, "Explicit authorization needs its own record ID.")
        self.check(utc_timestamp(authorization.get("recorded_at_utc")), "authorization_timestamp", AUTH, "Authorization needs a UTC ISO timestamp.")
        review = self.load(REVIEW)
        self.exact(review, {"schema_version": 1, "protocol_id": p.get("protocol_id"), "version": p.get("version"),
                            "authorization_ref": AUTH, "result": "PASS", "blocking_findings": []}, REVIEW)
        reviewer = review.get("reviewer")
        self.check(nonempty(reviewer) and reviewer.startswith("Codex /root/"), "automated_reviewer", REVIEW, "Automated reviewer must be explicitly identified as a Codex agent.")
        self.check(utc_timestamp(review.get("reviewed_at_utc")), "automated_review_timestamp", REVIEW, "Automated review needs a UTC ISO timestamp.")
        scopes = review.get("scope")
        self.check(isinstance(scopes, list) and all(nonempty(s) for s in scopes) and set(scopes) == AUTO_SCOPES and len(scopes) == len(AUTO_SCOPES), "automated_review_scope", REVIEW, "Automated review must cover all four required scopes exactly once.")
        checked = review.get("checked_artifacts")
        covered = set()
        if self.check(isinstance(checked, list) and bool(checked), "automated_review_coverage", REVIEW, "Review must bind actual artifacts, not an empty PASS claim."):
            for index, entry in enumerate(checked):
                location = f"{REVIEW}.checked_artifacts[{index}]"
                if not self.check(isinstance(entry, dict), "automated_review_schema", location, "Expected an artifact object."):
                    continue
                relative = entry.get("path")
                path = self.safe_path(relative, location)
                if path is None:
                    continue
                self.check(relative not in {REVIEW, MANIFEST}, "automated_review_cycle", location, "Review cannot hash itself or its enclosing manifest.")
                self.check(relative not in covered, "automated_review_duplicate", location, "Review artifact paths must be unique.")
                covered.add(relative)
                self.check(entry.get("sha256") == sha256(path), "automated_review_hash", location, "Artifact differs from the exact bytes reviewed.")
        self.check((REQUIRED_ARTIFACTS | {AUTH}).issubset(covered), "automated_review_coverage", REVIEW, "Review must bind all core docs/configs and the authorization record.")
        expected = [{"reviewer": reviewer, "scope": scopes, "reviewed_at": review.get("reviewed_at_utc"), "evidence_ref": REVIEW}]
        self.exact(m, {"automated_reviews": expected}, MANIFEST)

    def run(self, require_g0=False, manifest_override=None):
        self.protocol = self.load(PROTOCOL, "yaml")
        self.manifest = self.load(MANIFEST) if manifest_override is None else manifest_override
        self.exact(self.protocol, {"schema_version": 1, "required_retrievers": ["IR-B", "IR-D", "IR-H"]}, PROTOCOL)
        self.exact(self.protocol, METRIC_CONTRACT, PROTOCOL)
        for key in ("protocol_id", "version", "dataset_id", "split_version"):
            self.check(nonempty(self.protocol.get(key)), "schema", f"{PROTOCOL}.{key}", "Expected a nonempty string.")
        status = self.protocol.get("status")
        self.check(isinstance(status, str) and status in {"draft", "reviewed", "frozen"}, "protocol_status", PROTOCOL, "Invalid protocol status.")
        for validate in (self.inventory, self.document_summary, self.literature, self.decision_log,
                         self.permissions, self.manifest_files, self.human_reviews):
            try:
                validate()
            except (TypeError, KeyError, AttributeError) as exc:
                self.error("schema", validate.__name__, f"Malformed field type: {exc}")
        technical_valid = not self.errors
        g0_ready = technical_valid and not self.blockers
        return {
            "schema_version": 1,
            "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "protocol_id": self.protocol.get("protocol_id"),
            "technical_valid": technical_valid,
            "g0_ready": g0_ready,
            "require_g0": require_g0,
            "result": "PASS" if technical_valid and (g0_ready or not require_g0) else "FAIL",
            "errors": self.errors,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="Research pack root")
    parser.add_argument("--require-g0", action="store_true", help="Fail unless G0 has human or explicitly authorized automated acceptance")
    parser.add_argument("--output", type=Path, help="Write a validation receipt under 06_implementation (optional)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    validation = Validator(root)
    report = validation.run(args.require_g0)
    output = None
    if args.output is not None:
        output = args.output.resolve()
        # Receipts cannot overwrite configs, source material, or frozen artifacts.
        report_root = root / IMPL / "reports"
        frozen_outputs = {(root / entry["path"]).resolve() for entry in validation.manifest.get("artifacts", [])
                          if isinstance(entry, dict) and isinstance(entry.get("path"), str)}
        if not output.is_relative_to(report_root) or output.suffix.lower() != ".json" or output in frozen_outputs:
            report["errors"].append({"code": "unsafe_output", "location": str(output), "message": "--output must be a non-frozen .json receipt inside 06_implementation/reports."})
            report["technical_valid"] = report["g0_ready"] = False
            report["result"] = "FAIL"
            output = None
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
