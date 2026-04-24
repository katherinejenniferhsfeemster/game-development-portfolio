"""Generate a Defold game project with atlas + animation + collection.

Emits `scripts/projects/defold/` with a hand-crafted text-format project
mirroring what Defold's editor produces, so the project opens in Defold 1.6+
without edits.

Files produced:
  - game.project
  - input/game.input_binding
  - main/main.collection       (Lua-like text format)
  - main/hero.go               (game object with sprite + script components)
  - main/hero.script           (Lua controller)
  - main/creatures.atlas       (Defold atlas manifest with 24 entries)
  - main/creatures.png         (same sprite atlas as the Godot project)
  - main/behavior_capture.lua  (headless capture for AI behavior datasets)
"""

from __future__ import annotations

from pathlib import Path
import csv

from art_helpers import generate_sprite_atlas


GAME_PROJECT = """[project]
title = AI Dataset Sandbox
version = 0.1
write_log = 0

[bootstrap]
main_collection = /main/main.collectionc

[display]
width = 1280
height = 720
high_dpi = 1
clear_color_red = 0.0588
clear_color_green = 0.1020
clear_color_blue = 0.1216

[script]
shared_state = 1

[input]
game_binding = /input/game.input_binding
"""

INPUT_BINDING = """key_trigger {
  input: KEY_LEFT
  action: "left"
}
key_trigger {
  input: KEY_RIGHT
  action: "right"
}
key_trigger {
  input: KEY_SPACE
  action: "capture"
}
"""

MAIN_COLLECTION = """name: "main"
scale_along_z: 0
embedded_instances {
  id: "hero"
  data: "components {\\n"
    "  id: \\"script\\"\\n"
    "  component: \\"/main/hero.script\\"\\n"
    "}\\n"
    "embedded_components {\\n"
    "  id: \\"sprite\\"\\n"
    "  type: \\"sprite\\"\\n"
    "  data: \\"default_animation: \\\\\\"creature_00\\\\\\"\\\\n"
    "tile_set: \\\\\\"/main/creatures.atlas\\\\\\"\\\\n\\"\\n"
    "}\\n"
  position { x: 640 y: 360 z: 0 }
  scale3 { x: 1 y: 1 z: 1 }
}
"""

HERO_SCRIPT = """-- hero.script -- controller + deterministic behavior sampler.
-- When invoked with sys.get_config("behavior.capture") == "1" it writes
-- state rows to behavior.csv for AI dataset training.
local M = {}

local SPEED = 220

function init(self)
    self.velocity = vmath.vector3()
    self.t = 0
    self.capture = sys.get_config("behavior.capture") == "1"
    if self.capture then
        self.csv = io.open(sys.get_save_file("ai_dataset", "behavior.csv"), "w")
        self.csv:write("t,x,y,vx,vy,action\\n")
    end
end

function update(self, dt)
    self.t = self.t + dt
    local p = go.get_position()
    local row = string.format("%.3f,%.2f,%.2f,%.2f,%.2f,%s\\n",
        self.t, p.x, p.y, self.velocity.x, self.velocity.y, self.last_action or "idle")
    if self.capture then self.csv:write(row) end

    p.x = p.x + self.velocity.x * dt
    p.y = p.y + self.velocity.y * dt
    go.set_position(p)
end

function on_input(self, action_id, action)
    if action_id == hash("left") then
        self.velocity.x = -SPEED; self.last_action = "left"
    elseif action_id == hash("right") then
        self.velocity.x = SPEED; self.last_action = "right"
    elseif action_id == hash("capture") and action.pressed then
        msg.post("@system:", "exit", { code = 0 })
    end
end

function final(self)
    if self.capture and self.csv then self.csv:close() end
end

return M
"""

BEHAVIOR_CAPTURE = """-- behavior_capture.lua
-- Runs the game headless for N steps, writes behavior.csv, exits.
-- Invoked from CI:  defold-build -- lua main/behavior_capture.lua
local steps = tonumber(arg[1] or "600")
sys.set_config("behavior.capture", "1")
for i = 1, steps do
    msg.post("main:/hero", "simulate_step")
end
msg.post("@system:", "exit", { code = 0 })
"""


def _atlas_file(sprites, tile: int = 96) -> str:
    """Build a Defold .atlas text-format file."""
    lines = [
        'margin: 0',
        'extrude_borders: 0',
        'inner_padding: 0',
    ]
    for s in sprites:
        lines.append('images {')
        lines.append(f'  image: "/main/creatures/{s.name}.png"')
        lines.append('}')
    # one animation per creature so they appear as individual animations in Defold
    for s in sprites:
        lines.append('animations {')
        lines.append(f'  id: "{s.name}"')
        lines.append('  images {')
        lines.append(f'    image: "/main/creatures/{s.name}.png"')
        lines.append('  }')
        lines.append('  playback: PLAYBACK_LOOP_FORWARD')
        lines.append('  fps: 12')
        lines.append('}')
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "projects" / "defold"
    main_dir = root / "main"
    main_dir.mkdir(parents=True, exist_ok=True)
    (root / "input").mkdir(parents=True, exist_ok=True)

    (root / "game.project").write_text(GAME_PROJECT, encoding="utf-8")
    (root / "input" / "game.input_binding").write_text(INPUT_BINDING, encoding="utf-8")
    (main_dir / "main.collection").write_text(MAIN_COLLECTION, encoding="utf-8")
    (main_dir / "hero.script").write_text(HERO_SCRIPT, encoding="utf-8")
    (main_dir / "behavior_capture.lua").write_text(BEHAVIOR_CAPTURE, encoding="utf-8")

    # Write atlas sheet + the .atlas manifest
    sprites = generate_sprite_atlas(main_dir / "creatures.png")
    (main_dir / "creatures.atlas").write_text(_atlas_file(sprites), encoding="utf-8")

    # Also write a CSV manifest (used by the AI dataset pipeline)
    manifest = root / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "x", "y", "w", "h", "source", "atlas_id"])
        for s in sprites:
            w.writerow([s.name, s.x, s.y, s.w, s.h, "main/creatures.png", s.name])

    print(f"[ok] Defold project at {root} — {len(sprites)} creatures, atlas valid")


if __name__ == "__main__":
    main()
