"""
Tests for HardQualityGates, EditorialJudge, and QCSupervisor.
Validates non-negotiable machine gates and 2-revision repair loop.
"""
from src.ingest.probe import MediaProbe
from src.detection.visual_detector import VisualDetector
from src.qc.hard_gates import HardQualityGates
from src.qc.editorial_judge import EditorialJudge
from src.qc.supervisor import QCSupervisor


def test_hard_gates_pass_on_sample_video(sample_video):
    # Note: sample_video is 1920x1080 (horizontal), so resolution gate must fail
    probe = MediaProbe()
    v_det = VisualDetector()
    hg = HardQualityGates(probe=probe, visual_detector=v_det)

    all_pass, gates = hg.run_all_gates(sample_video)
    res_gate = next(g for g in gates if g.gate_id == "GATE-RESOLUTION")
    assert res_gate.pass_ is False  # Correctly catches horizontal video!
    assert all_pass is False


def test_hard_gates_detect_black_screen(black_screen_video):
    probe = MediaProbe()
    v_det = VisualDetector()
    hg = HardQualityGates(probe=probe, visual_detector=v_det)

    all_pass, gates = hg.run_all_gates(black_screen_video)
    black_gate = next(g for g in gates if g.gate_id == "GATE-BLACK-FRAMES")
    assert black_gate.pass_ is False
    assert all_pass is False


def test_hard_gates_detect_silent_audio(silent_video):
    probe = MediaProbe()
    v_det = VisualDetector()
    hg = HardQualityGates(probe=probe, visual_detector=v_det)

    all_pass, gates = hg.run_all_gates(silent_video)
    audio_gate = next(g for g in gates if g.gate_id == "GATE-AUDIO-PRESENCE")
    assert audio_gate.pass_ is False
    assert all_pass is False


def test_supervisor_repair_cap_escalation():
    probe = MediaProbe()
    v_det = VisualDetector()
    hg = HardQualityGates(probe=probe, visual_detector=v_det)
    judge = EditorialJudge()
    supervisor = QCSupervisor(hard_gates=hg, judge=judge)

    candidate = {"narrative_stages": {}}
    plan = {}

    # Revision 1: initial repair suggested
    res_rev1 = supervisor.audit_render(
        audit_id="qc-1",
        trace_id="tr-1",
        render_id="ren-1",
        media_path="/dummy/path",
        event_candidate=candidate,
        edit_plan=plan,
        current_revision=1,
    )

    # Revision 2: max repair revisions exceeded -> must escalate to human_review or reject!
    res_rev2 = supervisor.audit_render(
        audit_id="qc-2",
        trace_id="tr-2",
        render_id="ren-2",
        media_path="/dummy/path",
        event_candidate=candidate,
        edit_plan=plan,
        current_revision=2,
    )
    assert res_rev2.editorial.result in {"human_review", "reject"}
