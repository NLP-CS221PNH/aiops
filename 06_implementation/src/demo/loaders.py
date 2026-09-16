import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Gốc an toàn cho các artifact: 06_implementation
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OBSERVATIONS_FILE = BASE_DIR / "data" / "inference" / "observations.jsonl"

class SecurityError(Exception):
    """Lỗi bảo mật khi truy cập file ngoài allowlist hoặc path traversal."""
    pass

class ArtifactMismatchError(Exception):
    """Lỗi sai lệch mã băm (hash mismatch) giữa cấu hình và artifact thực tế."""
    pass

def safe_resolve_path(rel_or_abs_path: str, allow_root: Path = BASE_DIR) -> Path:
    """
    Chuẩn hóa và kiểm tra đường dẫn file:
    - Ngăn chặn triệt để path traversal ('..').
    - Không cho phép trỏ ra ngoài allow_root (06_implementation).
    """
    raw_path = Path(rel_or_abs_path)
    if raw_path.is_absolute():
        try:
            resolved = raw_path.resolve(strict=False)
            resolved.relative_to(allow_root.resolve())
            return resolved
        except ValueError:
            raise SecurityError(f"Truy cập bị chặn: Đường dẫn tuyệt đối nằm ngoài allowlist: {rel_or_abs_path}")
    else:
        # Nếu có dấu '..' trỏ ngược
        resolved = (allow_root / raw_path).resolve(strict=False)
        try:
            resolved.relative_to(allow_root.resolve())
            return resolved
        except ValueError:
            raise SecurityError(f"Truy cập bị chặn: Phát hiện path traversal '..': {rel_or_abs_path}")

def compute_file_sha256(filepath: Path) -> str:
    """Tính mã băm SHA-256 của file."""
    if not filepath.exists() or not filepath.is_file():
        return ""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

@dataclass
class EvidenceView:
    evidence_id: str
    actual_context_text: str
    source_kind: str
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    rank: Optional[int] = None
    source_revision: str = "unknown"
    start_codepoint: int = 0
    end_codepoint: int = 0
    offsets: str = ""
    used_by_claim_ids: List[str] = field(default_factory=list)

@dataclass
class Metadata:
    run_id: str
    generated_at_utc: str
    model_requested: str
    model_returned: Optional[str]
    context_hash: str
    corpus_hash: str
    manifest_hash: str
    status: str
    latency_ms: Optional[float] = None
    usage: Optional[Dict[str, Any]] = None

@dataclass
class ViewModel:
    case_id: str
    origin: str  # research_run | fixture
    display_mode: str  # replay | live | fixture
    incident_id: str
    condition: str  # G0 | GB | GD | GH | GR
    status: str  # ready | abstained | invalid_response | invalid_citation | artifact_mismatch
    selection_reason: str
    expected_status: str
    metadata: Metadata
    observations: Dict[str, Any]
    observations_hash: str
    evidence_items: List[EvidenceView]
    candidate_causes: List[Dict[str, Any]]
    supported_claims: List[Dict[str, Any]]
    missing_information: List[str]
    next_checks: List[str]
    abstain: bool
    confidence_label: str
    raw_response: str
    validation_error: Optional[str] = None

