local http = require "resty.http"
local cjson = require "cjson"

local function msg(code, _msg)
    ngx.status = code
    ngx.say(cjson.encode({ error = "Access forbidden", message = _msg }))
    ngx.exit(code)
end

local addr_country = ngx.shared["geoip_cache"]:get(ngx.var.remote_addr)
if not addr_country then
    local httpc = http.new()
    local res, err = httpc:request_uri(ngx.var.geo_api .. "/" .. ngx.var.remote_addr, {
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json",
            ["x-cluster-key"] = ngx.var.geo_key,
        }
    })
    if res and (res.status == 200 or res.status == 201) then
        local data, decode_err = cjson.decode(res.body)
        if not data then
            msg(500, "GeoIP blocked" .. "Error decoding GeoIP data: " .. decode_err)
        end
        ngx.shared.geoip_cache:set(ngx.var.remote_addr, data.country, 60)
        addr_country = data.country
        --ngx.log(ngx.ERR, "GeoIP Search: " .. ngx.var.geo_api .. "/" .. ngx.var.remote_addr .. ":" .. cjson.encode(data))
    else
        msg(500, "GeoIP blocked" .. "Error fetching GeoIP data: " .. err)
    end
end

if string.match(ngx.var.geo_block_list, "%f[%a]" .. addr_country .. "%f[%A]") then
    ngx.header["X-GeoIP-Country"] = addr_country
    ngx.var.geo_block = "DENY"
    msg(403, "GeoIP blocked: " .. ngx.var.remote_addr)
else
    ngx.var.geo_block = "PASS"
end