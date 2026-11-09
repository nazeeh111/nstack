"""Conservative GP5.2.1 interpolation: never discard unsupported attributes."""
from pathlib import Path

def patch(out):
 p=out/'scripts/bx_gp.py';t=p.read_text()
 a='    Pa, Ra, _ = _arrays(da)\n    Pb, Rb, _ = _arrays(db)\n    if np.allclose(Pa, Pb, atol=eps) and np.allclose(Ra, Rb, atol=eps):'
 b='''    # Generic inbetween only writes these attributes. Refuse unsupported data
    # even when endpoints agree: rebuilding would otherwise silently drop it.
    supported = {"position": ("POINT", "FLOAT_VECTOR"),
                 "radius": ("POINT", "FLOAT"), "opacity": ("POINT", "FLOAT"),
                 "material_index": ("CURVE", "INT"), "cyclic": ("CURVE", "BOOLEAN"),
                 "fill_id": ("CURVE", "INT"), "hide_stroke": ("CURVE", "BOOLEAN"),
                 "curve_type": ("CURVE", "INT8")}
    for drawing in (da, db):
        for attr in drawing.attributes:
            if attr.name in (".selection", ".selection_point", ".selection_curve"):
                continue
            if attr.name not in supported or (attr.domain, attr.data_type) != supported[attr.name]:
                return "different", f"unsupported attribute {attr.name}: redraw or explicit clip"
            if attr.name == "curve_type" and any(item.value != 1 for item in attr.data):
                return "different", "only POLY curves supported by generic interpolation"
    for i, (a, b) in enumerate(zip(da.strokes, db.strokes)):
        for prop in ("cyclic", "fill_id", "hide_stroke"):
            if getattr(a, prop) != getattr(b, prop):
                return "different", f"stroke {i}: {prop} differs; redraw or explicit clip"
    Pa, Ra, Oa = _arrays(da)
    Pb, Rb, Ob = _arrays(db)
    if (np.allclose(Pa, Pb, atol=eps) and np.allclose(Ra, Rb, atol=eps)
            and np.allclose(Oa, Ob, atol=eps)):'''
 if a not in t:raise ValueError('GP opacity/guard source anchor changed')
 t=t.replace(a,b)
 t+='\n\n'+(Path(__file__).parent/'gp_delivery_guard.py').read_text();p.write_text(t)
 p=out/'SKILL.md';t=p.read_text();t+='''\n## Interpolation and deliverable exposure

The bundled helper fixes opacity-only interpolation and refuses generic interpolation when topology, curve flags or meaningful attributes cannot be preserved. Explicit `clip=True` copies the nearest native drawing, preserving its attributes; it is a discrete hold, not interpolation. Redraw unsupported changes or use separately tested native interpolation. Do not silently flatten vertex colors, fills or softness. Use `validate_delivery(ob, required_layers=[...], frames=[...])` for the brief's actual active drawing layers, including completely unkeyed layers; accept only `result["issues"] == []`. Organizational layers are not automatically required.

New work uses the exercised Blender5.2.1 baseline; preserve incumbent file versions. Work in an owned/duplicated scene with unique names. Save and reopen editable fills, keys, parenting and materials in a second process and render distinct phases. Inspect decoded output and motion, not just helper return values. Upstream absent tests are source claims, not installed executable tests.\n''';p.write_text(t)
