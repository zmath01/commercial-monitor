from commercial_monitor.ingest import make_sample_panel
from commercial_monitor.pipeline import build_features,build_target

def test_pipeline():
    panel=make_sample_panel(["A","B","C"],range(2015,2025))
    frame,graph=build_features(panel,2)
    out=build_target(frame,"csi",2)
    assert len(out)==30
    assert {"csi","target","graph_degree"}.issubset(out.columns)
