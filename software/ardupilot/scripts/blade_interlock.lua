--[[
Orbitist blade interlock (ArduPilot Rover 4.6 Lua script).

The blade relay (K5 in hardware/electrical) is driven ONLY by this script. Missions ask for
the blade with MAV_CMD_DO_SEND_SCRIPT_MESSAGE (id = BLD_MSG_ID, param2 = 1 on / 0 off); the
script turns the relay on only while every condition holds:

  armed  AND  mode == AUTO  AND  GPS fix >= BLD_MIN_FIX  AND  no fence breach
  AND  tilt < BLD_TILT_DEG  AND  e-stop loop OK  AND  blade requested

If the e-stop loop opens, the script also disarms. The hardware e-stop drops the relay coil
supply independently of this script (hardware/electrical/README.md section 2), so this is the
second layer, not the only one.

Parameters (BLD_*):
  BLD_RELAY      relay instance wired to the blade relay (0 = RELAY1)
  BLD_MIN_FIX    minimum GPS fix: 6 = RTK fixed (hardware), 3 = 3D (SITL)
  BLD_TILT_DEG   max roll/pitch with the blade running
  BLD_ESTOP_SRC  1 = GPIO pin BLD_ESTOP_PIN (high = OK), 2 = BLD_ESTOP_SIM param (SITL only)
  BLD_ESTOP_PIN  GPIO number of the ESTOP_OK optocoupler input
  BLD_ESTOP_SIM  1 = loop OK, 0 = tripped (SITL test hook)
  BLD_MSG_ID     DO_SEND_SCRIPT_MESSAGE id that carries blade on/off
  BLD_FIX_PAUSE  seconds below BLD_MIN_FIX in AUTO before the script pauses the robot (Hold);
                 it resumes AUTO after the fix has been good for 3 s. 0 = blade-off only.

GPS pause: without it, ArduPilot dead-reckons for ~10+ s after losing GPS and the robot keeps
driving (~8 m in SITL) before the EKF failsafe stops it. RTK can drop briefly near trees, so the
script pauses and resumes rather than ending the mission.
--]]

local TABLE_KEY = 48
local PREFIX = "BLD_"
local MODE_AUTO = 10
local MODE_HOLD = 4
local LOOP_MS = 50

assert(param:add_table(TABLE_KEY, PREFIX, 8), "BLD: could not add param table")
local defaults = {
    { "RELAY", 0 }, { "MIN_FIX", 6 }, { "TILT_DEG", 25 }, { "ESTOP_SRC", 1 },
    { "ESTOP_PIN", -1 }, { "ESTOP_SIM", 1 }, { "MSG_ID", 1 }, { "FIX_PAUSE", 2 },
}
for i, d in ipairs(defaults) do
    assert(param:add_param(TABLE_KEY, i, d[1], d[2]), "BLD: could not add " .. d[1])
end

local function p(name)
    return param:get(PREFIX .. name)
end

local requested = false
local blade_on = false
local last_reason = ""
local last_report_ms = uint32_t(0)
local pin_configured = -1
local fix_bad_since = nil
local fix_good_since = nil
local paused_for_fix = false
local last_armed = nil
local reported_blade = nil

local function estop_ok()
    local src = p("ESTOP_SRC")
    if src == 2 then
        return p("ESTOP_SIM") >= 0.5
    end
    local pin = math.floor(p("ESTOP_PIN"))
    if pin < 0 then
        return false -- unconfigured input is treated as tripped (fail safe)
    end
    if pin_configured ~= pin then
        gpio:pinMode(pin, 0)
        pin_configured = pin
    end
    return gpio:read(pin)
end

local function blocking_reason()
    if not estop_ok() then return "e-stop" end
    if not arming:is_armed() then return "disarmed" end
    if vehicle:get_mode() ~= MODE_AUTO then return "not AUTO" end
    if not requested then return "not requested" end
    if gps:status(gps:primary_sensor()) < p("MIN_FIX") then return "GPS fix" end
    if fence:get_breaches() ~= 0 then return "fence" end
    local tilt = math.deg(math.max(math.abs(ahrs:get_roll()), math.abs(ahrs:get_pitch())))
    if tilt >= p("TILT_DEG") then return "tilt" end
    return nil
end

local function set_blade(on, reason)
    local relay_num = math.floor(p("RELAY"))
    if on then relay:on(relay_num) else relay:off(relay_num) end
    if on ~= blade_on or (not on and reason ~= last_reason) then
        gcs:send_text(on and 6 or 4, on and "Blade ON" or ("Blade OFF: " .. reason))
    end
    blade_on = on
    last_reason = reason or ""
end

local function update()
    -- Mission requests (DO_SEND_SCRIPT_MESSAGE)
    local time_ms, id, p2 = mission_receive()
    if time_ms and id == math.floor(p("MSG_ID")) then
        requested = (p2 ~= nil and p2 >= 0.5)
    end

    if not estop_ok() and arming:is_armed() then
        arming:disarm()
        gcs:send_text(2, "ESTOP loop open: disarmed")
    end
    if not arming:is_armed() then
        requested = false -- a new arming never inherits an old blade request
    end

    -- GPS pause / resume
    local fix_ok = gps:status(gps:primary_sensor()) >= p("MIN_FIX")
    local now = millis():tofloat() * 0.001
    if fix_ok then
        fix_bad_since = nil
        fix_good_since = fix_good_since or now
    else
        fix_good_since = nil
        fix_bad_since = fix_bad_since or now
    end
    local pause_s = p("FIX_PAUSE")
    if pause_s > 0 and arming:is_armed() then
        if vehicle:get_mode() == MODE_AUTO and fix_bad_since and now - fix_bad_since >= pause_s then
            vehicle:set_mode(MODE_HOLD)
            paused_for_fix = true
            gcs:send_text(4, "GPS fix lost: paused (Hold)")
        elseif paused_for_fix and vehicle:get_mode() == MODE_HOLD and fix_good_since and now - fix_good_since >= 3 then
            paused_for_fix = false
            vehicle:set_mode(MODE_AUTO)
            gcs:send_text(5, "GPS fix back: resuming mission")
        end
    end
    if vehicle:get_mode() ~= MODE_HOLD then
        paused_for_fix = false -- operator took over; never resume on our own after that
    end

    local reason = blocking_reason()
    set_blade(reason == nil, reason)

    -- Telemetry: periodic, plus immediately on any change (precise timing in logs and tests).
    local armed = arming:is_armed()
    if armed ~= last_armed then
        gcs:send_named_float("ARMED", armed and 1 or 0)
        last_armed = armed
    end
    if millis() - last_report_ms > 500 or blade_on ~= reported_blade then
        gcs:send_named_float("BLADE", blade_on and 1 or 0)
        reported_blade = blade_on
        last_report_ms = millis()
    end
end

-- Any script error forces the blade off and keeps the interlock running.
local function protected()
    local ok, err = pcall(update)
    if not ok then
        relay:off(math.floor(p("RELAY")))
        blade_on = false
        gcs:send_text(0, "Blade interlock error: " .. tostring(err))
    end
    return protected, LOOP_MS
end

relay:off(math.floor(p("RELAY")))
gcs:send_text(6, "Blade interlock loaded")
return protected, 1000
