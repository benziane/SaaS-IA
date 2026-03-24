---
name: db-migration
description: |
  Skill pour la gestion des migrations de base de donnees Alembic.
  TRIGGER quand: modification de modeles SQLModel, ajout/suppression de colonnes,
  creation de nouvelles tables, ou quand l'utilisateur mentionne "migration" ou "schema".
---

# Migrations Alembic - PostgreSQL + SQLModel

## Workflow de migration

### 1. Modifier le modele SQLModel
Les modeles sont dans `mvp/backend/app/models/`. Modifier le modele existant ou en creer un nouveau.

### 2. Generer la migration
```bash
cd mvp/backend
alembic revision --autogenerate -m "description_claire"
```

### 3. Verifier le fichier genere
**TOUJOURS** lire et verifier le fichier de migration genere dans `mvp/backend/alembic/versions/` avant de l'appliquer.

Verifier:
- Les operations `upgrade()` et `downgrade()` sont coherentes
- Pas de perte de donnees accidentelle
- Les types de colonnes sont corrects
- Les index et contraintes sont presents

### 4. Appliquer la migration
```bash
alembic upgrade head
```

## Regles de securite

1. **Ne jamais supprimer une colonne directement** - proceder en 2 etapes:
   - Migration 1: rendre la colonne nullable / ajouter la nouvelle colonne
   - Migration 2: supprimer l'ancienne colonne (apres deploiement)

2. **Data migration** - si des donnees doivent etre transformees:
   ```python
   def upgrade():
       # 1. Ajouter la nouvelle colonne
       op.add_column('users', sa.Column('full_name', sa.String()))
       # 2. Migrer les donnees
       op.execute("UPDATE users SET full_name = first_name || ' ' || last_name")
       # 3. Supprimer les anciennes colonnes (optionnel, migration suivante)
   ```

3. **Toujours tester** le downgrade apres l'upgrade

4. **Coherence Pydantic** - mettre a jour les schemas Pydantic correspondants dans `schemas.py`

5. **Index** - ajouter des index sur les colonnes frequemment filtrees/triees

## Commandes utiles
```bash
alembic current                    # Version actuelle
alembic history                    # Historique des migrations
alembic upgrade head               # Appliquer toutes les migrations
alembic downgrade -1               # Annuler la derniere migration
alembic revision --autogenerate -m "msg"  # Generer une migration
```
