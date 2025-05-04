
    console.log("✅ Script AJAX chargé");
    
    // Fonction pour animer les mises à jour avec une animation améliorée
    function animateUpdate(element) {
        if (!element) return;
        
        // Enlever la classe précédente si elle existe
        element.classList.remove('highlight-update');
        
        // Forcer un reflow pour réinitialiser l'animation
        void element.offsetWidth;
        
        // Ajouter la classe pour démarrer l'animation
        element.classList.add('highlight-update');
    }

    // Gestionnaire d'événements pour les champs éditables
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll(".editable").forEach(el => {
            const id = el.dataset.id;
            const field = el.dataset.field;
            let originalValue = el.value; // Stocker la valeur originale
            let isProcessing = false; // Flag pour éviter les doubles confirmations

            const sendUpdate = (fromEvent) => {
                // Si déjà en cours de traitement, ignorer
                if (isProcessing) return;
                
                const newValue = el.value;
                
                // Ne rien faire si la valeur n'a pas changé
                if (newValue === originalValue) {
                    return;
                }
                
                // Marquer comme en cours de traitement
                isProcessing = true;
                
                // Demander confirmation avant d'envoyer la mise à jour
                if (confirm(`Êtes-vous sûr de vouloir modifier ${field} de "${originalValue}" à "${newValue}" ?`)) {
                    console.log(`📝 Envoi AJAX : ${field} = ${newValue} (ID: ${id})`);
                    
                    // Ajouter classe pour indiquer l'état de mise à jour
                    el.classList.add('border-primary');
                    
                    // Ajouter un indicateur visuel pendant le chargement
                    el.style.backgroundImage = 'url(\'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>\')';
                    el.style.backgroundRepeat = 'no-repeat';
                    el.style.backgroundPosition = 'right 5px center';
                    el.style.backgroundSize = '12px';

                    fetch(`/formations/update-champ/${id}/`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": getCookie("csrftoken"),
                        },
                        body: JSON.stringify({ field: field, value: newValue }),
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (!data.success) {
                            showToast("❌ Erreur : " + data.error, "danger");
                            // Revenir à la valeur originale en cas d'erreur
                            el.value = originalValue;
                        } else {
                            console.log("✅ Champ mis à jour !");
                            
                            // Mettre à jour la valeur originale
                            originalValue = newValue;
                            
                            // Mettre à jour la barre de progression avec effet visuel
                            const progressBar = document.getElementById(`progress-${id}`);
                            if (progressBar) {
                                // Définir la nouvelle classe de couleur en fonction du pourcentage
                                progressBar.className = "progress-bar";
                                if (data.taux_saturation >= 100) {
                                    progressBar.classList.add("bg-success");
                                } else if (data.taux_saturation >= 80) {
                                    progressBar.classList.add("bg-primary");
                                } else if (data.taux_saturation >= 50) {
                                    progressBar.classList.add("bg-warning");
                                } else {
                                    progressBar.classList.add("bg-danger");
                                }
                                
                                // Animer la transition de la largeur
                                progressBar.style.width = `${data.taux_saturation}%`;
                            }
                            
                            // Animer les éléments mis à jour
                            const elementsToAnimate = [
                                document.getElementById(`transfo-${id}`),
                                document.getElementById(`saturation-${id}`),
                                document.getElementById(`crif-${id}`),
                                document.getElementById(`mp-${id}`)
                            ];
                            
                            elementsToAnimate.forEach(el => animateUpdate(el));

                            // Mettre à jour les textes
                            document.getElementById(`transfo-${id}`).textContent = `${data.taux_transformation.toFixed(0)}%`;
                            document.getElementById(`saturation-${id}`).textContent = `${data.taux_saturation.toFixed(0)}%`;
                            document.getElementById(`crif-${id}`).textContent = `CRIF: ${data.places_restantes_crif}`;
                            document.getElementById(`mp-${id}`).textContent = `MP: ${data.places_restantes_mp}`;

                            showToast("✅ Modification enregistrée", "success");
                        }
                        
                        // Supprimer l'indicateur de chargement
                        el.style.backgroundImage = 'none';
                        
                        // Supprimer la classe d'indication de mise à jour
                        setTimeout(() => {
                            el.classList.remove('border-primary');
                        }, 1000);
                        
                        // Réinitialiser le flag après traitement
                        setTimeout(() => {
                            isProcessing = false;
                        }, 300);
                    })
                    .catch(err => {
                        console.error("🚨 Erreur AJAX :", err);
                        showToast("❌ Erreur lors de l'enregistrement", "danger");
                        // Revenir à la valeur originale en cas d'erreur
                        el.value = originalValue;
                        el.classList.remove('border-primary');
                        el.style.backgroundImage = 'none';
                        
                        // Réinitialiser le flag après erreur
                        setTimeout(() => {
                            isProcessing = false;
                        }, 300);
                    });
                } else {
                    // Si l'utilisateur annule, revenir à la valeur originale
                    el.value = originalValue;
                    
                    // Réinitialiser le flag après annulation
                    setTimeout(() => {
                        isProcessing = false;
                    }, 300);
                }
            };

            // Utiliser un seul gestionnaire d'événements pour change
            el.addEventListener("change", function(e) {
                sendUpdate('change');
            });
            
            // Ne pas utiliser l'événement blur pour envoyer des mises à jour
            // car il se déclenche juste après change et cause des confirmations multiples
            
            // Permettre de soumettre avec Enter pour les inputs
            if (el.tagName === 'INPUT') {
                el.addEventListener("keypress", function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault(); // Empêcher le comportement par défaut
                        el.blur(); // Retirer le focus
                        sendUpdate('enter'); // Envoyer la mise à jour manuellement
                    }
                });
            }
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showToast(message, type = "info") {
        const container = document.getElementById("toastContainer");
        const toast = document.createElement("div");
        toast.className = `toast align-items-center text-white bg-${type} border-0 show`;
        toast.setAttribute("role", "alert");
        toast.setAttribute("aria-live", "assertive");
        toast.setAttribute("aria-atomic", "true");

        // Ajouter une icône en fonction du type de message
        let icon = '';
        switch(type) {
            case 'success':
                icon = '<i class="fas fa-check-circle me-2"></i>';
                break;
            case 'danger':
                icon = '<i class="fas fa-exclamation-circle me-2"></i>';
                break;
            case 'warning':
                icon = '<i class="fas fa-exclamation-triangle me-2"></i>';
                break;
            default:
                icon = '<i class="fas fa-info-circle me-2"></i>';
                break;
        }

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${icon}${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toast);
        
        // Animation de disparition
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    }

    // Gestion améliorée de l'affichage/masquage des colonnes
    const toggleButton = document.getElementById("toggleColumns");
    if (toggleButton) {
        // Spécifier les indices des colonnes à basculer (en se basant sur l'index 0)
        const toggleableColumns = [5, 6, 7];
        
        // Pour stocker les classes responsives d'origine
        const columnClasses = {};
        
        // Fonction pour obtenir toutes les cellules d'une colonne par indice
        function getCellsByColumnIndex(index) {
            const cells = [];
            const table = document.querySelector("table");
            
            if (!table) return cells;
            
            // Récupérer toutes les lignes (y compris les en-têtes)
            const rows = table.querySelectorAll("tr");
            
            rows.forEach(row => {
                const cell = row.children[index];
                if (cell) cells.push(cell);
            });
            
            return cells;
        }
        
        // Fonction pour enregistrer les classes d'origine
        function saveOriginalClasses() {
            toggleableColumns.forEach(colIndex => {
                const cells = getCellsByColumnIndex(colIndex);
                
                columnClasses[colIndex] = cells.map(cell => {
                    // Extraire uniquement les classes d'affichage (d-*)
                    return Array.from(cell.classList)
                        .filter(className => className.startsWith('d-') && className !== 'd-none');
                });
            });
        }
        
        // Enregistrer les classes d'origine
        saveOriginalClasses();
        
        // Restaurer l'état des colonnes cachées au chargement de la page
        const hiddenColumns = JSON.parse(localStorage.getItem("hiddenColumns")) || [];
        
        if (hiddenColumns.length > 0) {
            hiddenColumns.forEach(colIndex => {
                if (toggleableColumns.includes(Number(colIndex))) {
                    const cells = getCellsByColumnIndex(Number(colIndex));
                    
                    cells.forEach((cell, i) => {
                        cell.classList.add("d-none");
                        
                        // Supprimer les classes responsives pour éviter les conflits
                        if (columnClasses[colIndex] && columnClasses[colIndex][i]) {
                            columnClasses[colIndex][i].forEach(cls => {
                                cell.classList.remove(cls);
                            });
                        }
                    });
                }
            });
        }
        
        // Fonction pour basculer l'affichage des colonnes avec animation
        toggleButton.addEventListener("click", function() {
            // Vérifier si les colonnes sont visibles (prendre la première comme référence)
            const firstColumnCells = getCellsByColumnIndex(toggleableColumns[0]);
            const isVisible = firstColumnCells.length > 0 && 
                              window.getComputedStyle(firstColumnCells[0]).display !== 'none';
            
            // Basculer toutes les colonnes spécifiées avec animation
            toggleableColumns.forEach(colIndex => {
                const cells = getCellsByColumnIndex(colIndex);
                
                cells.forEach((cell, i) => {
                    if (isVisible) {
                        // Animation de sortie avant de cacher
                        cell.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                        cell.style.opacity = '0';
                        cell.style.transform = 'translateX(10px)';
                        
                        setTimeout(() => {
                            // Cacher la colonne
                            cell.classList.add("d-none");
                            
                            // Supprimer les classes responsives
                            if (columnClasses[colIndex] && columnClasses[colIndex][i]) {
                                columnClasses[colIndex][i].forEach(cls => {
                                    cell.classList.remove(cls);
                                });
                            }
                            
                            // Réinitialiser les styles après l'animation
                            cell.style.opacity = '';
                            cell.style.transform = '';
                            cell.style.transition = '';
                        }, 300);
                    } else {
                        // Préparer l'animation d'entrée
                        cell.style.opacity = '0';
                        cell.style.transform = 'translateX(-10px)';
                        cell.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                        
                        // Afficher la colonne et restaurer les classes responsives
                        cell.classList.remove("d-none");
                        
                        // Restaurer les classes responsives
                        if (columnClasses[colIndex] && columnClasses[colIndex][i]) {
                            columnClasses[colIndex][i].forEach(cls => {
                                cell.classList.add(cls);
                            });
                        }
                        
                        // Déclencher l'animation d'entrée
                        setTimeout(() => {
                            cell.style.opacity = '1';
                            cell.style.transform = 'translateX(0)';
                            
                            // Nettoyer les styles après l'animation
                            setTimeout(() => {
                                cell.style.opacity = '';
                                cell.style.transform = '';
                                cell.style.transition = '';
                            }, 300);
                        }, 10);
                    }
                });
            });
            
            // Mettre à jour les colonnes cachées dans localStorage
            let updatedHiddenColumns = JSON.parse(localStorage.getItem("hiddenColumns")) || [];
            
            // Filtrer pour garder uniquement les colonnes non-toggleables qui sont déjà cachées
            updatedHiddenColumns = updatedHiddenColumns.filter(colIndex => 
                !toggleableColumns.includes(Number(colIndex))
            );
            
            // Ajouter les colonnes toggleables si elles doivent être cachées
            if (isVisible) {
                updatedHiddenColumns = [...updatedHiddenColumns, ...toggleableColumns];
            }
            
            localStorage.setItem("hiddenColumns", JSON.stringify(updatedHiddenColumns));
            
            // Afficher un toast pour confirmer avec animation
            showToast(`✅ Colonnes ${isVisible ? 'masquées' : 'affichées'} avec succès`, "info");
            
            // Animer le bouton de basculement
            toggleButton.classList.add('animate__animated', isVisible ? 'animate__rotateOut' : 'animate__rotateIn');
            setTimeout(() => {
                toggleButton.classList.remove('animate__animated', 'animate__rotateOut', 'animate__rotateIn');
            }, 500);
        });
    }
    
    // Ajouter des tooltips Bootstrap aux boutons et éléments importants
    document.addEventListener('DOMContentLoaded', function() {
        // Vérifier si Bootstrap Tooltip est disponible
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl, {
                    delay: { show: 500, hide: 100 }
                });
            });
        }
        
        // Ajouter un effet de survol aux lignes qui affiche un indicateur visuel
        document.querySelectorAll('.formation-row').forEach(row => {
            row.addEventListener('mouseenter', function() {
                // Créer un indicateur de survol
                const indicator = document.createElement('div');
                indicator.className = 'row-hover-indicator';
                indicator.style.position = 'absolute';
                indicator.style.left = '0';
                indicator.style.top = '50%';
                indicator.style.transform = 'translateY(-50%)';
                indicator.style.width = '3px';
                indicator.style.height = '70%';
                indicator.style.backgroundColor = 'var(--primary-color)';
                indicator.style.borderRadius = '0 3px 3px 0';
                indicator.style.opacity = '0';
                indicator.style.transition = 'opacity 0.3s ease';
                
                row.style.position = 'relative';
                row.appendChild(indicator);
                
                // Animer l'apparition
                setTimeout(() => {
                    indicator.style.opacity = '1';
                }, 10);
            });
            
            row.addEventListener('mouseleave', function() {
                const indicator = row.querySelector('.row-hover-indicator');
                if (indicator) {
                    indicator.style.opacity = '0';
                    setTimeout(() => {
                        indicator.remove();
                    }, 300);
                }
            });
        });
    });
