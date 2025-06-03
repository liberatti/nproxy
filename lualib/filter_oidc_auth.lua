local jwt = require "resty.jwt"

-- Função para validar JWT
local function validate_jwt()
    local auth_header = ngx.var.http_Authorization
    if not auth_header then
        ngx.status = ngx.HTTP_UNAUTHORIZED
        ngx.say("Authorization header missing")
        return ngx.exit(ngx.HTTP_UNAUTHORIZED)
    end

    -- Extrair o token JWT do header
    local _, _, token = string.find(auth_header, "Bearer%s+(.+)")
    if not token then
        ngx.status = ngx.HTTP_UNAUTHORIZED
        ngx.say("Invalid Authorization header format")
        return ngx.exit(ngx.HTTP_UNAUTHORIZED)
    end

    -- Decodificar e verificar o JWT
    local jwt_obj = jwt:decode(token)
    if not jwt_obj or jwt_obj.err then
        ngx.status = ngx.HTTP_UNAUTHORIZED
        ngx.say("Invalid JWT")
        return ngx.exit(ngx.HTTP_UNAUTHORIZED)
    end

    -- Opcional: Validar se o token ainda não expirou
    if jwt_obj.payload.exp and jwt_obj.payload.exp < ngx.time() then
        ngx.status = ngx.HTTP_UNAUTHORIZED
        ngx.say("JWT expired")
        return ngx.exit(ngx.HTTP_UNAUTHORIZED)
    end

    -- Caso o token seja válido, apenas continue
    return true
end

-- Chama a função para validar JWT
return validate_jwt()
