-- capture.lua
-- Headless AI behavior capture: steps the simulation `n` times, writes one
-- row per tick to a CSV for downstream dataset use, then exits.
local M = {}

function M.run(n)
    local path = system.pathForFile("behavior.csv", system.DocumentsDirectory)
    local f = io.open(path, "w")
    f:write("t,hero_x,hero_y,action\n")
    local t = 0
    for i = 1, n do
        t = t + 1/60
        -- Simulated AI policy: sine-weave horizontal + bounded vertical drift
        local x = display.contentCenterX + math.sin(t * 2) * 220
        local y = display.contentCenterY + math.cos(t * 1.3) * 80
        local action = (math.sin(t * 2) > 0) and "right" or "left"
        f:write(string.format("%.3f,%.2f,%.2f,%s\n", t, x, y, action))
    end
    f:close()
    print("[capture] wrote " .. path)
    native.requestExit()
end

return M
