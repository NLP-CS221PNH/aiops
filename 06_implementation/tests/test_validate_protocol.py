"""Mutation tests using temporary, explicitly synthetic protocol fixtures only."""
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_protocol.py"
SPEC = importlib.util.spec_from_file_location("protocol_validator", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ProtocolValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cs221-synthetic-protocol-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.version = "1.0.0-draft.1"
        self.protocol = {
            "schema_version": 1, "protocol_id": "synthetic-test-protocol-v1",
            "version": self.version, "status": "draft", "dataset_id": "synthetic-test-data",
            "split_version": "synthetic-family-split-v1", "split_source": validator.SPLIT,
            "annotation_status_source": validator.ANNOTATION,
            "dataset": {"incidents": 90, "families": 30,
                        "split": {"train": 54, "dev": 18, "test": 18},
                        "family_split": {"train": 18, "dev": 6, "test": 6},
                        "repetitions_per_family": 3},
            "required_retrievers": ["IR-B", "IR-D", "IR-H"], "human_judgments_current": 0,
            "permissions": {"api": "pending", "api_payload": "pending", "local_model": "pending", "data_sharing": "pending", "budget_usd": None},
            "team": [{"role": role, "person": None, "reviewer": reviewer, "weekly_hours": None}
                     for role, reviewer in [("A", "B"), ("B", "C"), ("C", "A")]],
            "gate": {"gate_id": "G0", "gate_kind": "project_start", "status": "awaiting_human_review"},
            **copy.deepcopy(validator.METRIC_CONTRACT),
        }
        split_rows = ["incident_id\tscenario_family_id\tsplit\tsplit_version"]
        for family in range(30):
            split = "train" if family < 18 else ("dev" if family < 24 else "test")
            for repetition in range(3):
                split_rows.append(f"fixture_inc_{family}_{repetition}\tfixture_fam_{family}\t{split}\tsynthetic-family-split-v1")
        self.write(validator.SPLIT, "\n".join(split_rows) + "\n")
        self.protocol["split_sha256"] = validator.sha256(self.root / validator.SPLIT)
        self.write_json(validator.ANNOTATION, {
            "human_judgments_completed": 0, "gold_qrels_available": False,
            "reference_answers_available": False,
        })
        self.decisions = {"schema_version": 1, "protocol_id": self.protocol["protocol_id"], "version": self.version,
                          "decisions": [{"decision_id": f"FIXTURE-{key}", "topic": f"Synthetic {key} decision",
                                         "permission_key": key, "options": ["approve", "reject"], "chosen": None,
                                         "status": "pending", "owner": "C", "reviewer": "A", "due_relative_week": 2,
                                         "source_ref": None, "decided_at_utc": None}
                                        for key in sorted(validator.PERMISSION_KEYS)]}
        self.manifest = {
            "schema_version": 1, "gate_id": "G0", "gate_kind": "project_start",
            "gate_status": "awaiting_human_review", "protocol_id": self.protocol["protocol_id"],
            "version": self.version, "created_at_utc": "2026-09-13T00:00:00Z",
            "artifacts": [], "sources": [], "reviewers": [],
            "pending_reviews": [{"role": role, "person": None, "scope": f"Synthetic scope {role}", "reviewed_at": None} for role in sorted(validator.ROLES)],
            "permissions": copy.deepcopy(self.protocol["permissions"]),
            "open_decisions": [d["decision_id"] for d in self.decisions["decisions"]],
            "allowed_work": ["data", "corpus", "representation", "retrieval", "annotation_preparation"],
            "allowed_work_mode": "preparation_only_until_G0",
        }
        for relative in validator.REQUIRED_ARTIFACTS:
            self.write(relative, "Synthetic unit-test fixture; no real research or human review.\n")
        self.write("01_papers/fixture.txt", "Synthetic literature excerpt for testing only.\n")
        self.literature_rows = [{"paper_id": f"fixture-paper-{index}", "title": f"Synthetic Paper {index}",
                                "primary_url": "https://example.org/synthetic-paper", "read_depth": "selected_sections",
                                "reader": "Codex", "task_match": "Test method provenance", "method_decision": "Test only",
                                "limitations": "Synthetic fixture, not an actual paper", "verified_at": "2026-09-13T00:00:00Z",
                                "read_sections": "Synthetic test excerpt", "source_kind": "local_primary_text",
                                "source_local_path": "01_papers/fixture.txt", "source_sha256": validator.sha256(self.root / "01_papers/fixture.txt"),
                                "human_reader_assigned": "A", "human_reviewer_assigned": "B", "human_read_status": "pending", "human_review_status": "pending"}
                               for index in range(8)]
        self.save()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_json(self, relative, data):
        self.write(relative, json.dumps(data, indent=2) + "\n")

    def save(self):
        self.write(validator.PROTOCOL, yaml.safe_dump(self.protocol, sort_keys=False))
        self.write_json(validator.DECISIONS, self.decisions)
        with (self.root / validator.LITERATURE).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.literature_rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(self.literature_rows)
        summary = {k: self.protocol.get(k) for k in validator.METRIC_CONTRACT}
        self.write(validator.DOC, "Synthetic protocol fixture\n<!-- protocol-summary:start -->\n```yaml\n" + yaml.safe_dump(summary, sort_keys=False) + "```\n<!-- protocol-summary:end -->\n")
        self.rehash()

    def rehash(self):
        paths = set(validator.REQUIRED_ARTIFACTS)
        if self.manifest.get("review_mode") == "automated":
            paths.update(path for path in (validator.AUTH, validator.REVIEW, validator.AMENDMENT) if (self.root / path).is_file())
        self.manifest["artifacts"] = [{"path": relative, "sha256": validator.sha256(self.root / relative), "version": self.version}
                                      for relative in sorted(paths)]
        self.manifest["sources"] = [{"path": relative, "sha256": validator.sha256(self.root / relative)}
                                    for relative in (validator.SPLIT, validator.ANNOTATION)]
        self.write_json(validator.MANIFEST, self.manifest)

    def run_check(self, require_g0=False):
        return validator.Validator(self.root).run(require_g0)

    def assert_error(self, report, code):
        self.assertFalse(report["technical_valid"], report)
        self.assertIn(code, {issue["code"] for issue in report["errors"]}, report)

    def enable_automated(self):
        """Synthetic authorization never leaves this test's temporary pack."""
        self.version = "1.0.0-reviewed.1"
        for record in (self.protocol, self.decisions, self.manifest):
            record["version"] = self.version
        self.protocol["status"] = "reviewed"
        self.protocol["gate"].update(status="accepted", review_mode="automated", authorization_ref=validator.AUTH)
        self.manifest.update(gate_status="accepted", review_mode="automated", authorization_ref=validator.AUTH,
                             pending_reviews=[], allowed_work_mode="accepted_under_explicit_user_authorization")
        self.authorization = {
            "authorization_id": "synthetic-fixture-authorization", "source_kind": "user_message",
            "instruction": "tự check mọi thứ, không cần human input", "recorded_at_utc": "2026-09-13T02:00:00Z",
            "scope": "plan01_g0_self_review", "human_review_required": False, "permissions_unchanged": True,
        }
        self.write_json(validator.AUTH, self.authorization)
        self.write(validator.AMENDMENT, "Synthetic explicit-authorization amendment; no real approval.\n")
        self.save()
        self.automated_review = {
            "schema_version": 1, "protocol_id": self.protocol["protocol_id"], "version": self.version,
            "reviewer": "Codex /root/synthetic-reviewer", "reviewed_at_utc": "2026-09-13T02:01:00Z",
            "scope": sorted(validator.AUTO_SCOPES), "result": "PASS", "blocking_findings": [],
            "authorization_ref": validator.AUTH, "checked_artifacts": [],
        }
        self.refresh_automated_review()

    def refresh_automated_review(self):
        self.automated_review["checked_artifacts"] = [{"path": path, "sha256": validator.sha256(self.root / path)}
                                                       for path in sorted(validator.REQUIRED_ARTIFACTS | {validator.AUTH})]
        self.write_json(validator.REVIEW, self.automated_review)
        self.manifest["automated_reviews"] = [{"reviewer": self.automated_review["reviewer"], "scope": self.automated_review["scope"],
                                               "reviewed_at": self.automated_review["reviewed_at_utc"], "evidence_ref": validator.REVIEW}]
        self.rehash()

    def load_builder(self):
        spec = importlib.util.spec_from_file_location("synthetic_g0_builder", SCRIPT.with_name("build_g0_manifest.py"))
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        builder.ROOT = self.root
        builder.IMPLEMENTATION = self.root / validator.IMPL
        for name in builder.ARTIFACTS:
            path = builder.IMPLEMENTATION / name
            if not path.exists():
                self.write(f"{validator.IMPL}/{name}", "Synthetic builder artifact.\n")
        self.write_json(f"{validator.IMPL}/validation/source-inventory.json", {"sources": copy.deepcopy(self.manifest["sources"])})
        self.protocol["communication"] = {"status": "pending"}
        self.save()
        self.refresh_automated_review()
        return builder

    def test_truthful_draft_is_technically_valid_but_does_not_pass_g0(self):
        draft = self.run_check()
        self.assertEqual(draft["result"], "PASS", draft)
        self.assertFalse(draft["g0_ready"])
        strict = self.run_check(require_g0=True)
        self.assertEqual(strict["result"], "FAIL")
        self.assertTrue(strict["technical_valid"])
        self.assertIn("human_review_required", {x["code"] for x in strict["blockers"]})

    def test_changed_artifact_bytes_invalidate_manifest(self):
        path = self.root / validator.PROTOCOL
        path.write_bytes(path.read_bytes() + b"\n# stale manifest mutation\n")
        self.assert_error(self.run_check(), "artifact_hash")

    def test_hash_tampering_is_not_trusted(self):
        self.manifest["artifacts"][0]["sha256"] = "0" * 64
        self.write_json(validator.MANIFEST, self.manifest)
        self.assert_error(self.run_check(), "artifact_hash")

    def test_wrong_inventory_cannot_be_rehashed_into_validity(self):
        self.protocol["dataset"]["split"]["test"] = 17
        self.save()
        self.assert_error(self.run_check(), "contract_mismatch")

    def test_family_cannot_cross_splits_even_with_refreshed_hashes(self):
        path = self.root / validator.SPLIT
        text = path.read_text(encoding="utf-8").replace("fixture_inc_0_0\tfixture_fam_0\ttrain", "fixture_inc_0_0\tfixture_fam_0\ttest")
        self.write(validator.SPLIT, text)
        self.protocol["split_sha256"] = validator.sha256(path)
        self.save()
        self.assert_error(self.run_check(), "family_leakage")

    def test_freeze_order_cannot_use_test_pool_before_f1(self):
        self.protocol["freeze_sequence"] = ["test_pool", "F1", "test_input", "F2", "test_scoring"]
        self.save()
        self.assert_error(self.run_check(), "contract_mismatch")

    def test_missing_unjudged_policy_fails(self):
        del self.protocol["unjudged_is_zero"]
        self.save()
        self.assert_error(self.run_check(), "contract_mismatch")

    def test_numeric_zero_is_not_boolean_false(self):
        self.protocol["unjudged_is_zero"] = 0
        self.save()
        self.assert_error(self.run_check(), "contract_mismatch")

    def test_fabricated_current_judgments_fail(self):
        self.protocol["human_judgments_current"] = 56
        self.save()
        self.assert_error(self.run_check(), "contract_mismatch")

    def test_changed_source_annotation_status_fails(self):
        self.write_json(validator.ANNOTATION, {"human_judgments_completed": 1, "gold_qrels_available": True, "reference_answers_available": False})
        self.rehash()
        self.assert_error(self.run_check(), "contract_mismatch")

    def test_pending_api_never_authorizes_generation(self):
        self.manifest["allowed_work"].append("api_generation")
        self.write_json(validator.MANIFEST, self.manifest)
        self.assert_error(self.run_check(), "api_not_authorized")

    def test_permission_flags_without_confirmed_decision_fail(self):
        self.protocol["permissions"]["api"] = "approved"
        self.manifest["permissions"]["api"] = "approved"
        self.save()
        self.assert_error(self.run_check(), "false_permission")

    def test_confirmed_permission_without_evidence_fails(self):
        self.protocol["permissions"]["api"] = "approved"
        self.manifest["permissions"]["api"] = "approved"
        decision = next(d for d in self.decisions["decisions"] if d["permission_key"] == "api")
        decision.update(status="confirmed", chosen="approved")
        self.manifest["open_decisions"].remove(decision["decision_id"])
        self.save()
        self.assert_error(self.run_check(), "permission_evidence")

    def test_missing_decision_owner_and_deadline_fail(self):
        self.decisions["decisions"][0].update(owner=None, due_relative_week=None)
        self.save()
        report = self.run_check()
        self.assert_error(report, "decision_ownership")
        self.assert_error(report, "decision_deadline")

    def test_omitted_open_decision_fails(self):
        self.manifest["open_decisions"].pop()
        self.write_json(validator.MANIFEST, self.manifest)
        self.assert_error(self.run_check(), "open_decisions")

    def test_codex_cannot_sign_for_a_human(self):
        self.protocol["team"][0]["person"] = "Codex"
        self.manifest["reviewers"] = [{"role": "A", "person": "Codex", "scope": "All work", "reviewed_at": "2026-09-13T01:00:00Z"}]
        self.save()
        self.assert_error(self.run_check(), "human_review")

    def test_accepted_gate_without_human_reviews_is_false(self):
        self.manifest["gate_status"] = "accepted"
        self.save()
        self.assert_error(self.run_check(), "false_g0")

    def test_synthetic_complete_review_exercises_success_branch_only_in_temp_fixture(self):
        self.protocol["status"] = "reviewed"
        for member in self.protocol["team"]:
            member["person"] = "Synthetic Reviewer " + member["role"]
        self.manifest["reviewers"] = [{"role": member["role"], "person": member["person"], "scope": "Unit-test fixture review", "reviewed_at": "2026-09-13T01:00:00Z"} for member in self.protocol["team"]]
        self.manifest["pending_reviews"] = []
        self.manifest["gate_status"] = "accepted"
        self.protocol["gate"]["status"] = "accepted"
        self.save()
        report = self.run_check(require_g0=True)
        self.assertTrue(report["g0_ready"], report)

    def test_doc_summary_drift_fails_even_after_rehash(self):
        path = self.root / validator.DOC
        self.write(validator.DOC, path.read_text(encoding="utf-8").replace("passage_ndcg_at_5", "document_ndcg_at_5"))
        self.rehash()
        self.assert_error(self.run_check(), "contract_mismatch")

    def test_artifact_traversal_is_rejected(self):
        self.manifest["artifacts"][0]["path"] = "../outside.json"
        self.write_json(validator.MANIFEST, self.manifest)
        self.assert_error(self.run_check(), "unsafe_path")

    def test_absolute_windows_path_is_rejected(self):
        self.manifest["artifacts"][0]["path"] = "C:/Windows/system.ini"
        self.write_json(validator.MANIFEST, self.manifest)
        self.assert_error(self.run_check(), "unsafe_path")

    def test_version_mismatch_fails(self):
        self.manifest["artifacts"][0]["version"] = "2.0.0"
        self.write_json(validator.MANIFEST, self.manifest)
        self.assert_error(self.run_check(), "artifact_version")

    def test_gate_status_in_yaml_cannot_disagree_with_manifest(self):
        self.protocol["gate"]["status"] = "accepted"
        self.save()
        self.assert_error(self.run_check(), "contract_mismatch")

    def test_resolved_permission_must_match_machine_value(self):
        self.protocol["permissions"]["api"] = self.manifest["permissions"]["api"] = "approved"
        decision = next(d for d in self.decisions["decisions"] if d["permission_key"] == "api")
        decision.update(status="confirmed", chosen="approval rationale", permission_value="rejected", source_ref="https://example.org/fixture-approval", decided_at_utc="2026-09-13T01:00:00Z")
        self.manifest["open_decisions"].remove(decision["decision_id"])
        self.save()
        self.assert_error(self.run_check(), "permission_value")

    def test_budget_must_match_confirmed_numeric_value(self):
        self.protocol["permissions"]["budget_usd"] = self.manifest["permissions"]["budget_usd"] = 15
        decision = next(d for d in self.decisions["decisions"] if d["permission_key"] == "budget_usd")
        decision.update(status="confirmed", chosen="fixture budget rationale", permission_value="15", source_ref="https://example.org/fixture-approval", decided_at_utc="2026-09-13T01:00:00Z")
        self.manifest["open_decisions"].remove(decision["decision_id"])
        self.save()
        self.assert_error(self.run_check(), "permission_value")

    def test_chosen_rejection_cannot_support_approved_permission(self):
        self.protocol["permissions"]["api"] = self.manifest["permissions"]["api"] = "approved"
        decision = next(d for d in self.decisions["decisions"] if d["permission_key"] == "api")
        decision.update(options=["approved", "rejected"], status="confirmed", chosen="rejected", permission_value="approved", source_ref="https://example.org/fixture-approval", decided_at_utc="2026-09-13T01:00:00Z")
        self.manifest["open_decisions"].remove(decision["decision_id"])
        self.save()
        self.assert_error(self.run_check(), "permission_outcome")

    def test_budget_accepts_selected_option_with_separate_numeric_amount(self):
        self.protocol["permissions"]["budget_usd"] = self.manifest["permissions"]["budget_usd"] = 15
        decision = next(d for d in self.decisions["decisions"] if d["permission_key"] == "budget_usd")
        decision.update(options=["Confirm specified spending ceiling", "Reject spending"], status="confirmed", chosen="Confirm specified spending ceiling", permission_value=15, source_ref="https://example.org/fixture-approval", decided_at_utc="2026-09-13T01:00:00Z")
        self.manifest["open_decisions"].remove(decision["decision_id"])
        self.save()
        report = self.run_check()
        self.assertTrue(report["technical_valid"], report)

    def test_chosen_must_exist_in_recorded_options(self):
        decision = self.decisions["decisions"][0]
        decision.update(status="confirmed", chosen="unlisted outcome", source_ref="https://example.org/fixture-decision", decided_at_utc="2026-09-13T01:00:00Z")
        self.save()
        self.assert_error(self.run_check(), "decision_outcome")

    def test_missing_phase03_review_cannot_pass_manifest(self):
        self.manifest["artifacts"] = [row for row in self.manifest["artifacts"] if not row["path"].endswith("protocol-review.md")]
        self.write_json(validator.MANIFEST, self.manifest)
        self.assert_error(self.run_check(), "manifest_coverage")

    def test_literature_count_and_duplicate_ids_fail(self):
        self.literature_rows.pop()
        self.literature_rows[0]["paper_id"] = self.literature_rows[1]["paper_id"]
        self.save()
        report = self.run_check()
        self.assert_error(report, "literature_count")
        self.assert_error(report, "literature_id")

    def test_literature_source_hash_change_fails(self):
        self.write("01_papers/fixture.txt", "Changed synthetic excerpt.\n")
        self.assert_error(self.run_check(), "literature_source_hash")

    def test_literature_cannot_invent_completed_human_reading(self):
        self.literature_rows[0]["human_read_status"] = "completed"
        self.save()
        self.assert_error(self.run_check(), "literature_human_evidence")

    def test_malformed_permissions_produce_report_not_traceback(self):
        self.protocol["permissions"]["api"] = ["approved"]
        self.manifest["permissions"]["api"] = ["approved"]
        self.save()
        self.assert_error(self.run_check(), "schema")

    def test_cli_read_only_and_strict_exit_status(self):
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with redirect_stdout(io.StringIO()) as stdout:
            code = validator.main(["--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["result"], "PASS")
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(validator.main(["--root", str(self.root), "--require-g0"]), 1)

    def test_output_receipt_is_explicit_and_cannot_overwrite_source(self):
        output = self.root / validator.IMPL / "reports" / "test.json"
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(validator.main(["--root", str(self.root), "--output", str(output)]), 0)
        self.assertEqual(output.read_text(encoding="utf-8"), stdout.getvalue())
        source = self.root / validator.SPLIT
        before = source.read_bytes()
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(validator.main(["--root", str(self.root), "--output", str(source)]), 1)
        self.assertEqual(source.read_bytes(), before)
        self.assertIn("unsafe_output", {x["code"] for x in json.loads(stdout.getvalue())["errors"]})

    def test_explicit_automated_acceptance_passes_without_human_signatures(self):
        self.enable_automated()
        report = self.run_check(require_g0=True)
        self.assertTrue(report["g0_ready"], report)
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(self.manifest["reviewers"], [])
        self.assertEqual(self.protocol["permissions"], validator.PENDING_PERMISSIONS)

    def test_automated_mode_requires_existing_authorization(self):
        self.enable_automated()
        (self.root / validator.AUTH).unlink()
        self.assert_error(self.run_check(require_g0=True), "missing_file")

    def test_automated_mode_requires_existing_review_receipt(self):
        self.enable_automated()
        (self.root / validator.REVIEW).unlink()
        self.assert_error(self.run_check(require_g0=True), "missing_file")

    def test_automated_mode_rejects_wrong_authorization_scope(self):
        self.enable_automated()
        self.authorization["scope"] = "api_generation"
        self.write_json(validator.AUTH, self.authorization)
        self.refresh_automated_review()
        self.assert_error(self.run_check(require_g0=True), "contract_mismatch")

    def test_automated_review_must_match_protocol_and_version(self):
        self.enable_automated()
        self.automated_review.update(protocol_id="another-protocol", version="stale-version")
        self.refresh_automated_review()
        self.assert_error(self.run_check(require_g0=True), "contract_mismatch")

    def test_automated_review_rejects_hash_drift_after_rehashing_manifest(self):
        self.enable_automated()
        self.write(f"{validator.IMPL}/docs/project-charter.md", "Changed after automated review.\n")
        self.rehash()
        self.assert_error(self.run_check(require_g0=True), "automated_review_hash")

    def test_automated_review_rejects_missing_scope(self):
        self.enable_automated()
        self.automated_review["scope"].pop()
        self.refresh_automated_review()
        self.assert_error(self.run_check(require_g0=True), "automated_review_scope")

    def test_automated_review_rejects_blocking_findings(self):
        self.enable_automated()
        self.automated_review["blocking_findings"] = ["Unresolved synthetic finding"]
        self.refresh_automated_review()
        self.assert_error(self.run_check(require_g0=True), "contract_mismatch")

    def test_automated_review_rejects_non_pass_outcome(self):
        self.enable_automated()
        self.automated_review["result"] = "FAIL"
        self.refresh_automated_review()
        self.assert_error(self.run_check(require_g0=True), "contract_mismatch")

    def test_automated_receipt_cannot_be_empty_pass_claim(self):
        self.enable_automated()
        self.automated_review["checked_artifacts"] = []
        self.write_json(validator.REVIEW, self.automated_review)
        self.rehash()
        self.assert_error(self.run_check(require_g0=True), "automated_review_coverage")

    def test_automated_mode_cannot_fabricate_human_signatures(self):
        self.enable_automated()
        self.manifest["reviewers"] = [{"role": "A", "person": "Codex", "scope": "Synthetic", "reviewed_at": "2026-09-13T02:00:00Z"}]
        self.rehash()
        self.assert_error(self.run_check(require_g0=True), "contract_mismatch")

    def test_automated_override_cannot_grant_api_permissions(self):
        self.enable_automated()
        self.protocol["permissions"]["api"] = self.manifest["permissions"]["api"] = "approved"
        self.save()
        self.refresh_automated_review()
        report = self.run_check(require_g0=True)
        self.assert_error(report, "contract_mismatch")
        self.assert_error(report, "false_permission")

    def test_review_mode_must_match_between_protocol_and_manifest(self):
        self.enable_automated()
        self.manifest["review_mode"] = "human"
        self.rehash()
        self.assert_error(self.run_check(require_g0=True), "review_mode")

    def test_output_cannot_overwrite_frozen_automated_review(self):
        self.enable_automated()
        output = self.root / validator.REVIEW
        before = output.read_bytes()
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(validator.main(["--root", str(self.root), "--output", str(output)]), 1)
        self.assertEqual(output.read_bytes(), before)
        self.assertIn("unsafe_output", {x["code"] for x in json.loads(stdout.getvalue())["errors"]})

    def test_builder_accepts_only_verified_automated_candidate_and_is_idempotent(self):
        self.enable_automated()
        builder = self.load_builder()
        manifest = self.root / validator.MANIFEST
        manifest.unlink()
        with redirect_stdout(io.StringIO()):
            builder.main()
        first = manifest.read_bytes()
        report = self.run_check(require_g0=True)
        self.assertTrue(report["g0_ready"], report)
        with redirect_stdout(io.StringIO()):
            builder.main()
        self.assertEqual(first, manifest.read_bytes())

    def test_builder_rejects_stale_review_before_replacing_manifest(self):
        self.enable_automated()
        builder = self.load_builder()
        manifest = self.root / validator.MANIFEST
        before = manifest.read_bytes()
        self.write(f"{validator.IMPL}/docs/project-charter.md", "Changed synthetic artifact after review.\n")
        with self.assertRaises(SystemExit) as failure:
            builder.main()
        self.assertIn("automated_review_hash", str(failure.exception))
        self.assertEqual(before, manifest.read_bytes())

    def test_builder_rejects_missing_authorization_before_output(self):
        self.enable_automated()
        builder = self.load_builder()
        manifest = self.root / validator.MANIFEST
        before = manifest.read_bytes()
        (self.root / validator.AUTH).unlink()
        with self.assertRaises(SystemExit) as failure:
            builder.main()
        self.assertIn("missing_file", str(failure.exception))
        self.assertEqual(before, manifest.read_bytes())


if __name__ == "__main__":
    unittest.main()
