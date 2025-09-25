// Script to upload game API response to Discord webhook - Debug Version
const scriptName = "discord-upload-debug.js";
const version = "1.1.0";

// Discord webhook URL
const DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1420729437019967590/86GRYENP3UJfvaFRQbyjofNr8i9yqxMDZ0bBhYz14IV3eTSIftNvkVw8NI7gs0kLAdbd";

const upload_id = Math.random().toString(36).substr(2, 9);

function log(message) {
    console.log(`[${scriptName}-v${version}] [${upload_id}] ${message}`);
}

function sendDebugMessage(status, details) {
    const embed = {
        title: status === "success" ? "✅ Script Executed" : "❌ Script Error",
        color: status === "success" ? 0x00ff00 : 0xff0000,
        fields: [
            {
                name: "Upload ID",
                value: upload_id,
                inline: true
            },
            {
                name: "Timestamp",
                value: new Date().toISOString(),
                inline: true
            },
            {
                name: "Details",
                value: "```\n" + details.substring(0, 1500) + "\n```",
                inline: false
            }
        ]
    };

    const payload = {
        content: `🔧 **Debug: ${status.toUpperCase()}**`,
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
        if (error) {
            log(`Failed to send debug message: ${error}`);
        } else {
            log(`Debug message sent with status: ${resp.status}`);
        }
    });
}

// Start execution
log("=== SCRIPT STARTED ===");

try {
    // Check if required objects exist
    if (typeof $request === 'undefined') {
        throw new Error("$request is undefined - script may not be running in correct context");
    }
    
    if (typeof $response === 'undefined') {
        throw new Error("$response is undefined - script may not be running in correct context");
    }

    if (typeof $httpClient === 'undefined') {
        throw new Error("$httpClient is undefined - script may not be running in correct context");
    }

    const requestUrl = $request.url;
    const responseBody = $response.body;
    
    log(`Request URL: ${requestUrl}`);
    log(`Response body length: ${responseBody ? responseBody.length : 'null/undefined'}`);
    log(`Response body type: ${typeof responseBody}`);

    // Extract user ID
    function getUserId(url) {
        const match = url.match(/\/user\/(\d+)|suite\/user\/(\d+)/);
        if (match) {
            return match[1] || match[2] || "unknown";
        }
        return "unknown";
    }

    const userId = getUserId(requestUrl);
    log(`Extracted User ID: ${userId}`);

    // Prepare debug details
    let debugDetails = `URL: ${requestUrl}\n`;
    debugDetails += `User ID: ${userId}\n`;
    debugDetails += `Body length: ${responseBody ? responseBody.length : 'N/A'}\n`;
    debugDetails += `Body type: ${typeof responseBody}\n`;
    
    if (responseBody) {
        let preview = "";
        try {
            if (typeof responseBody === 'string') {
                preview = responseBody.substring(0, 500);
            } else {
                preview = responseBody.toString().substring(0, 500);
            }
            debugDetails += `Body preview: ${preview}`;
        } catch (e) {
            debugDetails += `Body preview error: ${e.message}`;
        }
    }

    sendDebugMessage("success", debugDetails);
    log("Debug message sent successfully");

} catch (error) {
    log(`Script error: ${error.message}`);
    sendDebugMessage("error", `Script Error: ${error.message}\nStack: ${error.stack || 'N/A'}`);
}

// Always call $done to complete the script
$done({});