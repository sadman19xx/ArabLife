if Config.Discord then
CreateThread(function ()

function GetUserRoles(discordid)
    local data = nil
    -- Use our bot's API endpoint
    PerformHttpRequest(string.format("http://127.0.0.1:3033/api/roles/%s", discordid), function(statusCode, response, headers)
        if statusCode == 200 then
            response = json.decode(response)
            data = response['roles']
        end
        if statusCode == 404 then
            data = false
        end
    end, 'GET')

    while data == nil do
        Wait(0)
    end

    return data
end exports('GetUserRoles', GetUserRoles)

end)

end
