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

function getMicrophonePrecheckError() {
    if (!window.isSecureContext) {
        return "마이크 사용 불가: HTTPS 또는 localhost 접속이 필요합니다.";
    }

    if (!navigator.mediaDevices?.getUserMedia) {
        return "마이크 사용 불가: 브라우저가 getUserMedia를 지원하지 않습니다.";
    }

    if (typeof MediaRecorder === "undefined") {
        return "마이크 사용 불가: 브라우저가 MediaRecorder를 지원하지 않습니다.";
    }

    return null;
}

function setPTTUnavailable(reason) {
    pttBtn.disabled = true;
    pttBtn.classList.remove("btn-danger", "btn-warning");
    pttBtn.classList.add("btn-secondary");
    pttBtn.innerText = "🎙️ 사용 불가";
    pttStatus.innerText = reason;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text || "";
    return div.innerHTML;
}

chatSocket.onopen = function () {
    sendBtn.disabled = false;
};

chatSocket.onerror = function (error) {
    console.error("WebSocket error:", error);
};

chatSocket.onclose = function () {
    sendBtn.disabled = true;
    pttBtn.disabled = true;
    pttStatus.innerText = "서버 연결이 끊겼습니다. 페이지를 새로고침해 주세요.";
};

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

    if (chatSocket.readyState !== WebSocket.OPEN) {
        alert("채팅 서버 연결 중입니다. 잠시 후 다시 시도해 주세요.");
        return;
    }

    try {
        chatSocket.send(
            JSON.stringify({
                message: message,
                receiver_id: receiverId,
            }),
        );
    } catch (error) {
        console.error("메시지 전송 실패:", error);
        alert("메시지 전송에 실패했습니다. 페이지를 새로고침해 주세요.");
        return;
    }

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

    if (!window.isSecureContext) {
        throw new Error("INSECURE_CONTEXT");
    }

    if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("GET_USER_MEDIA_UNSUPPORTED");
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
        let message = "마이크를 사용할 수 없습니다.";

        if (error?.message === "INSECURE_CONTEXT") {
            message =
                "마이크는 HTTPS 또는 localhost 접속에서만 사용할 수 있습니다.";
        } else if (error?.message === "GET_USER_MEDIA_UNSUPPORTED") {
            message = "현재 브라우저/환경에서 마이크 기능을 지원하지 않습니다.";
        } else if (error?.name === "NotAllowedError") {
            message =
                "마이크 권한이 거부되었습니다. 주소창의 사이트 권한에서 마이크를 허용해 주세요.";
        } else if (error?.name === "NotFoundError") {
            message = "사용 가능한 마이크 장치를 찾지 못했습니다.";
        } else if (error?.name === "NotReadableError") {
            message =
                "마이크를 다른 앱이 사용 중입니다. 다른 앱을 종료하고 다시 시도해 주세요.";
        }

        alert(message);
        pttStatus.innerText = "마이크 사용 불가";
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

    if (chatSocket.readyState !== WebSocket.OPEN) {
        sendBtn.disabled = true;
    }

    const precheckError = getMicrophonePrecheckError();
    if (precheckError) {
        setPTTUnavailable(precheckError);
        console.warn(precheckError, {
            protocol: window.location.protocol,
            host: window.location.host,
            isSecureContext: window.isSecureContext,
        });
    }
});
