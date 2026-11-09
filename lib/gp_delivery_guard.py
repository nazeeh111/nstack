"""Appended to the pinned GP helper: explicit active-layer exposure validation."""

def validate_delivery(ob, required_layers, frames, scene=None):
    """Audit named deliverable layers at every requested exposure, including unkeyed ones.

    Organisational/hidden layers are not implicitly deliverables. Caller identifies
    the visible drawing layers that the actual brief requires. Held keys count as
    exposures; an empty drawing or hidden layer does not.
    """
    result = report(ob, scene=scene)
    for name in required_layers:
        layer = ob.data.layers.get(name)
        if layer is None:
            result['issues'].append(f"required layer missing: {name}")
            continue
        if layer.hide:
            result['issues'].append(f"required layer hidden: {name}")
        keys = sorted(frame.frame_number for frame in layer.frames)
        for frame in frames:
            prior = [key for key in keys if key <= frame]
            drawing = layer.get_frame_at(frame).drawing if prior else None
            if drawing is None or not len(drawing.strokes):
                result['issues'].append(f"required layer {name}: no drawing exposed at frame {frame}")
    return result
