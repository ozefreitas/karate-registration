const toggleAthleteDetails = (athleteID) => {
  const athleteDiv = document.getElementById(`athlete-details-${athleteID}`);
  if (athleteDiv.style.display === "none" || athleteDiv.style.display === "") {
    athleteDiv.style.display = "flex";
  } else {
    athleteDiv.style.display = "none";
  }
};

const toggleRegistrationOptions = (athleteID) => {
  const buttonsDiv = document.getElementById(`buttons-container-${athleteID}`);
  const athleteDiv = document.getElementById(`athlete-details-${athleteID}`);
  if (athleteDiv.style.display !== "flex") {
    if (
      buttonsDiv.style.display === "none" ||
      buttonsDiv.style.display === ""
    ) {
      buttonsDiv.style.display = "flex";
    } else {
      buttonsDiv.style.display = "none";
    }
  }
};

const toggleArchivedAthletes = (compID) => {
  const athleteDiv = document.getElementById(`archived-athletes-container-${compID}`);
  if (athleteDiv.style.display === "none" || athleteDiv.style.display === "") {
    athleteDiv.style.display = "flex";
  } else {
    athleteDiv.style.display = "none";
  }
};

function hideMessagesAfterTimeout(messageType) {
  let timeout
  if (messageType === "success") {
    timeout = 5000
  } else timeout = 10000
  setTimeout(function () {
    const messageContainer = document.getElementById("messages");
    if (messageContainer) {
      messageContainer.style.display = "none";
    }
  }, timeout);
}
