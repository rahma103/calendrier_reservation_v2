document.addEventListener("DOMContentLoaded", () => {
  const calendars = document.querySelectorAll(".calendar");
  const btnReserve = document.getElementById("btnReserveSelected");
  const form = document.getElementById("reservationForm");
  const btnCancel = document.getElementById("btnCancel");

  // Structure pour garder les dates sélectionnées
  // Chaque élément est un objet : { date: Date, dateId: string, maison, niveau, mois, jour }
  let selectedDates = [];

  // Chargement des réservations pour griser les jours déjà réservés
  let reservationsData = null;

  fetch("/static/reservations.json")
    .then(res => {
      if (res.ok) return res.json();
      else return {};
    })
    .then(data => {
      reservationsData = data || {};
      initCalendars();
    })
    .catch(() => {
      reservationsData = {};
      initCalendars();
    });

  // Initialise chaque calendrier
  function initCalendars() {
    calendars.forEach(cal => {
      const maison = cal.dataset.maison;
      const niveau = cal.dataset.niveau;
      const mois = parseInt(cal.dataset.mois, 10);

      renderCalendar(cal, maison, niveau, mois);
    });

    updateReserveButton();
  }

  // Crée et affiche un calendrier pour un mois donné, maison et étage
  function renderCalendar(container, maison, niveau, mois) {
    container.innerHTML = "";

    // Pour 2025 (année fixe)
    const year = 2025;
    const firstDay = new Date(year, mois - 1, 1);
    const lastDay = new Date(year, mois, 0); // dernier jour du mois

    // Jour de la semaine du 1er jour (0 = dimanche)
    let startDay = firstDay.getDay();
    if (startDay === 0) startDay = 7; // Pour que lundi = 1

    // Affichage des jours avant le 1er (cases vides)
    for (let i = 1; i < startDay; i++) {
      const emptyCell = document.createElement("div");
      emptyCell.classList.add("day", "disabled");
      container.appendChild(emptyCell);
    }

    // Affichage des jours du mois
    for (let day = 1; day <= lastDay.getDate(); day++) {
      const dayDiv = document.createElement("div");
      dayDiv.classList.add("day");
      dayDiv.textContent = day;

      const dateId = `${maison}-${niveau}-${mois}-${day}`;

      // Si déjà réservé, griser et bloquer
      if (reservationsData && reservationsData[dateId]) {
        dayDiv.classList.add("booked");
        dayDiv.title = `Réservé par ${reservationsData[dateId].prenom} ${reservationsData[dateId].nom}`;
        dayDiv.style.cursor = "default";
      } else {
        // Sinon clic possible
        dayDiv.addEventListener("click", () => toggleSelectDay(dayDiv, dateId, maison, niveau, mois, day));
      }

      container.appendChild(dayDiv);
    }
  }

  // Gestion de la sélection/désélection d'un jour
  function toggleSelectDay(dayDiv, dateId, maison, niveau, mois, jour) {
    if (dayDiv.classList.contains("selected")) {
      // Désélectionner
      dayDiv.classList.remove("selected");
      selectedDates = selectedDates.filter(d => d.dateId !== dateId);
    } else {
      // Sélectionner
      dayDiv.classList.add("selected");
      selectedDates.push({ dateId, maison, niveau, mois, jour });
    }
    updateReserveButton();
  }

  // Met à jour l'état du bouton de réservation
  function updateReserveButton() {
    if (selectedDates.length > 0) {
      btnReserve.disabled = false;
    } else {
      btnReserve.disabled = true;
    }
  }

  // Clique sur le bouton "Réserver"
  btnReserve.addEventListener("click", () => {
    if (selectedDates.length === 0) return;

    // Afficher le formulaire
    form.style.display = "block";
    btnReserve.style.display = "none";

    // Pré-remplir les dates dans un champ caché ou juste stocker pour envoi
    // Ici on garde selectedDates dans variable JS (visible dans closure)
  });

  // Annuler réservation (bouton annuler dans formulaire)
  btnCancel.addEventListener("click", () => {
    form.style.display = "none";
    btnReserve.style.display = "inline-block";
  });

  // Soumission du formulaire
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    if (selectedDates.length === 0) {
      alert("Aucune date sélectionnée.");
      return;
    }

    // Trier les dates par ordre croissant pour prendre la première et la dernière
    selectedDates.sort((a, b) => {
      if (a.mois !== b.mois) return a.mois - b.mois;
      return a.jour - b.jour;
    });

    const first = selectedDates[0];
    const last = selectedDates[selectedDates.length - 1];

    // Construire les dates ISO format YYYY-MM-DD
    const startDate = `2025-${String(first.mois).padStart(2, "0")}-${String(first.jour).padStart(2, "0")}`;
    const endDate = `2025-${String(last.mois).padStart(2, "0")}-${String(last.jour).padStart(2, "0")}`;

    const nomPrenom = document.getElementById("nomPrenom").value.trim();
    const telephone = document.getElementById("telephone").value.trim();

    if (!nomPrenom || !telephone) {
      alert("Veuillez remplir tous les champs.");
      return;
    }

    // Préparation du payload
    const payload = {
      startDate,
      endDate,
      maison: first.maison,
      niveau: first.niveau,
      nomPrenom,
      telephone
    };

    // Envoi au serveur
    fetch("/reserver", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          alert("Réservation réussie !");
          // Reset interface
          resetSelection();
          form.style.display = "none";
          btnReserve.style.display = "inline-block";
          form.reset();

          // Recharger la page pour mettre à jour les calendriers (dates réservées)
          location.reload();
        } else {
          alert("Erreur : " + data.message);
        }
      })
      .catch(() => alert("Erreur lors de la communication avec le serveur."));
  });

  // Réinitialiser la sélection
  function resetSelection() {
    selectedDates = [];
    calendars.forEach(cal => {
      cal.querySelectorAll(".day.selected").forEach(d => d.classList.remove("selected"));
    });
    updateReserveButton();
  }
});
