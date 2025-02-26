document.addEventListener("DOMContentLoaded", async () => {
    const loginButton = document.getElementById("login-button");
    const tracksContainer = document.getElementById("tracks");
    const header = document.querySelector("h2");

    loginButton.style.display = "none";

    tracksContainer.innerHTML = "<p>Loading...</p>";

    try {
        const response = await fetch("/api/older-tracks");
        if (response.status === 401) {
            loginButton.style.display = "block";
            header.textContent = "Please log in to view your older top tracks";
            tracksContainer.innerHTML = ""; 
            
            loginButton.addEventListener("click", () => {
                window.location.href = "/auth";
            });
            return;
        }

        const data = await response.json();
        if (data.error) {
            console.error(data.error);
            tracksContainer.innerHTML = "<p>Failed to load tracks. Please try again.</p>";
            return;
        }

        loginButton.style.display = "none";
        header.textContent = "Your Top Tracks From 6 Months Ago";
        tracksContainer.innerHTML = "";

        data.older_tracks.forEach(track => {
            const trackElement = document.createElement("div");
            trackElement.className = "track";

            const image = document.createElement("img");
            image.src = track.image;
            image.alt = track.album;

            const title = document.createElement("h3");
            title.textContent = track.song;

            const artist = document.createElement("p");
            artist.textContent = track.artist;

            trackElement.appendChild(image);
            trackElement.appendChild(title);
            trackElement.appendChild(artist);
            tracksContainer.appendChild(trackElement);
        });
    } catch (error) {
        console.error("An error occurred:", error);
        tracksContainer.innerHTML = "<p>Failed to load tracks. Please try again.</p>";
    }
});