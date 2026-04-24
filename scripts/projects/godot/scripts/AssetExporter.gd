extends Node
# Autoload singleton: exports the scene tree to glTF for AI training datasets.
# Runs only in headless mode (--headless --export-gltf) to keep the editor fast.

func export_gltf(root: Node, path: String) -> void:
    if not OS.has_feature("headless"):
        return
    var gltf := GLTFDocument.new()
    var state := GLTFState.new()
    var err := gltf.append_from_scene(root, state)
    if err != OK:
        push_error("glTF append failed: %s" % err)
        return
    err = gltf.write_to_filesystem(state, path)
    if err != OK:
        push_error("glTF write failed: %s" % err)
        return
    print("[AssetExporter] wrote ", path)
