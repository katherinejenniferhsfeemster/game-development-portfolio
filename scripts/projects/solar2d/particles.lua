-- particles.lua
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
