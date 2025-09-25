// Game API capture script for Discord - Fixed version
const DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1420729437019967590/86GRYENP3UJfvaFRQbyjofNr8i9yqxMDZ0bBhYz14IV3eTSIftNvkVw8NI7gs0kLAdbd";

const scriptName = "pjsk-discord-capture-fixed";
const version = "1.2.0";
const upload_id = Math.random().toString(36).substr(2, 9);

function log(message) {
    console.log(`[${scriptName}] [${upload_id}] ${message}`);
}

function getUserId(url) {
    const match = url.match(/\/user\/(\d+)|suite\/user\/(\d+)/);
    if (match) {
        return match[1] || match[2] || "unknown";
    }
    return "unknown";
}

function getApiType(url) {
    if (url.includes("/mysekai")) {
        return "MySekai Data";
    } else if (url.includes("/suite/user/")) {
        return "Suite Data";
    }
    return "Unknown API";
}

function sendToDiscord(success, data = null, error = null) {
    const userId = getUserId($request.url);
    const apiType = getApiType($request.url);
    const timestamp = new Date().toISOString();
    
    let embed;
    let content;

    if (success) {
        // Success message
        let dataPreview = "No data available";
        let dataSize = 0;
        
        if (data) {
            dataSize = data.length;
            try {
                // Handle binary data properly
                let dataString = "";
                if (typeof data === 'string') {
                    dataString = data;
                } else if (data.constructor === ArrayBuffer || data.constructor === Uint8Array) {
                    // Convert binary to string for preview
                    const decoder = new TextDecoder('utf-8');
                    dataString = decoder.decode(data);
                } else {
                    dataString = data.toString();
                }
                dataPreview = dataString.substring(0, 2000);
            } catch (e) {
                dataPreview = `[Binary data - ${e.message}]`;
            }
        }

        embed = {
            title: "✅ Game API Data Captured",
            color: 0x00ff00,
            description: `Successfully captured ${apiType}`,
            fields: [
                {
                    name: "User ID",
                    value: userId,
                    inline: true
                },
                {
                    name: "API Type",
                    value: apiType,
                    inline: true
                },
                {
                    name: "Data Size",
                    value: `${dataSize} bytes`,
                    inline: true
                },
                {
                    name: "Upload ID",
                    value: upload_id,
                    inline: true
                },
                {
                    name: "Timestamp",
                    value: timestamp,
                    inline: true
                },
                {
                    name: "URL",
                    value: $request.url.length > 100 ? $request.url.substring(0, 97) + "..." : $request.url,
                    inline: false
                },
                {
                    name: "Data Preview (First 2000 chars)",
                    value: dataPreview.length > 0 ? "```json\n" + dataPreview + "\n```" : "No preview available",
                    inline: false
                }
            ]
        };
        content = "🎮 **Game API Captured Successfully!**";
        
    } else {
        // Error message - same as before
        let errorDetails = "Unknown error";
        if (error) {
            try {
                if (typeof error === 'string') {
                    errorDetails = error.substring(0, 3000);
                } else {
                    errorDetails = JSON.stringify(error).substring(0, 3000);
                }
            } catch (e) {
                errorDetails = "Error details unavailable";
            }
        }

        embed = {
            title: "❌ Game API Capture Failed",
            color: 0xff0000,
            description: `Failed to capture ${apiType}`,
            fields: [
                {
                    name: "User ID",
                    value: userId,
                    inline: true
                },
                {
                    name: "API Type",
                    value: apiType,
                    inline: true
                },
                {
                    name: "Upload ID",
                    value: upload_id,
                    inline: true
                },
                {
                    name: "Timestamp",
                    value: timestamp,
                    inline: true
                },
                {
                    name: "URL",
                    value: $request.url.length > 100 ? $request.url.substring(0, 97) + "..." : $request.url,
                    inline: false
                },
                {
                    name: "Error Details (First 3000 chars)",
                    value: "```\n" + errorDetails + "\n```",
                    inline: false
                }
            ]
        };
        content = "🚨 **Game API Capture Failed!**";
    }

    const payload = {
        content: content,
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

    log(`Sending ${success ? 'success' : 'failure'} message to Discord`);

    $httpClient.post(options, (httpError, resp, responseData) => {
        if (httpError || (resp.status !== 200 && resp.status !== 204)) {
            log(`Discord webhook failed: ${httpError || `HTTP ${resp.status}`}`);
        } else {
            log(`Successfully sent message to Discord`);
        }
        $done({});
    });
}

// Main execution
log("=== GAME API CAPTURE STARTED ===");

try {
    const requestUrl = $request.url;
    const responseBody = $response.body;
    const userId = getUserId(requestUrl);
    const apiType = getApiType(requestUrl);
    
    log(`Processing ${apiType} for user ${userId}`);
    log(`URL: ${requestUrl}`);
    log(`Response body length: ${responseBody ? responseBody.length : 'null/undefined'}`);
    log(`Response body type: ${typeof responseBody}`);

    if (responseBody && responseBody.length > 0) {
        log("Response body found, sending success message");
        sendToDiscord(true, responseBody);
    } else {
        log("No response body found, sending error message");
        sendToDiscord(false, null, "Response body is empty or undefined");
    }

} catch (error) {
    log(`Script execution error: ${error.message}`);
    sendToDiscord(false, null, `Script Error: ${error.message}\nStack: ${error.stack || 'N/A'}`);
}