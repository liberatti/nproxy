local ldap = require "lualdap"
local cjson = require "cjson"
local base64 = require "base64"

local function authenticate(username, password)
    local ld, err_o = ldap.open(ngx.var.ldap_host)
    if not ld then
        return nil, "Failed to connect to LDAP server: " .. err_o
    end

    local res, err_b = ld:bind_simple(ngx.var.ldap_bind_dn, ngx.var.ldap_bind_password)
    if not res then
        return nil, "LDAP bind failed: " .. err_b
    end

    local filter = string.format("(&(objectClass=user)(sAMAccountName=%s))", username)
    for dn, attribs in ld:search { base = ngx.var.ldap_base_dn, filter = filter, scope = "subtree" } do
        local res_b, err_s = ld:bind_simple(dn, password)
        if not res_b then
            return nil, "Login Failed: " .. err_s
        end

        if ngx.var.ldap_group_dn then
            local group_member = false
            for _, group in ipairs(attribs.memberOf or {}) do
                local group_str = string.gsub(group, "^%s*(.-)%s*$", "%1")
                if string.lower(group_str) == string.lower(ngx.var.ldap_group_dn) then
                    group_member = true
                    break
                end
            end
            if not group_member then
                return nil, "User not authorized by group"
            end
        end
    end
    return true
end

local function get_basic_auth_credentials()
    local auth_header = ngx.var.http_authorization
    if auth_header then
        local _, _, auth_type, credentials = string.find(auth_header, "^(%S+)%s+(.+)$")
        if auth_type == "Basic" then
            local decoded = base64.decode(credentials)
            if decoded then
                local username, password = string.match(decoded, "([^:]+):(.+)")
                if username and password then
                    return username, password
                end
            end
        end
    end
    return nil, "Authorization header invalid"
end

local username, password, err = get_basic_auth_credentials()
if not username then
    ngx.status = 401
    ngx.header["WWW-Authenticate"] = 'Basic realm="Restricted Area"'
    ngx.say(cjson.encode({ error = err }))
    ngx.exit(401)
end

local success, err_l = authenticate(username, password)
if not success then
    ngx.status = 403
    ngx.say(cjson.encode({ error = "Access forbidden", message = err_l }))
    ngx.exit(403)
end