local Debug = Config.Debug
local JoinDelay = GetGameTimer() + tonumber(Config.JoinDelay)
local MaxPlayers = GetConvarInt('sv_maxclients')
local HostName = GetConvar("sv_hostname") ~= "default FXServer" and GetConvar("sv_hostname") or false
local jsonCard = json.decode(LoadResourceFile(GetCurrentResourceName(), 'presentCard.json'))[1]

local prioritydata = {}
local queuelist = {}
local queuepositions = {}
local connectinglist = {}
local reconnectlist = {}
local playercount = 0


local randomEmojiStrings = {"🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐻", "🐨", "🐯", "🦁", "🐮", "🐷", "🐽", "🐸", "🐵"}

local function ChooseThreeRandomEmojis()
    local emojis = {}
    for i = 1, 3 do
        emojis[i] = randomEmojiStrings[math.random(1, #randomEmojiStrings)]
    end
    return emojis[1] .. emojis[2] .. emojis[3]
end

local function updateCard(data)
    local pCard = jsonCard
    local date = os.date( "%a %b %d, %H:%M")
    pCard.body[1]["columns"][1]["items"][2]["columns"][1]["items"][1].text = string.format('Queue: %d/%d', data.pos, data.maxpos)
    pCard.body[1]["columns"][1]["items"][3].text = ChooseThreeRandomEmojis()
    pCard.body[1]["columns"][2]["items"][2]["columns"][1]["items"][1].text = date.." EST" -- change the timezone based on your server machine timezone
    pCard.body[1]["columns"][2]["items"][2]["columns"][2]["items"][1].text = "Points: "..tostring(data.points)
    return pCard
end

local function getPrioData(identifier)
    return prioritydata[identifier]
end exports('getPrioData', getPrioData)

local function isInQueue(ids)
    local identifier = ids[Config.Identifier]
    local qpos, qdata = nil, nil
    for pos, data in ipairs(queuelist) do
        if data.id == identifier then
            qpos, qdata = pos, data
            break
        end
    end
    return qpos, qdata
end exports('isInQueue', isInQueue)

local function setQueuePos(identifier, newPos)
    if newPos <= 0 or newPos > #queuelist then return false end
    if not queuepositions[identifier] then return false end
    local currentPos = queuepositions[identifier]
    local data = queuelist[currentPos]
    if not data then return false end
    table.remove(queuelist, currentPos)
    table.insert(queuelist, newPos, data)
    queuepositions[identifier] = newPos

    return true
end exports('setQueuePos', setQueuePos)

local function getQueuePos(identifier)
    return queuepositions[identifier]
end exports('getQueuePos', getQueuePos)

local function updateQueuePositions()
    for k, v in ipairs(queuelist) do
        if k ~= queuepositions[v.id] then
            queuepositions[v.id] = k
        end
    end
    return true
end

local function addToQueue(ids, points)
    local index = #queuelist + 1
    local currentTime = os.time()
    local data = { id = ids[Config.Identifier], ids = ids, points = points, qTime = function() return (os.time()-currentTime) end }
    local newPos = index
    for pos, data in ipairs(queuelist) do
        if data.points >= points then
            newPos = pos + 1
        else
            newPos = pos
            break
        end
    end
    table.insert(queuelist, newPos, data)
    updateQueuePositions()

    return data
end

local function removeFromQueue(ids)
    local identifier = ids[Config.Identifier]
    for pos, data in ipairs(queuelist) do
        if identifier == data.id then
            queuepositions[identifier] = nil
            table.remove(queuelist, pos)
            updateQueuePositions()
            return true
        end
    end

    return false
end

local function isInConnecting(identifier)
    for pos, data in ipairs(connectinglist) do
        if identifier == data.id then
            return true, pos
        end
    end
    return false, false
end

local function addToConnecting(source, identifiers)
    if not source or not identifiers then return end
    local currentTime = os.time()
    local identifier = identifiers[Config.Identifier]
    local isConnecting, position = isInConnecting(identifier)
    if isConnecting then
        connectinglist[position] = {
            source = source,
            id = identifier,
            timeout = 0,
            cTime = function() return (os.time()-currentTime) end
        }
    else
        local index = #connectinglist + 1
        local cData = {
            source = source,
            id = identifier,
            timeout = 0,
            cTime = function() return (os.time()-currentTime) end
        }
        table.insert(connectinglist, index, cData)
    end
    removeFromQueue(identifiers)
end

local function removeFromConnecting(identifier)
    for pos, data in ipairs(connectinglist) do
        if identifier == data.id then
            table.remove(connectinglist, pos)
            break
        end
    end
end

local function canJoin()
    return (((#connectinglist + playercount) < MaxPlayers) and (JoinDelay <= GetGameTimer()))
end exports('canJoin', canJoin)

local function getIdentifiers(src)
    if not src then return nil end
    local identifiers = {}
    for _, id in ipairs(GetPlayerIdentifiers(src)) do
        local index = tostring(id:match("(%w+):"))
        identifiers[index] = id
    end
    return identifiers
end

-- Handle the "Play Now" Queue System
local function handleQueueSystem(deferrals, source, identifiers)
    -- If the player is in the connecting list, remove them
    if isInConnecting(identifiers[Config.Identifier]) then
        removeFromConnecting(identifiers[Config.Identifier])
        Wait(500)
    end

    -- Anti-spam prevention
    if Config.AntiSpam.enabled then
        deferrals.update(Lang.please_wait)
        Wait(math.random(Config.AntiSpam.time, Config.AntiSpam.time + 5000))
    end

    -- Check if identifiers exist
    if not identifiers then
        deferrals.done(Lang.ids_doesnt_exist)
        CancelEvent()
        return
    end

    -- Check required identifiers for connection
    for _, id in ipairs(Config.RequiredIdentifiers) do
        if not identifiers[id] then
            deferrals.done(string.format(Lang.id_doesnt_exist, id))
            CancelEvent()
            return
        end
    end

    -- Role-based priority check
    if Config.Discord.enabled then
        local playerroles = GetUserRoles(identifiers['discord'])
        if not playerroles then
            deferrals.done(Lang.join_discord)
            CancelEvent()
            return
        end

        local whitelisted = false
        local cIdentifier = identifiers[Config.Identifier]

        -- Clear and set priority data
        if prioritydata[cIdentifier] then prioritydata[cIdentifier] = {} end

        for _, role in pairs(playerroles) do
            if Config.Discord.roles[role] then
                if whitelisted then
                    prioritydata[cIdentifier].points = prioritydata[cIdentifier].points + Config.Discord.roles[role].points
                else
                    whitelisted = true
                    prioritydata[cIdentifier] = { points = Config.Discord.roles[role].points, name = Config.Discord.roles[role].name }
                end
            end
        end

        if not whitelisted then
            deferrals.done(Lang.not_whitelisted)
            CancelEvent()
            return
        end

        -- Handle reconnection priority
        if Config.ReconnectPrio.enabled and reconnectlist[cIdentifier] then
            prioritydata[cIdentifier].points = prioritydata[cIdentifier].points + Config.ReconnectPrio.points
        end
    end

    -- Direct join if server has room
    if canJoin() then
        addToConnecting(source, identifiers)
        deferrals.done()
        CancelEvent()
        return
    end

    -- Add player to queue if server is full
    local data = addToQueue(identifiers, prioritydata[identifiers[Config.Identifier]].points)
    if not data then
        deferrals.done(Lang.could_not_connect)
        CancelEvent()
        return
    end

    -- Queue handling loop
    while data and queuepositions[data.id] do
        Wait(3000)

        -- Join when at front of queue
        if queuepositions[data.id] <= 1 and canJoin() then
            addToConnecting(source, data.ids)
            deferrals.update(Lang.joining_now)
            Wait(1000)
            deferrals.done()
            CancelEvent()
            return
        end

        -- Check if player leaves queue
        if not GetPlayerEndpoint(source) then
            removeFromQueue(data.ids)
            deferrals.done(Lang.timed_out)
            CancelEvent()
            return
        end

        -- Present queue card
        local displayCard = updateCard({ pos = queuepositions[data.id], maxpos = #queuelist, points = data.points })
        deferrals.presentCard(displayCard, function(data, rawdata) end)
    end

    deferrals.done()
end

-- Event to Handle Player Connecting
AddEventHandler("playerConnecting", function(playerName, setKickReason, deferrals)
    local source = source
    local identifiers = getIdentifiers(source)
    deferrals.defer()

    Wait(0)
    local loadingProgress = 0
    local emojis = {"🌟", "🔄", "⏳", "🚀"}
    while loadingProgress < 100 do
        local emoji = emojis[math.random(1, #emojis)]  -- Randomize emoji for excitement
        local progressBar = string.rep("█", loadingProgress / 5) .. string.rep("░", (100 - loadingProgress) / 5)
        deferrals.update(string.format("%s [%s] %d%% Getting Ready for Adventure...", emoji, progressBar, loadingProgress))
        Wait(500)
        loadingProgress = loadingProgress + 20
    end

    local card = [[
    {
        "type": "AdaptiveCard",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "Image",
                        "url": "https://r2.fivemanage.com/EwcUuGvWswfqjdvkUfaFY/myLogo_NEW.png",
                        "size": "Medium",
                        "horizontalAlignment": "Center"
                    },
                    {
                        "type": "TextBlock",
                        "text": "Welcome To The Server !",
                        "weight": "Bolder",
                        "size": "ExtraLarge",
                        "horizontalAlignment": "Center"
                    },
                    {
                        "type": "TextBlock",
                        "text": "]] .. playerName .. [[",
                        "weight": "Bolder",
                        "size": "Large",
                        "color": "Attention",
                        "horizontalAlignment": "Center"
                    },
                    {
                        "type": "TextBlock",
                        "text": "We're Excited To Have You Here. Please Choose An Option Below To Begin.",
                        "wrap": true,
                        "horizontalAlignment": "Center"
                    },
                    {
                        "type": "ActionSet",
                        "horizontalAlignment": "Center",
                        "actions": [
                            {
                                "type": "Action.Submit",
                                "title": "🚀 Play Now",
                                "style": "positive",
                                "data": {
                                    "action": "play"
                                }
                            },
                            {
                                "type": "Action.OpenUrl",
                                "title": "🌐 Website",
                                "url": "https://www.arablife.gg/",
                                "style": "default"
                            },
                            {
                                "type": "Action.OpenUrl",
                                "title": "💿 Discord",
                                "url": "https://discord.gg/Ynz3CQ6w",
                                "style": "default"
                            },
                            {
                                "type": "Action.OpenUrl",
                                "title": "📜 Server Rules",
                                "url": "https://www.arablife.gg/rules"
                            }
                        ]
                    },
                    {
                        "type": "TextBlock",
                        "text": "You have 120 seconds to respond",
                        "color": "Warning",
                        "horizontalAlignment": "Center"
                    },
                    {
                    "type": "ColumnSet",
                    "spacing": "Medium",
                    "separator": true,
                    "columns": [
                        {
                            "type": "Column",
                            "width": 1,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "You Are Boarding!"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "Saudi Airlines",
                                    "size": "ExtraLarge",
                                    "color": "Accent",
                                    "spacing": "None"
                                }
                            ]
                        },
                        {
                            "type": "Column",
                            "width": "auto",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": " "
                                },
                                {
                                    "type": "Image",
                                    "url": "https://adaptivecards.io/content/airplane.png",
                                    "size": "Small"
                                }
                            ]
                        },
                        {
                            "type": "Column",
                            "width": 1,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "Los Santos International",
                                    "horizontalAlignment": "Right"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "LSIA",
                                    "horizontalAlignment": "Right",
                                    "size": "ExtraLarge",
                                    "color": "Accent",
                                    "spacing": "None"
                                }
                            ]
                        }
                    ]
                }
                ]
            }
        ],
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.3"
    }
    ]]
    
        local timeout = false

    deferrals.presentCard(card, function(data, rawData)
        if data.action == "play" then
            deferrals.update("We Are Checking Up Your Queue Priority")
            handleQueueSystem(deferrals, source, identifiers)
        else
            deferrals.done("You must click 'Play' to join the server.")  -- Handle other cases, if needed
        end
    end)
