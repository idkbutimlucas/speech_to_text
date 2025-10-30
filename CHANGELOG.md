# Changelog

## Version 2.0 - Mode Automatique (2025-01-30)

### 🎯 Modifications majeures

#### ✅ Démarrage automatique
- L'application démarre automatiquement la reconnaissance vocale dès le chargement
- Plus besoin d'appuyer sur un bouton "Démarrer"
- Redémarrage automatique en cas d'erreur ou de déconnexion
- Interface simplifiée sans boutons de contrôle visibles

#### ✅ Auto-effacement de l'historique
- Effacement automatique après 30 secondes d'inactivité (par défaut)
- Configurable : désactivé, 30s, 1min ou 2min
- Le timer se réinitialise à chaque nouvelle parole détectée
- Idéal pour une utilisation continue sans accumulation de texte

#### ✅ Accessibilité améliorée
- Taille de police par défaut augmentée à **60px** (au lieu de 40px)
- Historique en **48px** (au lieu de 32px)
- Plage de réglage étendue : 30-100px (au lieu de 20-80px)
- Meilleure lisibilité pour personnes âgées

#### ✅ Interface épurée
- Suppression des boutons Démarrer/Arrêter/Effacer de l'interface principale
- Bouton "Effacer maintenant" déplacé dans les paramètres
- Interface minimaliste centrée sur l'affichage du texte
- Moins de distractions visuelles

### 🔧 Modifications techniques

#### JavaScript (app.js)
- Ajout de la fonction `resetAutoClearTimer()` pour gérer l'auto-effacement
- Démarrage automatique 1 seconde après la connexion WebSocket
- Redémarrage automatique après arrêt ou erreur
- Détection de visibilité de la page pour relancer la reconnaissance
- Sauvegarde des préférences dans localStorage

#### HTML (index.html)
- Suppression de la section `.controls` avec les boutons
- Ajout du sélecteur `autoClearDelay` dans les paramètres
- Ajout du bouton `manualClearBtn` dans les paramètres
- Valeurs par défaut ajustées (fontSize: 60px)

#### CSS (style.css)
- Police par défaut du texte courant : 60px (↑ de 40px)
- Police par défaut de l'historique : 48px (↑ de 32px)
- Ajout du style pour le select d'auto-effacement
- Ajout du style pour le bouton d'effacement manuel
- Amélioration du responsive

#### Configuration (config.json)
- Nouveau paramètre `auto_start: true`
- `default_font_size: 60` (↑ de 40)
- Nouveau paramètre `auto_clear_delay: 30`

### 📚 Documentation

#### GUIDE_MAMIE.md
- Complètement réécrit pour refléter le fonctionnement automatique
- Simplification maximale du guide
- Accent mis sur "rien à faire"
- Instructions claires pour les réglages optionnels

#### README.md
- Mise à jour pour mentionner le démarrage automatique
- Documentation des nouvelles fonctionnalités

---

## Version 1.0 - Version initiale (2025-01-30)

### Fonctionnalités initiales
- Reconnaissance vocale locale avec Vosk
- Interface web avec Flask et Socket.IO
- Boutons de contrôle manuel (Démarrer/Arrêter/Effacer)
- Paramètres ajustables (taille, thème, auto-scroll)
- Mode sombre/clair
- Horodatage des messages
- Historique des transcriptions
- Installation simplifiée avec scripts
- Service systemd pour démarrage au boot
- Documentation complète
