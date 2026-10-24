from pathlib import Path
p=Path('scripts/package_hw.py');s=p.read_text();s=s.replace("['omni_sequence_hv.json','omni_audit_hv.json','key_geometry_ht.json','boundaries_hv.json','installer_delivery_hv.json']","['escape_hw.json','escape_surface_hw.json','text_hw.json','hint_anchor_hs.json','installer_delivery_hw.json']");p.write_text(s)
