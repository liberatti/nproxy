local http = require "resty.http"
local cjson = require "cjson"

local function msg(code, _msg)
    ngx.status = code
    ngx.say(cjson.encode({ error = "Access forbidden", message = _msg }))
    ngx.exit(code)
end

local api_headers = {
    ["Content-Type"] = "application/json",
    ["x-cluster-key"] = ngx.var.api_key,
}
local addr_action = ngx.shared["si_" .. ngx.var.sensor_id .. "_cache"]:get(ngx.var.remote_addr)
if not addr_action then
    local httpc = http.new()
    local res, err = httpc:request_uri(ngx.var.api_url .. "/cluster/rbl/blocked/" .. ngx.var.sensor_id .. "/" .. ngx.var.remote_addr, {
        method = "GET",
        headers = api_headers
    })
    if res and (res.status == 200 or res.status == 201) then
        local data, decode_err = cjson.decode(res.body)
        if not data then
            msg(500, "RBL blocked" .. "Error decoding RBL data: " .. decode_err)
        end

        ngx.shared["si_" .. ngx.var.sensor_id .. "_cache"]:set(ngx.var.remote_addr, data.blocked, 60)
        addr_action = data.blocked
        --ngx.log(ngx.ERR, "RBL Search: " .. ngx.var.remote_addr .. ":" .. cjson.encode(data))
    else
        msg(500, "RBL blocked" .. "Error fetching RBL data: " .. err)
    end
end

if addr_action then
    ngx.var.rbl_block = "DENY"
    msg(403, "RBL blocked: " .. ngx.var.remote_addr)
else
    ngx.var.rbl_block = "PASS"
end

if ngx.var.geo_block_list then
    local addr_country = ngx.shared["geoip_cache"]:get(ngx.var.remote_addr)
    if not addr_country then
        local httpc = http.new()
        local res, err = httpc:request_uri(ngx.var.api_url .. "/cluster/geoip_info/" .. ngx.var.remote_addr, {
            method = "GET",
            headers = api_headers
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
    ngx.header["X-GeoIP-Country"] = addr_country
    if string.match(ngx.var.geo_block_list, "%f[%a]" .. addr_country .. "%f[%A]") then
        ngx.var.geo_block = "DENY"
        msg(403, "GeoIP blocked: " .. ngx.var.remote_addr)
    else
        ngx.var.geo_block = "PASS"
    end
end

