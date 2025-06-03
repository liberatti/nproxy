local http = require "resty.http"
local cjson = require "cjson"

local function get_client_ip()
    local ip = ngx.var.http_x_forwarded_for
    if ip == nil or ip == "" then
        ip = ngx.var.http_x_real_ip
    end
    if ip == nil or ip == "" then
        ip = ngx.var.remote_addr
    end
    if ip then
        local first_ip = string.match(ip, "([^,]+)")
        return first_ip or ip
    end
    return ngx.var.remote_addr
end

local function msg(code, _msg)
    ngx.status = code
    ngx.say(cjson.encode({ error = "Access forbidden", message = _msg }))
    ngx.exit(code)
end

local api_headers = {
    ["Content-Type"] = "application/json",
    ["x-cluster-key"] = ngx.var.api_key,
}
local client_ip = get_client_ip()
local addr_action = ngx.shared["si_" .. ngx.var.sensor_id .. "_cache"]:get(client_ip)
if not addr_action then
    local httpc = http.new()
    local res, err = httpc:request_uri(ngx.var.api_url .. "/cluster/rbl/blocked/" .. ngx.var.sensor_id .. "/" .. client_ip, {
        method = "GET",
        headers = api_headers
    })
    if res and (res.status == 200 or res.status == 201) then
        local data, decode_err = cjson.decode(res.body)
        if not data then
            msg(500, "RBL blocked" .. "Error decoding RBL data: " .. decode_err)
        end

        ngx.shared["si_" .. ngx.var.sensor_id .. "_cache"]:set(client_ip, data.blocked, 60)
        addr_action = data.blocked
        --ngx.log(ngx.ERR, "RBL Search: " .. client_ip .. ":" .. cjson.encode(data))
    else
        msg(500, "RBL blocked" .. "Error fetching RBL data: " .. err)
    end
end

if addr_action then
    ngx.var.rbl_status = "REJECTED"
    msg(403, "RBL blocked: " .. client_ip)
else
    ngx.var.rbl_status = "PASSED"
end

if ngx.var.geo_block_list then
    local addr_country = ngx.shared["geoip_cache"]:get(client_ip)
    if not addr_country then
        local httpc = http.new()
        local res, err = httpc:request_uri(ngx.var.api_url .. "/cluster/geoip_info/" .. client_ip, {
            method = "GET",
            headers = api_headers
        })
        if res and (res.status == 200 or res.status == 201) then
            local data, decode_err = cjson.decode(res.body)
            if not data then
                msg(500, "GeoIP blocked" .. "Error decoding GeoIP data: " .. decode_err)
            end
            ngx.shared.geoip_cache:set(client_ip, data.country, 60)
            addr_country = data.country
            --ngx.log(ngx.ERR, "GeoIP Search: " .. ngx.var.geo_api .. "/" .. client_ip .. ":" .. cjson.encode(data))
        else
            msg(500, "GeoIP blocked" .. "Error fetching GeoIP data: " .. err)
        end
    end
    if not addr_country then
        addr_country = "Unknown"
        ngx.shared.geoip_cache:set(client_ip, addr_country, 60)
    end
    ngx.header["X-GeoIP-Country"] = addr_country
    if string.match(ngx.var.geo_block_list, "%f[%a]" .. addr_country .. "%f[%A]") then
        ngx.var.geoip_status = "REJECTED"
        msg(403, "GeoIP blocked: " .. client_ip)
    else
        ngx.var.geoip_status = "PASSED"
    end
end

