// Ultra-simple test script
const DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1420729437019967590/86GRYENP3UJfvaFRQbyjofNr8i9yqxMDZ0bBhYz14IV3eTSIftNvkVw8NI7gs0kLAdbd";

// Send immediate test message
const payload = {
    content: "🧪 **SCRIPT IS WORKING!** Script executed at " + new Date().toISOString(),
    embeds: [{
        title: "Script Execution Test",
        description: "If you see this, the script is running!",
        color: 0x00ff00,
        fields: [
            {
                name: "URL",
                value: ($request && $request.url) ? $request.url : "No URL available",
                inline: false
            },
            {
                name: "Test Status",
                value: "✅ Script executed successfully",
                inline: false
            }
        ]
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
    console.log("Test message sent. Error:", error, "Status:", resp ? resp.status : "no response");
    $done({});
});