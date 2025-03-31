local http = require "resty.http"
local cjson = require "cjson"

local NODE_KEY = os.getenv("NODE_KEY") or "DEV"
local API_URL = "http://localhost:5000/api/cluster/geoip_info"

local geoip_cached_addr = ngx.shared["geoip_cache"]:get(ngx.var.remote_addr)
local bl_cached_addr = ngx.shared[ngx.var.sensor_name .. "_bl_cache"]:get(ngx.var.remote_addr)

if not geoip_cached_addr or not bl_cached_addr then
    local httpc = http.new()
    local res, err = httpc:request_uri(API_URL .. "/" .. ngx.var.remote_addr, {
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json",
            ["x-cluster-key"] = NODE_KEY,
        }
    })

    if not res then
        ngx.log(ngx.DEBUG, "GeoIp failed: " .. err)
    end

    local data = cjson.decode(res.body)
    if data then
        if data.country then
            ngx.shared.geoip_cache:set(ngx.var.remote_addr, data.country, 60)  -- 60 seconds
            geoip_cached_addr = data.country
            ngx.log(ngx.DEBUG, "GeoIP cache set: " .. data)
        else
            ngx.log(ngx.DEBUG, "GeoIP not found for: " .. ngx.var.remote_addr)
    end

end
if string.match(ngx.var.block_countries, "%f[%a]" .. geoip_cached_addr .. "%f[%A]") then
    ngx.req.set_header("X-Sensor-Block", "geoip")
end

-- ngx.req.set_header("X-Sensor-Block", "geoip")
-- set_by_lua_file $custom_header /path/to/set_header.lua;
-- SecRule REQUEST_HEADERS:X-Sensor-Block "@eq geoip" "id:1000001,phase:1,deny,ctl:ruleEngine=Off"
-- SecRule REQUEST_HEADERS:X-Sensor-Block "@eq rbl" "id:1000001,phase:1,deny,ctl:ruleEngine=Off"
-- SecRule REQUEST_HEADERS:X-Sensor-Block "@eq jail" "id:1000001,phase:1,deny,ctl:ruleEngine=Off"