# DPaaS (Débat Politique as a Service)

![GitHub License](https://img.shields.io/github/license/Chelsea486MHz/debat-politique-ia)

Génération automatique, sur-demande, de débats politiques à l'aide de technologies d'intelligence artificielle (IA). Fonctionnalités:

- Imitation de voix

- Animation d'avatars virtuels

- Choix du sujet

Par défaut, les débats sont animés par Jean-Luc Mélenchon et Eric Zemmour, et sont au sujet des violences policières.

Nos récepteurs de dopamines grillés par TikTok ne sont plus capables d'attendre 6 mois entre chaque débat intéressant, on doit bien trouver des solutions pour se divertir.

## Architecture

Chaque interlocuteur est conçu comme bot Discord. Ils interagissent sur un serveur leur étant dédié.

Les conversations sont générées en requêtant l'API OpenAI.

L'audio est généré à partir des complétions OpenAI par un webservice flask basé sur XTTSv2.

Un serveur MariaDB est inclus pour authentifier les requêtes vers XTTS en utilisant un token.

## Pré-requis

Le système est assez complexe, mais si vous savez ce que vous faites vous devrez pouvoir l'étaler sur plusieurs machines ou pods k8s.

Le système est distribué par Docker pour faciliter les choses, mais peut fonctionner en standalone.

Assurez-vous d'avoir une carte graphique Nvidia capable d'inférer le modèle XTTSv2.

Ah, et, installez Docker (obviously)

## Installation

Une utilisation normale ne demande qu'à créer un fichier `.env` à la racine de ce dépôt avec les variables suivantes:

```
MYSQL_PASSWORD="..."
MYSQL_ROOT_PASSWORD="..."

MELENCHON_TOKEN_XTTS="..."
MELENCHON_TOKEN_OPENAI="..."
MELENCHON_TOKEN_DISCORD="..."

ZEMMOUR_TOKEN_XTTS="..."
ZEMMOUR_TOKEN_OPENAI="..."
ZEMMOUR_TOKEN_DISCORD="..."
```

Utilisez votre propre token OpenAI, ou bien un que vous avez générer avec Basaran/Llama-api si vous hébergez votre propre infération de modèle.

Le token Discord correspond à celui du bot. Chaque personnage doit avoit son propre bot Discord.

Se référer à la section suivante pour apprendre à générer des tokens XTTS.

Il faut télécharger le modèle XTTSv2 avant d'effectuer des requêtes pour l'inférer. Pour ce faire, démarrez le conteneur XTTS seul et attendez qu'il termine son téléchargement :

`$ docker compose up xtts`

Une fois le téléchargement terminé, éxécutez la commande :

`$ docker compose up -d`

Vous pouvez maintenant rejoindre le serveur Discord utilisé par vos bots, rejoindre un canal vocal, et éxécuter la commande `!reset`.

L'éxécution de cette commande remet les bots à zéro. L'initiateur de conversation (configurable dans `docker-compose.yml`) va ensuite relancer le sujet.

## Ajout d'un token

Générer un token:

`$ python3 -c 'import secrets; print(secrets.token_urlsafe(48));'`

Hash le token:

`$ python3 -c 'import hashlib; print(hashlib.sha256("YOUR_TOKEN".encode()).hexdigest());'`

Modifier `sql/init.sql` pour insérer le token dans la db:

`INSERT INTO tokens VALUES ('YOUR_HASH');`

## Commentaires de l'autrice

Je recommande d'ajouter un token pour chaque bot, contrôle d'accès traçabilité toussa toussa.

Les runners nodejs peuvent être déployés sur Heroku ou autres services similaires, ils ne sont pas intensifs.

Ah, et amusez-vous. Du temps de nos parents ces technos auraient déclenché des conflits nucléaires.