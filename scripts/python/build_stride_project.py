"""Generate a Stride (formerly Xenko) .NET game project.

Stride projects are YAML-based. We emit a GameStudio-compatible package plus
a minimal C# game entry point that loads a procedural scene and includes a
`DataCaptureComponent` that writes one JSON per frame for AI dataset use.

Files produced in `scripts/projects/stride/`:
  - DatasetSandbox.sln
  - DatasetSandbox/DatasetSandbox.csproj
  - DatasetSandbox/DatasetSandbox.sdpkg
  - DatasetSandbox/Assets/Scenes/MainScene.sdscene
  - DatasetSandbox/DatasetSandboxGame.cs
  - DatasetSandbox/DataCaptureComponent.cs
  - DatasetSandbox/Program.cs
"""

from __future__ import annotations

from pathlib import Path
import uuid
import yaml


PACKAGE_GUID = "b0d4a1f2-0000-4000-8000-000000000001"
PROJECT_GUID = "b0d4a1f2-0000-4000-8000-000000000002"
SCENE_GUID = "b0d4a1f2-0000-4000-8000-000000000003"

SLN = r"""Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "DatasetSandbox", "DatasetSandbox\DatasetSandbox.csproj", "{B0D4A1F2-0000-4000-8000-000000000002}"
EndProject
Global
    GlobalSection(SolutionConfigurationPlatforms) = preSolution
        Debug|Any CPU = Debug|Any CPU
        Release|Any CPU = Release|Any CPU
    EndGlobalSection
    GlobalSection(ProjectConfigurationPlatforms) = postSolution
        {B0D4A1F2-0000-4000-8000-000000000002}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
        {B0D4A1F2-0000-4000-8000-000000000002}.Debug|Any CPU.Build.0 = Debug|Any CPU
        {B0D4A1F2-0000-4000-8000-000000000002}.Release|Any CPU.ActiveCfg = Release|Any CPU
        {B0D4A1F2-0000-4000-8000-000000000002}.Release|Any CPU.Build.0 = Release|Any CPU
    EndGlobalSection
EndGlobal
"""

CSPROJ = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
    <RootNamespace>DatasetSandbox</RootNamespace>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Stride.Engine" Version="4.2.*" />
    <PackageReference Include="Stride.Graphics" Version="4.2.*" />
    <PackageReference Include="Stride.Physics" Version="4.2.*" />
    <PackageReference Include="Stride.UI" Version="4.2.*" />
  </ItemGroup>
</Project>
"""

GAME_CS = """using System;
using Stride.Engine;
using Stride.Games;

namespace DatasetSandbox
{
    /// <summary>
    /// Main game class. Stride instantiates this via Program.cs; it wires up
    /// a procedurally-populated scene and the dataset capture component.
    /// </summary>
    public class DatasetSandboxGame : Game
    {
        protected override void BeginRun()
        {
            base.BeginRun();

            // Attach a data-capture component to the root scene entity so it
            // receives Update() callbacks each frame.
            var root = new Entity("DataCapture");
            root.Add(new DataCaptureComponent { CapturePath = Environment.GetEnvironmentVariable("CAPTURE_PATH") });
            SceneSystem.SceneInstance.RootScene.Entities.Add(root);
        }
    }
}
"""

CAPTURE_CS = """using System;
using System.IO;
using System.Text.Json;
using Stride.Core.Mathematics;
using Stride.Engine;

namespace DatasetSandbox
{
    /// <summary>
    /// Writes one JSON line per frame with the transform of every named
    /// entity in the scene. Gated on the CAPTURE_PATH env var so normal
    /// editor runs stay quiet.
    /// </summary>
    public class DataCaptureComponent : SyncScript
    {
        public string? CapturePath { get; set; }

        private StreamWriter? _writer;
        private double _t;

        public override void Start()
        {
            if (string.IsNullOrEmpty(CapturePath)) return;
            _writer = new StreamWriter(CapturePath!);
        }

        public override void Update()
        {
            if (_writer == null) return;
            _t += Game.UpdateTime.Elapsed.TotalSeconds;
            foreach (var entity in Entity.Scene.Entities)
            {
                var row = new
                {
                    t = _t,
                    name = entity.Name,
                    pos = new[] { entity.Transform.Position.X, entity.Transform.Position.Y, entity.Transform.Position.Z },
                };
                _writer.WriteLine(JsonSerializer.Serialize(row));
            }
        }

