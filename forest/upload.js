// Script to upload game API response to Discord webhook
const scriptName = "discord-upload.js";
const version = "1.0.0";

// Replace with your Discord webhook URL
const DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1420729437019967590/86GRYENP3UJfvaFRQbyjofNr8i9yqxMDZ0bBhYz14IV3eTSIftNvkVw8NI7gs0kLAdbd";

const upload_id = Math.random().toString(36).substr(2, 9);
const body = $response.body;

function log(message) {
    console.log(`[${scriptName}-v${version}] [${upload_id}] ${message}`);
}

function getUserId(url) {
    const match = url.match(/\/user\/(\d+)|suite\/user\/(\d+)/);
    if (match) {
        return match[1] || match[2] || "unknown";
    }
    return "unknown";
}

function sendToDiscord(data, userId, originalUrl) {
    // Convert binary data to base64 for Discord
    const base64Data = data.toString('base64');
    
    // Create Discord embed
    const embed = {
        title: "🎮 Game API Data Captured",
        color: 0x00ff00,
        fields: [
            {
                name: "User ID",
                value: userId,
                inline: true
            },
            {
                name: "Data Size",
                value: `${data.length} bytes`,
                inline: true
            },
            {
                name: "Upload ID",
                value: upload_id,
                inline: true
            },
            {
                name: "Original URL",
                value: originalUrl.length > 1024 ? originalUrl.substring(0, 1021) + "..." : originalUrl,
                inline: false
            }
        ],
        timestamp: new Date().toISOString()
    };

    const payload = {
        embeds: [embed]
    };

    // If data is small enough, include it in the embed
    if (base64Data.length < 4000) {
        embed.fields.push({
            name: "Data (Base64)",
            value: "```" + base64Data.substring(0, 4000) + "```",
            inline: false
        });
    }

    const options = {
        method: "POST",
        url: DISCORD_WEBHOOK_URL,
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    };

    log(`Sending data to Discord for user ${userId}`);

    $httpClient.post(options, (error, resp, data) => {
        if (error || resp.status !== 200 && resp.status !== 204) {
            log(`Discord upload failed: ${error || `HTTP ${resp.status}`}`);
        } else {
            log(`Successfully sent to Discord`);
        }
        $done({});
    });
}

function sendLargeDataToDiscord(data, userId, originalUrl) {
    // For large data, save to file and send file info
    const embed = {
        title: "🎮 Large Game API Data Captured",
        color: 0xffaa00,
        description: "Data too large for Discord message. File would need to be uploaded separately.",
        fields: [
            {
                name: "User ID",
                value: userId,
                inline: true
            },
            {
                name: "Data Size",
                value: `${data.length} bytes`,
                inline: true
            },
            {
                name: "Upload ID",
                value: upload_id,
                inline: true
            },
            {
                name: "Original URL",
                value: originalUrl.length > 1024 ? originalUrl.substring(0, 1021) + "..." : originalUrl,
                inline: false
            }
        ],
        timestamp: new Date().toISOString()
    };

    const payload = {
        content: `@here Large API response captured (${data.length} bytes)`,
        embeds: [embed]
    };

    const options = {
        method: "POST",
        url: DISCORD_WEBHOOK_URL,
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    };

    $httpClient.post(options, (error, resp, data) => {
        if (error || resp.status !== 200 && resp.status !== 204) {
            log(`Discord upload failed: ${error || `HTTP ${resp.status}`}`);
        } else {
            log(`Successfully sent large data notification to Discord`);
        }
        $done({});
    });
}

const userId = getUserId($request.url);

log(`Capturing API response for user ${userId}`);
log(`Content length: ${body.length}`);
log(`Original URL: ${$request.url}`);

if (body && body.length > 0) {
    // Discord has message limits, so handle large data differently
    if (body.length > 1000000) { // 1MB limit
        sendLargeDataToDiscord(body, userId, $request.url);
    } else {
        sendToDiscord(body, userId, $request.url);
    }
} else {
    log("Response body is empty, nothing to upload.");
    $done({});
}