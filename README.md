# Gyro Controller pour Mowgli

## Introduction
Ce dépôt GitHub héberge le projet Gyro Controller, destiné à la création d'un gyrophare à LED contrôlable et personnalisable pour la tondeuse robot OpenMower utilisant le fork Mowgli.

## Caractéristiques Principales
- Gyrophare à LED personnalisable avec plusieurs effets lumineux
- Contrôle dynamique des LED en fonction de l'état de la tondeuse
- Facilement intégrable avec le système OpenMower et Raspberry Pi 4
- Nombre de LED WS2812 utilisables personnalisable (14 dans mon projet pour l'instant)

## Installation
Suivez ces étapes pour installer ce dépôt sur votre Raspberry Pi 3 ou 4 via SSH.

### Prérequis
- Un Raspberry Pi 3 ou 4 avec Raspbian installé et connecté au réseau.
- Un ordinateur avec un client SSH (comme Terminal sur macOS ou PuTTY sur Windows).
- Un robot tondeuse avec mowgli et openmower.

### Étape 1 : Connexion au Raspberry Pi
1. Trouvez l'adresse IP de votre Raspberry Pi.
2. Connectez-vous en SSH avec la commande :
   ```bash
   ssh <username>@<raspberry_pi_ip>
   ```
3. Entrez le mot de passe.

### Étape 2 : Cloner le dépôt
Clonez le dépôt sur votre Raspberry Pi :
```bash
git clone https://github.com/juditech3D/Gyro_Controller_for_Mowgli.git
```

### Étape 3 : Déplacer dans le répertoire
Déplacez-vous dans le répertoire cloné :
```bash
cd Gyro_Controller_for_Mowgli
```

### Étape 4 : Créer et activer un environnement virtuel
Pour installer les dépendances dans un environnement virtuel, suivez les étapes suivantes :

1. Créez un environnement virtuel dans le répertoire du projet :
   ```bash
   python3 -m venv venv
   ```

2. Activez l'environnement virtuel :
   ```bash
   source venv/bin/activate
   ```

3. Installez les dépendances depuis le fichier `requirements.txt` :
   ```bash
   pip install -r requirements.txt
   ```

### Étape 5 : Configuration pour le lancement automatique au démarrage
Pour lancer le gyrophare automatiquement au démarrage du Raspberry Pi, créez un fichier de service `systemd` :

1. Créez un fichier de service avec la commande suivante :
   ```bash
   sudo nano /etc/systemd/system/gyro_controller.service
   ```

2. Ajoutez-y le contenu suivant (remplacez `<user>` par votre nom d'utilisateur, par exemple `juditech3d`) :
   ```ini
   [Unit]
   Description=Gyro Controller pour Mowgli
   After=network.target

   [Service]
   ExecStart=/home/<user>/Gyro_Controller_for_Mowgli/venv/bin/python /home/<user>/Gyro_Controller_for_Mowgli/main.py
   WorkingDirectory=/home/<user>/Gyro_Controller_for_Mowgli
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=<user>

   [Install]
   WantedBy=multi-user.target
   ```

3. Enregistrez et fermez le fichier en appuyant sur `CTRL+X`, puis `Y` et `Entrée`.

4. Activez le service pour qu'il se lance automatiquement au démarrage :
   ```bash
   sudo systemctl enable gyro_controller.service
   ```

5. (Optionnel) Démarrez le service immédiatement sans redémarrer avec :
   ```bash
   sudo systemctl start gyro_controller.service
   ```

6. Vérifiez le statut du service avec :
   ```bash
   sudo systemctl status gyro_controller.service
   ```

### Étape 6 : Lancer le gyrophare
Si vous n'avez pas configuré le démarrage automatique, lancez manuellement le gyrophare avec la commande suivante :
```bash
source venv/bin/activate && python main.py
```

---

En suivant ces étapes, votre gyrophare à LED démarrera automatiquement à chaque démarrage de votre Raspberry Pi, en utilisant un environnement virtuel pour une meilleure gestion des dépendances.

## Utilisation
- Personnalisez les effets lumineux en modifiant le fichier `effects_config.json`.
- Lancez le script principal pour activer le gyrophare.

## Contribution
Les contributions sont les bienvenues ! Veuillez soumettre une pull request ou ouvrir une issue pour discuter des changements proposés.

## Licence
Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Avertissement
**Attention :** Ce projet est actuellement en version bêta. Il est encore en développement actif, et son fonctionnement peut être instable. Utilisez-le avec prudence et soyez conscients des risques potentiels.
