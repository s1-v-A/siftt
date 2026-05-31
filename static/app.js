document.addEventListener("DOMContentLoaded", () => {
    // 1. Grab references to our HTML interactive components
    const createRoomBtn = document.getElementById("create-room-btn");
    const homeView = document.getElementById("home-view");
    const roomView = document.getElementById("room-view");
    const roomCodeDisplay = document.getElementById("room-code-display");

    // 2. Attach a click listener to the "Create Sharing Room" Button
    createRoomBtn.addEventListener("click", async () => {
        try {
            // 3. Fire a background request to our FastAPI endpoint
            const response = await fetch("/api/rooms/create", { method: "POST" });
            
            if (response.ok) {
                const data = await response.json();
                const freshCode = data.room_code; // Extracted from our Python RAM dict!

                // 4. Update the browser URL address bar without reloading the page
                window.history.pushState({}, "", `/room/${freshCode}`);

                // 5. Swap the layout styling to transition screens seamlessly
                roomCodeDisplay.textContent = freshCode;
                homeView.classList.add("hidden");
                roomView.classList.remove("hidden");
            } else {
                alert("Backend failed to initialize an active transfer node.");
            }
        } catch (error) {
            console.error("Networking breakdown:", error);
            alert("Could not establish a stable connection with AeroDrop server.");
        }
    });
});