end)

-- Other Helper Functions (isInQueue, addToQueue, canJoin, etc.) should remain unchanged.


CreateThread(function()
    while true do
        Wait(5000)
        if #connectinglist < 1 then goto skipLoop end
        for pos, data in ipairs(connectinglist) do
            local endpoint = GetPlayerEndpoint(data.source)
            if not endpoint or data.cTime() >= Config.Timeout then
                removeFromConnecting(data.id)
                DebugPrint(string.format('%s has been timed out while connecting to server', data.id))
            end
        end
        ::skipLoop::
        local currentTime = os.time()
        for identifier, expire in pairs(reconnectlist) do
            if expire < currentTime then
                reconnectlist[identifier] = nil
            end
        end
    end
end)

AddEventHandler("playerJoining", function(source, oldid)
    local identifiers = getIdentifiers(source)

    playercount = playercount + 1
    removeFromConnecting(identifiers[Config.Identifier])
end)

AddEventHandler("playerDropped", function()
    local source = source
    local identifiers = getIdentifiers(source)
    playercount = playercount - 1

    if Config.ReconnectPrio.enabled then
        reconnectlist[identifiers[Config.Identifier]] = os.time() + (Config.ReconnectPrio.time * 60)
    end
end)

AddEventHandler('onResourceStart', function(resource)
    if resource ~= GetCurrentResourceName() then return end
    local playerPool = GetPlayers()
    playercount = #playerPool
    DebugPrint('Players: '..playercount)
end)

local function getQueueCount()
    return queuelist
end exports('getQueueCount', getQueueCount)