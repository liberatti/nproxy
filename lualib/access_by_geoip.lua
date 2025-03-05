local http = require "resty.http"
local cjson = require "cjson"

local NODE_KEY = os.getenv("NODE_KEY") or "DEV"
local API_URL = "http://localhost:5000/api/cluster/ipinfo"

local cached_data = ngx.shared.geoip_cache:get(ngx.var.remote_addr)
if not cached_data then
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
        ngx.status = 403
        ngx.say(cjson.encode({ error = "GeoIp failed", message = err }))
        ngx.exit(403)
    end

    local data = cjson.decode(res.body)
    if data and data.country then
        ngx.shared.geoip_cache:set(ngx.var.remote_addr, data.country, 60)  -- 60 seconds
        cached_data = data.country
        ngx.log(ngx.DEBUG, "GeoIP cache set: " .. data)
    else
        ngx.log(ngx.DEBUG, "GeoIP not found for: " .. ngx.var.remote_addr)
    end

end
if string.match(ngx.var.block_countries, "%f[%a]" .. cached_data .. "%f[%A]") then
    ngx.status = 403
    ngx.say(cjson.encode({ error = "GeoIP Deny" }))
    ngx.exit(403)
end