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

function sendSuccessToDiscord(data, userId, originalUrl) {
    // Get first 2000 characters of response for preview
    let dataPreview = "";
    try {
        if (typeof data === 'string') {
            dataPreview = data.substring(0, 2000);
        } else if (data && data.length) {
            // Try to convert to string first
            dataPreview = data.toString().substring(0, 2000);
        }
    } catch (e) {
        dataPreview = "[Binary data - cannot preview]";
    }

    const embed = {
        title: "✅ Game API Data Captured Successfully",
        color: 0x00ff00,
        description: "Successfully intercepted game API response",
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
                name: "URL",
                value: originalUrl.length > 100 ? originalUrl.substring(0, 97) + "..." : originalUrl,
                inline: false
            },
            {
                name: "Data Preview (First 2000 chars)",
                value: dataPreview.length > 0 ? "```json\n" + dataPreview + "\n```" : "No preview available",
                inline: false
            }
        ],
        timestamp: new Date().toISOString()
    };

    const payload = {
        content: "🎮 **API Capture Success**",
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

    log(`Sending success message to Discord for user ${userId}`);

    $httpClient.post(options, (error, resp, responseData) => {
        if (error || (resp.status !== 200 && resp.status !== 204)) {
            log(`Discord upload failed: ${error || `HTTP ${resp.status}`}`);
            // Send failure message
            sendFailureToDiscord(error || `HTTP ${resp.status}`, userId, originalUrl);
        } else {
            log(`Successfully sent success message to Discord`);
        }
        $done({});
    });
}

function sendFailureToDiscord(errorInfo, userId, originalUrl) {
    // Get first 3000 characters of error for debugging
    let errorPreview = "";
    try {
        if (typeof errorInfo === 'string') {
            errorPreview = errorInfo.substring(0, 3000);
        } else if (errorInfo) {
            errorPreview = JSON.stringify(errorInfo).substring(0, 3000);
        }
    } catch (e) {
        errorPreview = "Error details unavailable";
    }

    const embed = {
        title: "❌ Game API Capture Failed",
        color: 0xff0000,
        description: "Failed to process game API response",
        fields: [
            {
                name: "User ID",
                value: userId || "unknown",
                inline: true
            },
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
                name: "URL",
                value: originalUrl ? (originalUrl.length > 100 ? originalUrl.substring(0, 97) + "..." : originalUrl) : "unknown",
                inline: false
            },
            {
                name: "Error Details (First 3000 chars)",
                value: errorPreview.length > 0 ? "```\n" + errorPreview + "\n```" : "No error details available",
                inline: false
            }
        ],
        timestamp: new Date().toISOString()
    };

    const payload = {
        content: "🚨 **API Capture Failed**",
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

    log(`Sending failure message to Discord`);

    $httpClient.post(options, (error, resp, data) => {
        if (error || (resp.status !== 200 && resp.status !== 204)) {
            log(`Failed to send failure message to Discord: ${error || `HTTP ${resp.status}`}`);
        } else {
            log(`Successfully sent failure message to Discord`);
        }
        $done({});
    });
}

// Main execution
const userId = getUserId($request.url);

log(`Starting API capture for user ${userId}`);
log(`Content length: ${body ? body.length : 0}`);
log(`Original URL: ${$request.url}`);

try {
    if (body && body.length > 0) {
        sendSuccessToDiscord(body, userId, $request.url);
    } else {
        log("Response body is empty");
        sendFailureToDiscord("Response body is empty or undefined", userId, $request.url);
    }
} catch (error) {
    log(`Error during processing: ${error}`);
    sendFailureToDiscord(error.toString(), userId, $request.url);
}