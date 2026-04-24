# Stride (Xenko) .NET Asset Pipeline

A GameStudio-compatible Stride 4.2 project, generated from Python. Ships a
`.sln` + `.csproj` + `.sdpkg` + YAML `.sdscene` with the same 12×12 voxel scene
as the Godot and Panda 3D projects, plus a C# `DataCaptureComponent` that logs
per-frame entity transforms to JSONL for AI dataset use.

## What the script produces

`scripts/python/build_stride_project.py` emits
`scripts/projects/stride/` with:

- **`DatasetSandbox.sln`** — standard .NET SDK solution file.
- **`DatasetSandbox/DatasetSandbox.csproj`** — `Microsoft.NET.Sdk`, targets
  `net8.0`, references `Stride.Engine`, `Stride.Graphics`, `Stride.Physics`,
  `Stride.UI` at version `4.2.*`.
- **`DatasetSandbox/DatasetSandbox.sdpkg`** — Stride package (YAML) with a
  shared platform profile and the main scene as a root asset.
- **`DatasetSandbox/Assets/Scenes/MainScene.sdscene`** — YAML scene document
  with a camera, a sun light, and \(12 \times 12 \times 1\text{--}3\) voxel
  entities, each with `Transform` and `ModelComponent`.
- **`DatasetSandbox/DatasetSandboxGame.cs`** — `Game` subclass. In
  `BeginRun()` it attaches `DataCaptureComponent` to a new `Entity` so the
  component receives per-frame `Update()` callbacks.
- **`DatasetSandbox/DataCaptureComponent.cs`** — `SyncScript`. When the
  `CAPTURE_PATH` env var is set it writes one `System.Text.Json` line per
  entity per frame to that path.
- **`DatasetSandbox/Program.cs`** — `Main` entry point for headless and
  GameStudio runs.

## Why it matters for AI research

- **First-class C# + .NET.** For teams already on the Microsoft stack, Stride
  eliminates FFI overhead for ML runtimes such as ML.NET, ONNX Runtime, or
  TorchSharp that you might want to hook into gameplay.
- **YAML scenes diff cleanly.** The `.sdscene` document is deterministic
  YAML, so PR reviewers can see entity additions and transform tweaks in a
  conventional diff.
- **Same scene content across engines.** The voxel positions in
  `MainScene.sdscene` match the Godot `.tscn` and Panda `.egg` scenes; a
  training set can be captured from any of the three.

## Run Stride

Open `DatasetSandbox.sln` in Visual Studio, Rider, or GameStudio. Or headless:

```bash
cd scripts/projects/stride
dotnet run --project DatasetSandbox
```

Capture per-frame entity transforms:

```bash
CAPTURE_PATH=capture.jsonl dotnet run --project DatasetSandbox
```

## Run the generator

```bash
python3 scripts/python/build_stride_project.py
```

## References

- Stride manual: https://doc.stride3d.net/
- `.sdscene` asset reference: https://doc.stride3d.net/latest/en/manual/game-studio/asset-types.html
- `SyncScript` lifecycle: https://doc.stride3d.net/latest/en/manual/scripts/types-of-scripts.html
- Stride on GitHub: https://github.com/stride3d/stride
