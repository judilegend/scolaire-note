document.addEventListener("DOMContentLoaded", function () {
  // Sidebar toggle functionality
  const sidebarToggle = document.querySelector(".sidebar-toggle");
  const sidebar = document.querySelector(".sidebar");
  const mainContent = document.querySelector(".main-content");

  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("sidebar-visible");
    });
  }

  // Dropdown menu functionality
  const dropdownToggles = document.querySelectorAll(".dropdown-toggle");

  dropdownToggles.forEach((toggle) => {
    toggle.addEventListener("click", function (e) {
      e.preventDefault();

      // Close other dropdowns
      dropdownToggles.forEach((otherToggle) => {
        if (otherToggle !== toggle) {
          otherToggle.classList.remove("active");
          const otherMenu = otherToggle.nextElementSibling;
          if (otherMenu) otherMenu.classList.remove("show");
        }
      });

      // Toggle current dropdown
      toggle.classList.toggle("active");
      const dropdownMenu = toggle.nextElementSibling;
      if (dropdownMenu) dropdownMenu.classList.toggle("show");
    });
  });

  // Auto-hide flash messages after 5 seconds
  const flashMessages = document.querySelectorAll(".alert");
  if (flashMessages.length > 0) {
    setTimeout(() => {
      flashMessages.forEach((message) => {
        message.style.opacity = "0";
        message.style.transform = "translateX(100%)";
        setTimeout(() => {
          message.remove();
        }, 300);
      });
    }, 5000);
  }

  // Handle active menu items
  const currentPath = window.location.pathname;
  const menuLinks = document.querySelectorAll(".sidebar-menu a");

  menuLinks.forEach((link) => {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");

      // If it's in a dropdown, open the dropdown
      const parentDropdown = link.closest(".sidebar-dropdown");
      if (parentDropdown) {
        const dropdownToggle = parentDropdown.querySelector(".dropdown-toggle");
        const dropdownMenu = parentDropdown.querySelector(".dropdown-menu");

        if (dropdownToggle && dropdownMenu) {
          dropdownToggle.classList.add("active");
          dropdownMenu.classList.add("show");
        }
      }
    }
  });

  // Form validation for notes
  const notesForm = document.querySelector(".notes-form");
  if (notesForm) {
    notesForm.addEventListener("submit", function (e) {
      const noteInputs = document.querySelectorAll('input[type="number"]');
      let isValid = true;

      noteInputs.forEach((input) => {
        const value = parseFloat(input.value);
        if (input.value && (isNaN(value) || value < 0 || value > 20)) {
          isValid = false;
          input.classList.add("error");
        } else {
          input.classList.remove("error");
        }
      });

      if (!isValid) {
        e.preventDefault();
        alert("Veuillez entrer des notes valides (entre 0 et 20).");
      }
    });
  }

  // Confirmation for delete actions
  const deleteButtons = document.querySelectorAll(".btn-delete");
  deleteButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      if (
        !confirm(
          "Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible."
        )
      ) {
        e.preventDefault();
      }
    });
  });
});
document.addEventListener("DOMContentLoaded", function () {
  const reclamationsLink = document.getElementById("reclamations-link");
  if (reclamationsLink) {
    reclamationsLink.addEventListener("click", function (e) {
      e.preventDefault();
      window.location.href = "/enseignant/reclamations";
    });
  }
});
