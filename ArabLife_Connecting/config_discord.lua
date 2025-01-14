Config = Config or {}

Config.Discord = {
    enabled = true, -- you want whitelist/priority modules?
    bottoken = GetConvar('DISCORD_BOT_TOKEN', ''), -- bot token from environment variable
    serverid = GetConvar('DISCORD_SERVER_ID', ''), -- discord serverid from environment variable
    roles = {
        -- roleid = table (name, points)
        ['1309555494586683474'] = {name = "Allowlisted", points = 0},
        -- ['<role_id2>'] = {name = "Member", points = 1000},
        -- ['<role_id3>'] = {name = "VIP", points = 2000},
        -- ['<role_id4>'] = {name = "Moderator", points = 3000},
        -- ['<role_id5>'] = {name = "Admin", points = 4000},
    }
}
