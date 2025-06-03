local cjson = require "cjson"

description = "Unexcepted error"
if ngx.status == 404 then
    description = "Resource not found"
elseif ngx.status == 403 then
    description = "Access forbidden"
elseif ngx.status == 500 then
    description = "Internal server error"
end

local resposta = {
    remote_addr = ngx.var.remote_addr,
    request_id = ngx.var.request_id,
    status = ngx.status,
    description = description,
    request = ngx.var.request
}

ngx.header["Content-Type"] = "application/json"
ngx.say(cjson.encode(resposta))