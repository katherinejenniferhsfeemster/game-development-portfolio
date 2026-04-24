-- scene.lua
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
