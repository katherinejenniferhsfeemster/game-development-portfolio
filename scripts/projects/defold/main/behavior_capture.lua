-- behavior_capture.lua
-- Runs the game headless for N steps, writes behavior.csv, exits.
-- Invoked from CI:  defold-build -- lua main/behavior_capture.lua
local steps = tonumber(arg[1] or "600")
sys.set_config("behavior.capture", "1")
for i = 1, steps do
    msg.post("main:/hero", "simulate_step")
end
msg.post("@system:", "exit", { code = 0 })
