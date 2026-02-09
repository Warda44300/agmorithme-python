# SECURITY_FIRST

## Objectif
Ce document définit les règles “Sécurité First” appliquées au pipeline data (CSV/DB/API)
pour garantir un workflow enrichissement-first, sans actions externes automatiques.

## Principes non négociables
- Sécurité > volume, vision long terme.
- Aucune action externe (invitation/message) sans validation manuelle explicite.
- Aucun scoring décisionnel tant que `statut != a_valider` et validation manuelle effective.
- Complétude obligatoire : `poste` ET `entreprise` requis pour passer à `a_valider`.

## Statuts V1 (valeurs autorisées)
- `a_enrichir`
- `enrichi`
- `a_valider`
- `rejete`

## Champs “Sécurité First” (data-only)
- `action_linkedin_autorisee` : "non" par défaut
- `validated_by` : vide par défaut
- `validated_at` : vide par défaut
- `interdit_action` : "oui" si incomplet (poste/entreprise manquants)

## Contrats opérationnels (sans logique d’action)
- Passage vers `a_valider` uniquement si `poste` et `entreprise` non vides.
- `rejete` possible uniquement après validation manuelle.
- Tant que non validé : aucune action externe, aucun scoring décisionnel.

## Pipeline data (résumé)
1. Normalisation (`01_`) : préparation CSV + statut `a_enrichir`
2. Enrichissement minimal (`02_`) : extraction `linkedin_slug`
3. Dédoublonnage (`03_`) : unicité `linkedin_slug`
4. Scoring (`04_`) : pré-scoring non décisionnel (diagnostic uniquement)

## Enrichissement LinkedIn via session utilisateur (contrat)
- Entrée minimale : `linkedin_url` (+ `linkedin_slug` si présent)
- Sortie attendue : `poste`, `entreprise`, `secteur`, `localisation`
- Transition vers `a_valider` seulement si `poste` + `entreprise` remplis.

## Traçabilité & conformité
- Toutes les validations sont manuelles et tracées (`validated_by`, `validated_at`).
- Aucune automatisation d’action LinkedIn ou WhatsApp dans le pipeline data.
