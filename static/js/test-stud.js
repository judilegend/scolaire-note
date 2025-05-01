// Fonction pour ajouter la classe "active" au lien de navigation actif
document.addEventListener("DOMContentLoaded", function () {
  // Récupérer le chemin actuel
  const currentPath = window.location.pathname;

  // Sélectionner tous les liens de navigation
  const navLinks = document.querySelectorAll(".nav-link");

  // Parcourir les liens et ajouter la classe "active" au lien correspondant
  navLinks.forEach((link) => {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");
    }
  });

  // Gestion de la barre latérale sur mobile
  const menuToggle = document.getElementById("menu-toggle");
  const container = document.querySelector(".container");

  if (menuToggle) {
    menuToggle.addEventListener("click", function () {
      container.classList.toggle("sidebar-collapsed");
    });
  }

  // Fermer la barre latérale lorsqu'on clique sur un lien (sur mobile)
  const sidebarLinks = document.querySelectorAll(".sidebar-nav .nav-link");

  function closeSidebarOnMobile() {
    if (window.innerWidth <= 768) {
      container.classList.remove("sidebar-collapsed");
    }
  }

  sidebarLinks.forEach((link) => {
    link.addEventListener("click", closeSidebarOnMobile);
  });

  // Gestion des cartes avec glassmorphism
  const cards = document.querySelectorAll(".card");
  cards.forEach((card) => {
    card.classList.add("glass-effect");
  });
});

// Fonction pour gérer l'effet parallaxe sur les éléments glassmorphism
document.addEventListener("mousemove", function (e) {
  const cards = document.querySelectorAll(".glass-effect");
  const mouseX = e.clientX;
  const mouseY = e.clientY;

  cards.forEach((card) => {
    const rect = card.getBoundingClientRect();
    const cardCenterX = rect.left + rect.width / 2;
    const cardCenterY = rect.top + rect.height / 2;

    const offsetX = (mouseX - cardCenterX) / 50;
    const offsetY = (mouseY - cardCenterY) / 50;

    card.style.transform = `perspective(1000px) rotateX(${
      -offsetY * 0.2
    }deg) rotateY(${offsetX * 0.2}deg)`;
  });
});
