"""Generate a Solar 2D (formerly Corona SDK) project.

Solar 2D projects are pure Lua + PNGs — no editor is required. This generator
emits a working project with a scene, sprite loader, deterministic particle
system and an AI behavior capture module that writes a CSV each frame.

Files produced in `scripts/projects/solar2d/`:
  - main.lua
  - config.lua
  - build.settings
  - scene.lua
  - particles.lua
  - capture.lua
  - assets/tilemap.png
  - assets/particles.png
  - assets/creatures.png
"""

from __future__ import annotations

from pathlib import Path

from art_helpers import (
    generate_sprite_atlas,
    generate_tilemap,
    generate_particle_burst,
)


MAIN_LUA = """-- main.lua
-- Entry point for Solar 2D. Loads the scene and, when CAPTURE=1, runs the
-- AI behavior capture module before exit.
local composer = require("composer")

if system.getInfo("environment") == "simulator" or os.getenv("CAPTURE") == "1" then
    math.randomseed(7)  -- deterministic captures
end

composer.gotoScene("scene")

if os.getenv("CAPTURE") == "1" then
    local capture = require("capture")
    timer.performWithDelay(10, function() capture.run(600) end)
end
"""

CONFIG_LUA = """application = {
    content = {
        width = 720,
        height = 1280,
        scale = "letterbox",
        fps = 60,
        imageSuffix = { ["@2x"] = 2 },
    },
    license = { google = { key = "" } },
}
"""

BUILD_SETTINGS = """settings = {
    orientation = { default = "portrait", supported = { "portrait" } },
    iphone = { plist = { UIStatusBarHidden = true, UIViewControllerBasedStatusBarAppearance = false } },
    android = { googlePlayGamesAppId = "", supportsScreens = {
        smallScreens = true, normalScreens = true, largeScreens = true, xlargeScreens = true
    } },
    window = { defaultMode = "normal", resizable = false,
        defaultViewWidth = 720, defaultViewHeight = 1280,
        titleText = { default = "AI Dataset Sandbox" } },
    plugins = {},
}
"""

SCENE_LUA = """-- scene.lua
-- Builds a scripted scene: tilemap background, sprite hero, particle burst.
-- Every random choice is seeded so captures stay deterministic.
local composer = require("composer")
local scene = composer.newScene()

function scene:create(event)
    local group = self.view

    -- Tilemap background
    local tmap = display.newImageRect(group, "assets/tilemap.png", 1152, 672)
    tmap.x = display.contentCenterX
    tmap.y = display.contentCenterY - 180

    -- Sprite hero from shared atlas (frame 0)
    local opts = { width = 96, height = 96, numFrames = 24 }
    local sheet = graphics.newImageSheet("assets/creatures.png", opts)
    local hero = display.newSprite(group, sheet, { name = "idle", start = 1, count = 24, time = 2000 })
    hero.x, hero.y = display.contentCenterX, display.contentCenterY + 360
    hero:play()

    -- Particle overlay
    local fx = display.newImageRect(group, "assets/particles.png", 720, 420)
    fx.x = display.contentCenterX
    fx.y = display.contentCenterY - 180
    fx.alpha = 0.7
    fx.blendMode = "add"
end

scene:addEventListener("create", scene)
return scene
"""

PARTICLES_LUA = """-- particles.lua
-- Deterministic CPU particle emitter. Solar 2D's emitter API is fine, but we
-- wrote this in plain Lua so it round-trips into other Lua-first engines.
local M = {}

local function rand(state)
    state.s = (state.s * 1103515245 + 12345) % 2147483648
    return state.s / 2147483648
end

function M.burst(cx, cy, n, seed)
    local particles = {}
    local state = { s = seed or 17 }
    for i = 1, n do
        local angle = rand(state) * math.pi * 2
        local speed = 40 + rand(state) * 180
        local life = 0.3 + rand(state) * 0.7
        particles[i] = {
            x = cx, y = cy, vx = math.cos(angle) * speed,
            vy = math.sin(angle) * speed, life = life,
        }
    end
    return particles
end

return M
"""

CAPTURE_LUA = """-- capture.lua
-- Headless AI behavior capture: steps the simulation `n` times, writes one
-- row per tick to a CSV for downstream dataset use, then exits.
local M = {}

function M.run(n)
    local path = system.pathForFile("behavior.csv", system.DocumentsDirectory)
    local f = io.open(path, "w")
    f:write("t,hero_x,hero_y,action\\n")
    local t = 0
    for i = 1, n do
        t = t + 1/60
        -- Simulated AI policy: sine-weave horizontal + bounded vertical drift
        local x = display.contentCenterX + math.sin(t * 2) * 220
        local y = display.contentCenterY + math.cos(t * 1.3) * 80
        local action = (math.sin(t * 2) > 0) and "right" or "left"
        f:write(string.format("%.3f,%.2f,%.2f,%s\\n", t, x, y, action))
    end
    f:close()
    print("[capture] wrote " .. path)
    native.requestExit()
end

return M
"""


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "projects" / "solar2d"
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    (root / "main.lua").write_text(MAIN_LUA, encoding="utf-8")
    (root / "config.lua").write_text(CONFIG_LUA, encoding="utf-8")
    (root / "build.settings").write_text(BUILD_SETTINGS, encoding="utf-8")
    (root / "scene.lua").write_text(SCENE_LUA, encoding="utf-8")
    (root / "particles.lua").write_text(PARTICLES_LUA, encoding="utf-8")
    (root / "capture.lua").write_text(CAPTURE_LUA, encoding="utf-8")

    generate_sprite_atlas(assets / "creatures.png")
    generate_tilemap(assets / "tilemap.png")
    generate_particle_burst(assets / "particles.png", size=(720, 420))

    print(f"[ok] Solar 2D project at {root}")


if __name__ == "__main__":
    main()
