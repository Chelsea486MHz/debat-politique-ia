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

MELENCHON_TOKEN_DPAAS="..."
MELENCHON_TOKEN_OPENAI="..."
MELENCHON_TOKEN_DISCORD="..."

ZEMMOUR_TOKEN_DPAAS="..."
ZEMMOUR_TOKEN_OPENAI="..."
ZEMMOUR_TOKEN_DISCORD="..."
```

Utilisez votre propre token OpenAI, ou bien un que vous avez générer avec Basaran/Llama-api si vous hébergez votre propre infération de modèle.

Le token Discord correspond à celui du bot. Chaque personnage doit avoit son propre bot Discord.

Se référer à la section suivante pour apprendre à générer des tokens DPAAS.

Vous pouvez maintenant construire les images Docker. Le premier build est lent car les modèles d'IA se font télécharger, mais les builds suivants seront plus rapides car le modèle sera en cache sur votre machine.

`$ docker compose build`

Vous pouvez à présent démarrer le stack de services. Le flag `-d` est utilisé pour les faire tourner en fond:

`$ docker compose up -d`

## Utilisation

Vous pouvez maintenant rejoindre le serveur Discord utilisé par vos bots, rejoindre un canal vocal, et éxécuter la commande `!reset` suivie des mots qui seront prononcés par l'initiateur de conversation (à défaut, Mélenchon (configurable dans `docker-compose.yml`)).

Par exemple, pour que Mélenchon lance le débat avec Zemmour sur le sujet des violences policières :

`! reset La police est violente`

Mélenchon prononcera "La police est violente" et Zemmour répondra.

## Lenteur

Oui, c'est lent. Il faut inférer un modèle d'IA à chaque tour de parole, ce n'est pas rapide.

Temp d'éxécution pour un temps de parole sur Ryzen 5700X / 64 Go RAM / RTX 3060 12 Go : 1-2 min

## Ajout d'un token DPAAS

Certains composants de DPaaS comme la génération par IA sont gourmands en ressources et bénéficient de fonctionner en bare-metal sur des machines dédiées sur un réseau local ou à distance. Dans le cas d'usage où les machines sont à distance, il est vital de protéger les services en authentifiant les requêtes avec un token pour éviter les attaques par déni de service. Cependant, l'authentification par token ne peut être efficace que lorsqu'associée à un tunnel chiffré, je recommande donc vivement de cacher les services derrière un reverse-proxy.

Générer un token:

`$ python3 -c 'import secrets; print(secrets.token_urlsafe(64));'`

Hash le token:

`$ python3 -c 'import hashlib; print(hashlib.sha256("YOUR_TOKEN".encode()).hexdigest());'`

Modifier `sql/init.sql` pour insérer le token dans la db:

`INSERT INTO tokens VALUES ('YOUR_HASH');`

Les tokens par défaut sont :

```
MELENCHON_TOKEN_DPAAS="hvcyntF4SMqRCSXWGz5p-4H0vag9tvFyz2GXOTOXZ7XjLcsSaPbvrq2ziFxzDaMl"
ZEMMOUR_TOKEN_DPAAS="utK9pJVPbDcinnxLw-qA-83Nct2BrzB255eQfLv5XytupEX8Q4ARw4gRhgAA8PF9"
```

## Commentaires de l'autrice

Je recommande d'ajouter un token pour chaque bot, contrôle d'accès traçabilité toussa toussa.

Les runners nodejs peuvent être déployés sur Heroku ou autres services similaires, ils ne sont pas intensifs.

Ah, et amusez-vous. Du temps de nos parents ces technos auraient déclenché des conflits nucléaires.