        public override void Cancel()
        {
            _writer?.Flush();
            _writer?.Dispose();
        }
    }
}
"""

PROGRAM_CS = """using Stride.Engine;

namespace DatasetSandbox
{
    internal static class Program
    {
        public static void Main(string[] args)
        {
            using var game = new DatasetSandboxGame();
            game.Run();
        }
    }
}
"""


def _build_scene_yaml() -> str:
    """Stride .sdscene is YAML. Build a minimal valid document."""
    # Use safe_dump on a nested dict; Stride's YAML is permissive enough that
    # this round-trips in GameStudio without touching the editor.
    doc = {
        "!Scene": None,
        "Id": SCENE_GUID,
        "SerializedVersion": {"Stride": "2.1.0.1"},
        "Tags": [],
        "Hierarchy": {
            "RootParts": [],
            "Parts": [],
        },
        "Offset": {"X": 0.0, "Y": 0.0, "Z": 0.0},
    }

    # Camera + light + 12x12 voxel entities (matches Godot/Panda scene)
    parts: list[dict] = []
    root_parts: list[dict] = []

    def _add(name: str, pos: list[float], color: list[float]) -> None:
        ent_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"sandbox.{name}"))
        parts.append({
            "Entity": {
                "Id": ent_id,
                "Name": name,
                "Components": {
                    "Transform": {
                        "Position": {"X": pos[0], "Y": pos[1], "Z": pos[2]},
                        "Rotation": {"X": 0, "Y": 0, "Z": 0, "W": 1},
                        "Scale": {"X": 1, "Y": 1, "Z": 1},
                    },
                    "ModelComponent": {
                        "Model": None,
                        "Materials": [{"Color": {"R": color[0], "G": color[1], "B": color[2], "A": 1.0}}],
                    },
                },
            },
        })
        root_parts.append({"Id": ent_id})

    _add("MainCamera", [20, 18, -24], [1, 1, 1])
    _add("Sun", [0, 40, 0], [1, 0.95, 0.85])

    for i in range(12):
        for j in range(12):
            h = 3 if (2 <= i < 5 and 2 <= j < 5) else 2 if (7 <= i < 10 and 6 <= j < 9) else 1
            for z in range(h):
                color = [0.85, 0.64, 0.25] if h >= 4 else [0.18, 0.48, 0.48] if h >= 2 else [0.94, 0.93, 0.89]
                _add(f"vox_{i}_{j}_{z}", [float(i), float(z), float(j)], color)

    doc["Hierarchy"]["Parts"] = parts
    doc["Hierarchy"]["RootParts"] = root_parts
    return yaml.safe_dump(doc, sort_keys=False, width=120)


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "projects" / "stride"
    proj = root / "DatasetSandbox"
    scenes = proj / "Assets" / "Scenes"
    scenes.mkdir(parents=True, exist_ok=True)

    (root / "DatasetSandbox.sln").write_text(SLN, encoding="utf-8")
    (proj / "DatasetSandbox.csproj").write_text(CSPROJ, encoding="utf-8")
    (proj / "DatasetSandboxGame.cs").write_text(GAME_CS, encoding="utf-8")
    (proj / "DataCaptureComponent.cs").write_text(CAPTURE_CS, encoding="utf-8")
    (proj / "Program.cs").write_text(PROGRAM_CS, encoding="utf-8")
    (scenes / "MainScene.sdscene").write_text(_build_scene_yaml(), encoding="utf-8")

    # Minimal .sdpkg (Stride package)
    sdpkg = {
        "!Package": None,
        "Id": PACKAGE_GUID,
        "SerializedVersion": {"Stride": "2.1.0.1"},
        "Meta": {"Name": "DatasetSandbox", "Version": "1.0.0.0"},
        "Profiles": [{
            "Platform": "Shared",
            "AssetFolders": [{"Path": "Assets"}],
            "OutputGroup": "",
        }],
        "Bundles": [],
        "RootAssets": [{"Id": SCENE_GUID, "Location": "Scenes/MainScene"}],
    }
    (proj / "DatasetSandbox.sdpkg").write_text(
        yaml.safe_dump(sdpkg, sort_keys=False), encoding="utf-8",
    )

    print(f"[ok] Stride project at {root}")


if __name__ == "__main__":
    main()