class DemoDataLoader:
    def __init__(self, base_dir: Path = BASE_DIR):
        self.base_dir = base_dir.resolve()
        self._observations_cache: Dict[str, Dict[str, Any]] = {}
        self._load_observations()

    def _load_observations(self):
        """Nạp danh mục observations từ observations.jsonl nếu tồn tại."""
        if OBSERVATIONS_FILE.exists():
            with open(OBSERVATIONS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            inc_id = record.get("incident_id")
                            if inc_id:
                                self._observations_cache[inc_id] = record
                        except json.JSONDecodeError:
                            continue

    def get_observation(self, incident_id: str) -> Dict[str, Any]:
        """Lấy observation theo incident_id hoặc trả về mock nếu không có."""
        if incident_id in self._observations_cache:
            return self._observations_cache[incident_id]
        return {
            "incident_id": incident_id,
            "system_id": "online_boutique",
            "observation_start": "unknown",
            "observation_end_exclusive": "unknown",
            "metric_summary_ids": [],
            "log_span_ids": [],
            "trace_span_ids": []
        }

    def load_case_config(self, config_path: str = "configs/demo-cases.yaml") -> Dict[str, Any]:
        """Nạp danh sách ca demo từ file YAML."""
        safe_path = safe_resolve_path(config_path, self.base_dir)
        if not safe_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file cấu hình: {config_path}")
        
        import yaml
        with open(safe_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_view_model(self, case_config: Dict[str, Any]) -> ViewModel:
        """Xây dựng ViewModel đầy đủ từ cấu hình case và các artifact trên đĩa."""
        case_id = case_config.get("case_id", "unknown")
        incident_id = case_config.get("incident_id", "unknown")
        run_id = case_config.get("run_id", "unknown")
        condition = case_config.get("condition", "GH")
        origin = case_config.get("origin", "fixture")
        display_mode = case_config.get("display_mode", "fixture")
        selection_reason = case_config.get("selection_reason", "")
        expected_status = case_config.get("expected_status", "success")
        result_ref = case_config.get("result_ref", "")
        expected_manifest_hash = case_config.get("manifest_hash", "")
        
        # 1. Resolve run directory safely
        run_dir = safe_resolve_path(result_ref, self.base_dir)
        if not run_dir.exists() or not run_dir.is_dir():
            raise FileNotFoundError(f"Thư mục run_dir không tồn tại: {result_ref}")
            
        manifest_path = run_dir / "manifest.json"
        responses_path = run_dir / "responses.jsonl"
        context_path = run_dir / "context.jsonl"
        
        # 2. Verify Manifest Hash
        actual_manifest_hash = compute_file_sha256(manifest_path)
        if expected_manifest_hash and actual_manifest_hash != expected_manifest_hash:
            raise ArtifactMismatchError(
                f"Lệch hash manifest tại {case_id}: Kỳ vọng {expected_manifest_hash}, thực tế {actual_manifest_hash}"
            )
            
        manifest_data = {}
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
                
        # 3. Load Context Items
        context_items: List[Dict[str, Any]] = []
        if context_path.exists():
            with open(context_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        context_items.append(json.loads(line))
        actual_context_hash = compute_file_sha256(context_path)
        
        # 4. Load RunRecord from responses.jsonl
        run_record: Dict[str, Any] = {}
        if responses_path.exists():
            with open(responses_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        run_record = json.loads(line)
                        break  # Demo cases currently contain 1 record per run
                        
        status = run_record.get("status", expected_status)
        raw_response = run_record.get("raw_response", "")
        val_error = run_record.get("error", None)
        parsed_payload = run_record.get("parsed_payload")
        
        # Try to parse raw_response if parsed_payload is missing and status is success
        if not parsed_payload and raw_response:
            try:
                candidate_data = json.loads(raw_response)
                if isinstance(candidate_data, dict):
                    parsed_payload = candidate_data
            except json.JSONDecodeError:
                pass
                
        candidate_causes = []
        supported_claims = []
        missing_info = []
        next_checks = []
        abstain = False
        confidence_label = "unknown"
        
        if parsed_payload and isinstance(parsed_payload, dict):
            candidate_causes = parsed_payload.get("candidate_causes", [])
            supported_claims = parsed_payload.get("supported_claims", [])
            missing_info = parsed_payload.get("missing_information", [])
            next_checks = parsed_payload.get("next_checks", [])
            abstain = parsed_payload.get("abstain", False)
            confidence_label = parsed_payload.get("confidence_label", "unknown")
            
        # Map which claims use which evidence_id
        claim_map: Dict[str, List[str]] = {}
        for claim in supported_claims:
            c_id = claim.get("claim_id", "")
            for eid in claim.get("evidence_ids", []):
                claim_map.setdefault(eid, []).append(c_id)
                
        # 5. Build EvidenceView objects
        evidence_views: List[EvidenceView] = []
        for item in context_items:
            eid = item.get("evidence_id", "")
            ev = EvidenceView(
                evidence_id=eid,
                actual_context_text=item.get("text", ""),
                source_kind=item.get("source_kind", "doc"),
                document_id=item.get("document_id"),
                chunk_id=item.get("chunk_id"),
                rank=item.get("rank"),
                source_revision=item.get("source_revision", "unknown"),
                start_codepoint=item.get("start_codepoint", 0),
                end_codepoint=item.get("end_codepoint", 0),
                offsets=f"[{item.get('start_codepoint', 0)}:{item.get('end_codepoint', 0)}]",
                used_by_claim_ids=claim_map.get(eid, [])
            )
            evidence_views.append(ev)
            
        # 6. Load Observation details
        obs_data = self.get_observation(incident_id)
        obs_serialized = json.dumps(obs_data, sort_keys=True)
        obs_hash = hashlib.sha256(obs_serialized.encode("utf-8")).hexdigest()
        
        meta = Metadata(
            run_id=run_id,
            generated_at_utc=run_record.get("UTC", "2026-09-13T10:00:00Z"),
            model_requested=run_record.get("model_requested", "unknown"),
            model_returned=run_record.get("model_returned"),
            context_hash=actual_context_hash,
            corpus_hash="5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3",
            manifest_hash=actual_manifest_hash,
            status=status,
            latency_ms=run_record.get("usage", {}).get("latency_ms") if run_record.get("usage") else None,
            usage=run_record.get("usage")
        )
        
        return ViewModel(
            case_id=case_id,
            origin=origin,
            display_mode=display_mode,
            incident_id=incident_id,
            condition=condition,
            status=status,
            selection_reason=selection_reason,
            expected_status=expected_status,
            metadata=meta,
            observations=obs_data,
            observations_hash=obs_hash,
            evidence_items=evidence_views,
            candidate_causes=candidate_causes,
            supported_claims=supported_claims,
            missing_information=missing_info,
            next_checks=next_checks,
            abstain=abstain,
            confidence_label=confidence_label,
            raw_response=raw_response,
            validation_error=val_error
        )
