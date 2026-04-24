-- main.lua
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
