const dmRoomId = window.DM_DATA.roomId;
const currentUserId = window.DM_DATA.currentUserId;
const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";

const dmSocket = new WebSocket(
    protocol + window.location.host + "/ws/dm/" + dmRoomId + "/"
);

const dmChatBox = document.getElementById("dm-chat-box");
const dmInput = document.getElementById("dm-message-input");
const dmSendBtn = document.getElementById("dm-send-btn");

function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text || "";
    return div.innerHTML;
}

dmSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    if (data.type !== "dm_message") return;

    const emptyMessage = document.getElementById("dm-empty-message");
    if (emptyMessage) {
        emptyMessage.remove();
    }

    const isMine = String(data.sender_id) === String(currentUserId);

    const div = document.createElement("div");
    div.className = "dm-message" + (isMine ? " mine" : "");

    div.innerHTML = `
        <div class="dm-message-meta">
            <strong>${escapeHtml(data.sender)}</strong>
            <small>${escapeHtml(data.created_at)}</small>
            <span>읽음 ${data.read_count || 1}</span>
        </div>
        <div class="dm-message-content">
            ${escapeHtml(data.message)}
        </div>
    `;

    dmChatBox.appendChild(div);
    dmChatBox.scrollTop = dmChatBox.scrollHeight;
};

function sendDM() {
    const message = dmInput.value.trim();

    if (!message) return;

    dmSocket.send(JSON.stringify({
        message: message
    }));

    dmInput.value = "";
}

dmSendBtn.onclick = sendDM;

dmInput.addEventListener("keyup", function(e) {
    if (e.key === "Enter") {
        sendDM();
    }
});

window.addEventListener("load", function() {
    dmChatBox.scrollTop = dmChatBox.scrollHeight;
});