document.addEventListener("DOMContentLoaded", async () => {
    const createRoomBtn = document.getElementById("create-room-btn");
    const homeView = document.getElementById("home-view");
    const roomView = document.getElementById("room-view");
    const roomCodeDisplay = document.getElementById("room-code-display");
    const fileSelector = document.getElementById("file-selector");
    const uploadBtn = document.getElementById("upload-btn");
    const fileList = document.getElementById("file-list");
    const joinRoomInput = document.getElementById("join-room-input");
    const joinRoomBtn = document.getElementById("join-room-btn");

    // TRACK STATE GLOBAL ENGINE VARIABLES
    let activeRoomCode = null;
    let isSender = false; // Tracks if the current browser window is the creator

    // DYNAMIC FILE RENDER CELL
    function appendFileToUiList(filename) {
        const li = document.createElement("li");
        li.style.margin = "8px 0";

        if (isSender) {
            // SENDER ROLE: Just display the file name as clean, unclickable text
            li.textContent = `${filename} (Uploaded)`;
            li.style.color = "#4b5563";
        } else {
            // RECEIVER ROLE: Render a styled download hyperlink anchor
            const downloadLink = document.createElement("a");
            downloadLink.href = `/api/rooms/${activeRoomCode}/files/${filename}`;
            downloadLink.textContent = filename;
            downloadLink.style.color = "#0070f3";
            downloadLink.style.textDecoration = "underline";
            downloadLink.setAttribute("download", filename); 
            li.appendChild(downloadLink);
        }

        fileList.appendChild(li);
    }

    // INITIALIZATION ROUTER
    async function initializeApplicationRoute() {
        const urlPath = window.location.pathname;
        const pathSegments = urlPath.split("/");

        if (pathSegments[1] === "room" && pathSegments[2]) {
            const codeFromUrl = pathSegments[2].toUpperCase();

            try {
                const response = await fetch(`/api/rooms/${codeFromUrl}`);

                if (response.ok) {
                    const data = await response.json();
                    activeRoomCode = data.room_code;

                    roomCodeDisplay.textContent = activeRoomCode;
                    homeView.classList.add("hidden");
                    roomView.classList.remove("hidden");

                    fileList.innerHTML = "";
                    data.files.forEach(filename => appendFileToUiList(filename));
                } else {
                    alert("This sharing room link has expired or never existed.");
                    window.history.pushState({}, "", "/");
                }
            } catch (error) {
                console.error("Routing failure:", error);
            }
        }
    }

    await initializeApplicationRoute();

    // INTERACTIVE ACTIONS: CREATE ROOM
    createRoomBtn.addEventListener("click", async () => {
        try {
            const response = await fetch("/api/rooms/create", { method: "POST" });
            if (response.ok) {
                const data = await response.json();
                
                activeRoomCode = data.room_code;
                isSender = true; // Flips role flag to hide download elements

                window.history.pushState({}, "", `/room/${activeRoomCode}`);

                roomCodeDisplay.textContent = activeRoomCode;
                homeView.classList.add("hidden");
                roomView.classList.remove("hidden");
                fileList.innerHTML = ""; 
            }
        } catch (error) {
            alert("Could not initialize room.");
        }
    });

    // INTERACTIVE ACTIONS: JOIN ROOM
    joinRoomBtn.addEventListener("click", async () => {
        const inputCode = joinRoomInput.value.trim().toUpperCase();

        if (inputCode.length !== 5) {
            alert("Please enter a valid 5-character room code.");
            return;
        }

        activeRoomCode = inputCode;
        isSender = false; // Receiver explicitly joins -> needs download hyperlinks

        window.history.pushState({}, "", `/room/${activeRoomCode}`);
        fileList.innerHTML = "";

        await initializeApplicationRoute();
        joinRoomInput.value = "";
    });

    // INTERACTIVE ACTIONS: UPLOAD FILE
    uploadBtn.addEventListener("click", async () => {
        if (fileSelector.files.length === 0) {
            alert("Please select a file first.");
            return;
        }

        const targetedFile = fileSelector.files[0];
        const payload = new FormData();
        payload.append("file", targetedFile);

        try {
            uploadBtn.textContent = "Uploading...";
            uploadBtn.disabled = true;

            const response = await fetch(`/api/rooms/${activeRoomCode}/upload`, {
                method: "POST",
                body: payload
            });

            if (response.ok) {
                const data = await response.json();
                appendFileToUiList(data.filename);
                fileSelector.value = "";
            } else {
                alert("Upload failed.");
            }
        } catch (error) {
            console.error("Upload error:", error);
        } finally {
            uploadBtn.textContent = "Upload";
            uploadBtn.disabled = false;
        }
    });
});