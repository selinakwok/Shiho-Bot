// Script to upload game api response body in chunks
// Origin author: NeuraXmy
// Modified for Discord webhook
const scriptName = "upload.js";
const version = "0.2.0";

const upload_id = Math.random().toString(36).substr(2, 9);
const DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1420729437019967590/86GRYENP3UJfvaFRQbyjofNr8i9yqxMDZ0bBhYz14IV3eTSIftNvkVw8NI7gs0kLAdbd";
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

function sendToDiscord(success, message, errorDetails = null) {
    const userId = getUserId($request.url);
    
    let content, color;
    if (success) {
        content = `✅ **API Successfully Intercepted**`;
        color = 0x00ff00;
    } else {
        content = `❌ **API Interception Failed**`;
        color = 0xff0000;
    }

    const payload = {
        content: content,
        embeds: [{
            title: success ? "Game API Captured" : "API Capture Error",
            color: color,
            fields: [
                {
                    name: "User ID",
                    value: userId,
                    inline: true
                },
                {
                    name: "Upload ID", 
                    value: upload_id,
                    inline: true
                },
                {
                    name: "Data Size",
                    value: body ? `${body.length} bytes` : "No data",
                    inline: true
                },
                {
                    name: "URL",
                    value: $request.url.length > 100 ? $request.url.substring(0, 97) + "..." : $request.url,
                    inline: false
                },
                {
                    name: success ? "Status" : "Error Details",
                    value: errorDetails ? errorDetails.substring(0, 3000) : message,
                    inline: false
                }
            ],
            timestamp: new Date().toISOString()
        }]
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
        if (error || (resp.status !== 200 && resp.status !== 204)) {
            log(`Discord webhook failed: ${error || `HTTP ${resp.status}`}`);
        } else {
            log(`Successfully sent message to Discord`);
        }
        $done({});
    });
}

const userId = getUserId($request.url);

log(`开始上传响应内容`);
log(`内容长度: ${body ? body.length : 0}`);
log(`原始网址: ${$request.url}`);
log(`提取到的 User ID: ${userId}`);

try {
    if (body && body.length > 0) {
        log("响应内容存在，发送成功消息");
        sendToDiscord(true, `Successfully captured ${body.length} bytes of API data`);
    } else {
        log("响应内容为空，发送错误消息");
        sendToDiscord(false, "Response body is empty", "响应内容为空，无需上传。");
    }
} catch (error) {
    log(`脚本执行错误: ${error.message}`);
    sendToDiscord(false, "Script execution error", `Script Error: ${error.message}\nStack: ${error.stack || 'N/A'}`);
}