const toggleAthleteDetails = (athleteID) => {
    const athleteDiv = document.getElementById(`athlete-details-${athleteID}`)
    if (athleteDiv.style.display === "none" || athleteDiv.style.display === "") {
        athleteDiv.style.display = "block";
    } else {
        athleteDiv.style.display = "none";
    }
}