# MQTT Inspector

Les règles générales sont dans `CodeMastery/CLAUDE.md`. Ce fichier ajoute le projet.

## Le but
Une appli de bureau pour se connecter à un broker MQTT, voir les topics et les messages en direct, et publier.
Le design cible est `design/mockup.png` (thème sombre). De petits changements sont permis.

## Choix techniques
- PySide6 pour la fenêtre (Qt en Python). Nouveau pour moi : chaque notion Qt vient seule.
- paho-mqtt pour le client MQTT.
- pytest pour les tests. uv gère Python 3.13 et les bibliothèques.
- Broker de test : le conteneur Docker `mqtt-test` (Mosquitto, sans mot de passe, localhost:1883).
- `fake_sensors.py` publie de faux capteurs, pour avoir du trafic.

## Le plan
1. MQTT dans le terminal (sans fenêtre). Je vois : les messages défilent dans le terminal.
2. Première fenêtre : champ URL + bouton « Se connecter ». Je vois : la fenêtre s'ouvre, « Connecté ».
3. Tableau des messages en direct (Heure / Topic / Message). Je vois : les messages arrivent dans la fenêtre.
4. Panneau Topics avec compteurs et cases à cocher. Je vois : les compteurs montent, le filtre marche.
5. Détail du message + barre « Publier ». Je vois : je clique un message, je publie, mon message revient.
6. Style de la maquette (thème sombre, sidebar, icônes). Je vois : l'app ressemble à la capture.
7. Rendre pro + README + GitHub.

Bonus s'il reste du temps : pause, vider, recherche, JSON, Historique, Paramètres.

## Où on en est
- 2026-11-13 : plan validé. Étape 1 finie (3 tests verts, mon `on_message` relu).
- 2026-11-13 : étape 2a finie (fenêtre + champ URL + bouton, Entrée connecte aussi, 6 tests verts).
- 2026-11-13 : étape 2b finie (vraie connexion via QTimer + `client.loop(timeout=0)`, « Dernier message », 12 tests verts).
- 2026-11-13 : étape 3 finie (tableau Heure/Topic/Message, plus récent en haut, 16 tests verts).
- 2026-11-14 : étape 4 finie (panneau Topics, compteurs, filtre par cases cochées, 20 tests verts).
- 2026-11-15 : étape 5a finie (panneau Détail du message au clic sur une ligne, 23 tests verts).
- 2026-11-15 : étape 5b finie (barre Publier, Entrée publie aussi, le message revient dans le tableau, 27 tests verts). Étape 5 finie.
- Prochaine étape : 6, style de la maquette (thème sombre, sidebar, icônes).

## Réglages
Aucun changement par rapport à `CodeMastery/CLAUDE.md`.
