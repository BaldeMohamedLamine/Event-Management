# Plateforme de Gestion d'Événements

## Description
Cette plateforme web permet aux utilisateurs d'organiser et de participer à divers événements tels que des conférences, des concerts, des ateliers et des réunions professionnelles. Elle offre des fonctionnalités pour la création d'événements, la gestion des inscriptions, le paiement des billets et la visualisation des participants.

## Fonctionnalités
- **Système d'authentification et gestion des utilisateurs**
  - Inscription et connexion avec email et mot de passe.
  - Rôles des utilisateurs : Organisateur et Participant.
  - Gestion des mots de passe avec réinitialisation via email.

- **Gestion des événements**
  - Création, modification et suppression d'événements.
  - Catégorisation des événements.
  - Événements publics et privés.

- **Inscription aux événements**
  - Liste des événements disponibles avec filtres.
  - Détails de chaque événement.
  - Confirmation d'inscription par email.

- **Système de paiement**
  - Intégration avec une plateforme de paiement (Stripe ou PayPal Sandbox) pas encore finis completement.
  - Facture et confirmation de paiement envoyées par email.

- **Gestion des participants**
  - Liste des participants inscrits.
  - Vérification des billets via QR code.

- **Tableau de bord pour les organisateurs**
  - Suivi des événements et statistiques sur les inscriptions.

- **Tests unitaires**
  - Tests pour vérifier la fonctionnalité de l’application. pas encore tester 

## Détails Techniques

### Modèles
- **User** : Extension du modèle utilisateur Django pour inclure les rôles.
- **Event** : Informations sur l'événement (titre, description, date, lieu, etc.).
- **Category** : Catégorie de l'événement.
- **Ticket** : Informations sur les billets.
- **Payment** : Détails du paiement.

### Vues
- Liste des événements, détails d'un événement, tableau de bord, etc.

### Permissions et Authentification
Utilisation de `LoginRequiredMixin` et `PermissionRequiredMixin` pour gérer les accès.

## Installation
1. Clonez le dépôt :
   ```bash
   git clone <URL_DU_DEPOT>
   cd <NOM_DU_DOSSIER>