const toggleOptionsContainer = () => {
  const optionsContainer = document.getElementById(`options-nav-menu`);
  if (
    optionsContainer.style.display === "none" ||
    optionsContainer.style.display === ""
  ) {
    optionsContainer.style.display = "block";
  } else {
    optionsContainer.style.display = "none";
  }
};

const toggleTopHeaderContainer = () => {
  const athleteDiv = document.getElementById(`top-header-container`);
  athleteDiv.style.display = "none";
};

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
  const athleteDiv = document.getElementById(
    `archived-athletes-container-${compID}`
  );
  if (athleteDiv.style.display === "none" || athleteDiv.style.display === "") {
    athleteDiv.style.display = "flex";
  } else {
    athleteDiv.style.display = "none";
  }
};

function hideMessagesAfterTimeout(messageType) {
  let timeout;
  if (messageType === "success") {
    timeout = 5000;
  } else timeout = 10000;
  setTimeout(function () {
    const messageContainer = document.getElementById("messages");
    if (messageContainer) {
      messageContainer.style.display = "none";
    }
  }, timeout);
}

// modal windows

document.addEventListener("DOMContentLoaded", function () {
  const deleteAccountTrigger = document.getElementById("delete-account-span");
  const deleteModal = document.getElementById("deleteModal");
  const deleteModalIndividual = document.getElementById("deleteModalIndividual");
  const cancelDelete = document.getElementById("cancel-delete");
  const confirmDelete = document.getElementById("confirm-delete");

  if (deleteAccountTrigger) {
    deleteAccountTrigger.addEventListener("click", function () {
      deleteModal.style.display = "block";
    });
  }

  if (deleteAccountTrigger) {
    deleteAccountTrigger.addEventListener("click", function () {
      deleteModalIndividual.style.display = "block";
    });
  }

  if (cancelDelete) {
    cancelDelete.addEventListener("click", function () {
      deleteModal.style.display = "none";
    });
  }

  if (confirmDelete) {
    cancelDelete.addEventListener("click", function () {
      deleteModal.style.display = "none";
    });
  }
});

document.addEventListener("DOMContentLoaded", function () {
  let checkbox = document.querySelector("#id_is_just_student");
  let extraFields = document.querySelector("#athlete_fields");

  function toggleFields() {
      if (checkbox.checked) {
          extraFields.style.display = "none";
      } else {
          extraFields.style.display = "block";
      }
  }

  // Initial check on page load
  toggleFields();

  // Listen for checkbox changes
  checkbox.addEventListener("change", toggleFields);
});
