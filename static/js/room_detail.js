const roomId = window.ROOM_DATA?.roomId;
const currentUserId = window.ROOM_DATA?.currentUserId;
const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";

const chatSocket = new WebSocket(
    protocol + window.location.host + "/ws/rooms/" + roomId + "/",
);

const chatBox = document.getElementById("chat-box");
const input = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const receiverSelect = document.getElementById("receiver");
const onlineUsers = document.getElementById("online-users");

const pttBtn = document.getElementById("ptt-btn");
const pttStatus = document.getElementById("ptt-status");

let mediaRecorder = null;
let audioChunks = [];
let audioStream = null;
let isRecording = false;

function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text || "";
    return div.innerHTML;
}

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);

    if (data.type === "users") {
        onlineUsers.innerHTML = "";
        receiverSelect.innerHTML = `<option value="">전체에게</option>`;

        data.users.forEach((user) => {
            onlineUsers.innerHTML += `
                    <div class="list-group-item online-user">
                        🟢 ${escapeHtml(user.nickname)}
                        <div class="small text-muted">${escapeHtml(user.name)}</div>
                    </div>
                `;

            if (String(user.id) !== String(currentUserId)) {
                receiverSelect.innerHTML += `
                        <option value="${user.id}">${escapeHtml(user.nickname)}에게</option>
                    `;
            }
        });

        return;
    }

    if (data.type === "audio") {
        const audio = new Audio(data.audio);
        audio.play();

        const div = document.createElement("div");
        div.className = "message";

        div.innerHTML = `
                <strong>${escapeHtml(data.sender)}</strong>
                <span class="badge bg-danger ms-2">음성 메시지</span>
                <div class="small text-muted">음성이 재생되었습니다.</div>
            `;

        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;

        return;
    }

    const emptyMessage = document.getElementById("empty-message");
    if (emptyMessage) {
        emptyMessage.remove();
    }

    const isPrivate = data.message_type === "private";

    const div = document.createElement("div");
    div.className = "message" + (isPrivate ? " private" : "");

    div.innerHTML = `
            <div class="message-meta">
                <strong>${escapeHtml(data.sender)}</strong>
                ${isPrivate ? '<span class="badge bg-warning text-dark ms-2">개인 메시지</span>' : ""}
                <small>${escapeHtml(data.created_at || "")}</small>
                <span class="read-badge">읽음 ${data.read_count || 1}</span>
            </div>
            <div class="message-content">${escapeHtml(data.message)}</div>
        `;

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
};

function sendMessage() {
    const message = input.value.trim();
    const receiverId = receiverSelect.value;

    if (!message) return;

    chatSocket.send(
        JSON.stringify({
            message: message,
            receiver_id: receiverId,
        }),
    );

    input.value = "";
}

sendBtn.onclick = sendMessage;

input.addEventListener("keyup", function (e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});

async function initMicrophone() {
    if (audioStream) {
        return audioStream;
    }

    audioStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
    });

    return audioStream;
}

async function startPTT() {
    if (isRecording) return;

    try {
        const stream = await initMicrophone();

        audioChunks = [];

        mediaRecorder = new MediaRecorder(stream, {
            mimeType: "audio/webm",
        });

        mediaRecorder.ondataavailable = function (event) {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = function () {
            const audioBlob = new Blob(audioChunks, {
                type: "audio/webm",
            });

            const reader = new FileReader();

            reader.onloadend = function () {
                chatSocket.send(
                    JSON.stringify({
                        type: "audio",
                        audio: reader.result,
                        receiver_id: receiverSelect.value,
                    }),
                );
            };

            reader.readAsDataURL(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;

        pttBtn.classList.remove("btn-danger");
        pttBtn.classList.add("btn-warning");
        pttBtn.innerText = "🔴 송신 중...";
        pttStatus.innerText = "말하는 중입니다.";
    } catch (error) {
        alert("마이크 권한이 필요합니다.");
        console.error(error);
    }
}

function stopPTT() {
    if (!isRecording || !mediaRecorder) return;

    mediaRecorder.stop();
    isRecording = false;

    pttBtn.classList.remove("btn-warning");
    pttBtn.classList.add("btn-danger");
    pttBtn.innerText = "🎙️ 누르고 말하기";
    pttStatus.innerText = "대기 중";
}

pttBtn.addEventListener("mousedown", startPTT);
pttBtn.addEventListener("mouseup", stopPTT);
pttBtn.addEventListener("mouseleave", stopPTT);

pttBtn.addEventListener("touchstart", function (e) {
    e.preventDefault();
    startPTT();
});

pttBtn.addEventListener("touchend", function (e) {
    e.preventDefault();
    stopPTT();
});

window.addEventListener("load", function () {
    chatBox.scrollTop = chatBox.scrollHeight;
});
