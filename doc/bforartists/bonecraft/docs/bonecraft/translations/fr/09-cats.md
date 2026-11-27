# Outils CATS {#cats-tools}

[← Sommaire](index.md)

Les outils CATS se trouvent dans **CATS → CATS** dans la barre latérale droite. Appuyez sur **N** pour l’afficher.

Ils apparaissent aussi dans **Properties → Scene** si Preferences → Tabs → Scene Properties → Show est activé. Le commutateur CATS de la vue et celui de Scene Properties contrôlent leurs copies indépendamment.

Les outils suivent [Le pipeline CATS](04-cats-pipeline.md). En haut de la section, sélectionnez l’armature à traiter.

Dans 9.1, plusieurs panneaux contiennent des réglages facultatifs dans un groupe sous les boutons d’action. Les entrées requises restent au-dessus : options de nettoyage de Fix Model, langue source de Translate Bone Names, formes de bouche et os des yeux.

Les outils d’os utilisant Adjust Last Operation s’exécutent immédiatement. Après l’opération, réglez leurs options dans ce panneau. Survolez un bouton ou une option pour lire son infobulle.

---

## Fix Model {#fix-model}

**Phase du pipeline :** 1 (examen recommandé du nettoyage)

**Fonction :** exécute les opérations de nettoyage activées sur le maillage sélectionné. Un avatar propre peut ne pas en avoir besoin.

**Options, toutes désactivables :**

- Appliquer les modificateurs
- Remove doubles : fusionner les sommets en double au même emplacement
- Recalculer les normales : corriger les surfaces inversées
- Retirer la géométrie isolée : faces non attachées au corps
- Retirer les groupes de sommets vides
- Retirer les os sans poids : ceux qui ne déplacent aucun sommet
- Retirer les contraintes et corps rigides inutilisables par VRChat

1. Examinez les options de nettoyage.

2. Activez uniquement les opérations nécessaires à l’avatar.

3. Enregistrez un point de sauvegarde.

4. Sélectionnez **Fix Model** pour exécuter les opérations activées sur le maillage sélectionné en un passage.

5. Inspectez le résultat avant de continuer.

Description de l’image source anglaise (image omise) : options et action Fix Model. Examiner ces choix avant la première phase du pipeline.

*Panneau contextuel natif, BoneCraft 9.2.18. Options et action Fix Model. Examiner ces choix avant la première phase du pipeline.*

---

## Translate Bone Names {#translate-bone-names}

**Fonction :** traduit les noms des os du squelette en noms anglais pour VRChat. Il fonctionne hors ligne avec un dictionnaire intégré de noms d’os connus.

**Langues prises en charge :** japonais (日本語, le plus courant, issu de MMD et de nombreux modèles communautaires), chinois (中文), coréen (한국어), portugais (Português), espagnol (Español) et français (Français).

**Commandes principales :**

1. Sélectionnez la **Language** des noms sources.

2. Sélectionnez **Translate Bone Names**.

Language désigne la langue des noms d’os du modèle, pas celle de l’interface. Pour un modèle MMD japonais, choisissez Japanese quelle que soit la langue de Bforartists.

Description de l’image source anglaise (image omise) : choisir la langue des noms sources avant Translate Bone Names. Aucun nom correspondant n’a été détecté dans cet exemple.

*Panneau contextuel natif, BoneCraft 9.2.18. Choisir la langue des noms sources avant Translate Bone Names. Aucun nom correspondant n’a été détecté dans cet exemple.*

---

## Join Meshes {#join-meshes}

**Fonction :** combine les objets de maillage de l’avatar en un seul maillage. VRChat est plus performant avec un maillage par avatar. Si les sources ont des clés de forme différentes, CATS remplit les clés manquantes avec des formes neutres. Le maillage assemblé possède un ensemble cohérent.

**Commandes principales :** liste des maillages, bouton d’actualisation et **Join Meshes**.

**Quand l’utiliser :** après l’attache et la pondération des vêtements et accessoires.

1. Inspectez les maillages sources.

2. Sélectionnez le nettoyage nécessaire avant assemblage.

3. Enregistrez un point de sauvegarde.

4. Si la liste doit être actualisée, utilisez le bouton situé à côté.

5. Sélectionnez **Join Meshes**.

6. Inspectez le maillage assemblé, ses clés de forme et ses poids.

Description de l’image source anglaise (image omise) : après Refresh Mesh List, la liste contient un maillage coché de six polygones. L’examiner avant Join Meshes.

*Panneau contextuel natif de compilation de test, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Après Refresh Mesh List, la liste contient un maillage coché de six polygones. L’examiner avant Join Meshes.*

---

## Material Atlas Combiner {#material-atlas-combiner}

**Phase du pipeline :** 2 (facultative)

**Fonction :** précalcule plusieurs matériaux sur une planche de textures, ou atlas. Moins de matériaux améliore le rang de performance VRChat.

**Emplacement :** **CATS → CATS → Material Atlas**. Le panneau divise le travail en **1. Choose Target**, **2. Choose Materials and Textures** et **3. Bake and Review**.

### Analyser et choisir les sources {#analyze-and-choose-sources}

Description de l’image source anglaise (image omise) : Material Atlas avant analyse. Choisir la cible, conserver une sauvegarde, puis Analyze Materials.

*Panneau contextuel natif, BoneCraft 9.2.18. Material Atlas avant analyse. Choisir la cible, conserver une sauvegarde, puis Analyze Materials.*

**Target** propose **Active Avatar**, **Selected Meshes** et **Visible Scene**. Active Avatar utilise les maillages enfants de l’armature active. Sans armature active, il utilise le maillage actif. Visible Scene utilise les maillages visibles. Pour un ensemble précis, choisissez Selected Meshes.

1. Enregistrez une copie du fichier.

2. Choisissez la portée nécessaire dans **Target**.

3. Gardez **Preserve Backup Duplicate** activé.

4. Sélectionnez **Analyze Materials**.

5. Sélectionnez un groupe d’atlas.

6. Pour précalculer ce groupe, cochez sa case.

7. Dans **Materials to combine**, activez les matériaux à inclure.

8. Dans **Texture images**, activez les images à inclure.

9. Répétez l’examen des sources pour chaque groupe activé.

**Analyze Materials** crée les listes de sources. Son libellé devient **Refresh Analysis** dès que des groupes existent. Refresh reconstruit les listes et leurs choix. Examinez-les de nouveau après actualisation.

Chaque liste possède **Select All** et **Deselect All**. Ces boutons changent les cases **Include** de cette liste pour le groupe actif, pas la ligne surlignée. Les listes de matériaux et textures restent indépendantes. Les autres groupes conservent leurs choix. Les textures manquantes restent décochées. La sélection groupée n’active pas un groupe désactivé.

Les mêmes actions groupées sont disponibles dans **Object → Atlas Source Selection**. Acceptez ou rétablissez un aperçu d’atlas en attente avant de changer sa sélection de sources.

Un groupe activé nécessite au moins deux matériaux cochés. Le précalcul ignore les groupes désactivés ou à un seul matériau. Les emplacements de matériaux exclus et les références partagées restent distincts. Exclure une image l’omet du précalcul sans exclure son matériau entier.

Les matériaux transparents et émissifs commencent dans des groupes séparés. Les groupes Alpha Blend sont désactivés au départ pour préserver l’ordre de rendu. Activez-les si vous acceptez d’éventuels changements de cet ordre.

**Source Details** est désactivé au départ. Activez-le pour examiner les diagnostics de maillage, avertissements de clés de forme et d’UV, tailles de matériaux, rôles des textures et groupes de sources en double. **Override Size** d’un matériau expose son choix de taille. Une taille personnalisée utilise **Width** et **Height**. Les matériaux à couleur seule utilisent la taille **Fallback**.

La liste des groupes propose **Resolution** et des commandes d’ajout et retrait. **Add Group** et **Remove Group** gèrent les groupes sans lancer eux-mêmes de précalcul.

Description de l’image source anglaise (image omise) : sources analysées de deux maillages d’exemple. Examiner les cases des groupes, matériaux et images, y compris l’avertissement UV.

*Version candidate de BoneCraft 9.2.19. Compilation de test native de Bforartists 5.2.3, Blender 5.4 Alpha. Sources analysées de deux maillages d’exemple. Examiner les cases des groupes, matériaux et images, y compris l’avertissement UV.*

### Précalculer et examiner {#bake-and-review}

1. Après examen des listes sources, sélectionnez **Bake Checked Sources**.

2. Lisez le résumé du contrôle préalable.

3. Corrigez toute erreur de source ou de réglage signalée.

4. Une fois les changements prévus corrects, confirmez le précalcul.

5. Inspectez l’atlas, la transparence, les clés de forme et le canal UV exporté.

6. Si le résultat convient, sélectionnez **Accept — Delete Backup**.

Pour retrouver le résultat d’origine, choisissez plutôt **Revert — Restore Originals**. Accept supprime la sauvegarde. Revert restaure objets, matériaux et visibilité d’origine, et réinitialise les résultats de comptage de matériaux.

Description de l’image source anglaise (image omise) : un groupe Opaque de 2048 pixels précalculé depuis deux maillages d’exemple. Le panneau indique toujours de 2 à 2 matériaux et un rang Excellent. Examiner l’avertissement UV avant Accept ou Revert.

*Version candidate de BoneCraft 9.2.19. Bforartists officiel 5.2.3, Blender 5.3 Alpha. Un groupe Opaque de 2048 pixels précalculé depuis deux maillages d’exemple. Le panneau indique toujours de 2 à 2 matériaux et un rang Excellent. Examiner l’avertissement UV avant Accept ou Revert.*

**Preserve Backup Duplicate** est activé au départ. Il conserve un duplicata pré-atlas visible pour examen et Revert. Le désactiver supprime les originaux après création de l’atlas et ne laisse aucune sauvegarde de rétablissement. Avant de le désactiver, enregistrez un fichier distinct.

Acceptez ou rétablissez l’aperçu actuel avant une autre analyse ou un autre précalcul. Si un objet analysé, emplacement de matériau ou classification de rendu change, le contrôle préalable peut annuler avant de créer une sauvegarde.

Avant un nouveau précalcul :

1. Sélectionnez **Refresh Analysis**.

2. Examinez les choix reconstruits.

**Smart Combine Materials** est le raccourci automatique initial, avant toute analyse. Avec **Auto Analyze** activé, il reconstruit l’analyse avant précalcul. Utilisez **Bake Checked Sources** pour précalculer vos choix examinés sans réanalyse automatique. Les anciennes instructions appellent cet opérateur **Bake Atlas**.

**Si le précalcul ne démarre pas :** il nécessite Cycles. Si Bforartists signale son absence, utilisez une compilation complète comprenant Cycles.

### Advanced Options {#advanced-options}

**Advanced Options** remplace l’ancien libellé Override Inherited Settings. Ce groupe contient des commandes facultatives de procédure, précalcul, UV et sortie.

| Réglage | Utilité |
| --- | --- |
| Auto Analyze | Reconstruit les groupes pour le raccourci automatique Smart Combine. |
| Debug Report / Copy Debug Report | Active les diagnostics et copie le dernier rapport pour le dépannage. |
| Albedo (Color) | Passe de couleur de base obligatoire. La garder activée. |
| Normal Map / Emission / Roughness | Passes de sortie distinctes facultatives. Examiner les données sources prises en charge et les résultats. |
| Metallic / Pack ORM Channels | Le contrôle préalable bloque ces options dans cette compilation. Les laisser désactivées. |
| Packing Preset / Bake Padding / UV Margin | Règle les marges et l’espacement entre îlots d’atlas. |
| Pixel Art No-Bleed / Preserve Island Orientation | Contrôle les marges et le traitement pris en charge de l’orientation des îlots. |
| UV Method / UV Seed / Rotation Step | Choisit le rangement et sa variation. La graine et la rotation n’apparaissent que pour les méthodes qui les utilisent. |
| Keep Source UV Maps | Conserve les couches UV sources sur le maillage de sortie. Désactivé au départ. |
| Fallback Size | Règle la place allouée dans l’atlas aux matériaux à couleur seule sans images. |
| Format Output | Choisit PNG, TGA ou EXR. EXR conserve l’émission supérieure à 1.0. PNG et TGA l’écrêtent. |
| Material Output Type / Surface Output | Choisit le type de rendu et le shader de surface du matériau généré. |
| Path Output | Règle le dossier des textures de sortie. |

Avec **Keep Source UV Maps** désactivé, le maillage d’atlas final utilise `atlas_uv` comme UV0 pour FBX, Unity et VRChat. L’activer peut laisser `atlas_uv` sur UV1. Vérifiez le canal UV du moteur si vous conservez les cartes sources. Les maillages à couleur seule sans UV créés reçoivent aussi la couche UV d’atlas générée.

### Préservation et limites {#preservation-and-limits}

Le combinateur conserve la teinte Principled connectée, le mappage de textures et l’alpha pendant le précalcul. Il traite les maillages sources masqués au rendu avec des copies temporaires. Les références de matériaux exclus restent partagées avec d’autres objets. Les positions géométriques, clés de forme et parentages restent protégés durant l’assemblage.

Les matériaux VRM / MToon conservent leur voie de repli dédiée. La classification de transparence tient compte du graphe alpha et de l’alpha réel des textures. Le réglage DITHERED seul ne classe pas un matériau comme transparent. Des tuiles problématiques peuvent apparaître magenta après précalcul. Inspectez-les avant d’accepter.

Les corrections documentées ont été vérifiées sur l’hôte avec des scènes générées. Elles ne certifient pas tous les avatars ou graphes de shaders de production. Le comportement visible du navigateur de fichiers, la disposition de la fenêtre réelle et l’annulation/rétablissement interactifs conservent les limites de tests consignées. Consultez le [relevé historique des corrections](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md) et la [revue d’interface 9.2.15](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md).

**Crédits de filiation :** cette procédure poursuit l’intégration de CATS et crédite le Cats Blender Plugin d’origine. La filiation de Material Combiner crédite Grim-es/material-combiner-addon. Le travail UV s’inspire d’UV Toolkit par Alexander Belyakov et du dépôt d’archives oRazeD/UVToolkit. BoneCraft implémente ses propres utilitaires UV d’atlas. Il n’inclut pas le code source d’UVToolkit.

---

## Visemes {#visemes}

**Phase du pipeline :** 3

**Fonction :** crée les 15 visèmes VRChat à partir de trois formes de bouche de base.

**Avant génération :** **A Shape**, **O Shape** et **CH Shape** nécessitent chacun une source. Chaque champ doit nommer une clé de forme de bouche existante.

**Sélection manuelle des sources :**

1. Sélectionnez la clé source dans **A Shape**.

2. Sélectionnez la clé source dans **O Shape**.

3. Sélectionnez la clé source dans **CH Shape**.

**Alternative automatique :** sélectionnez plutôt **Auto-Detect**.

**Après l’une ou l’autre méthode :**

1. Vérifiez que les trois champs nomment des clés existantes.

2. Si nécessaire, dépliez Options sous les boutons.

3. Si nécessaire, changez l’option d’écrasement des visèmes existants.

4. Sélectionnez **Generate Visemes**.

Consultez le [guide 13, phase 2](03-guides-b.md#phase-2--viseme-generation).

Description de l’image source anglaise (image omise) : CATS Visemes : sélectionner les formes sources A, O et CH, ou utiliser Auto-Detect, avant Generate Visemes.

*Panneau contextuel natif, BoneCraft 9.2.18. CATS Visemes : sélectionner les formes sources A, O et CH, ou utiliser Auto-Detect, avant Generate Visemes.*

---

## Eye Tracking {#eye-tracking}

**Phase du pipeline :** 4 (après Fix Model)

Auto-Detect recherche des noms courants d’os des yeux. Il n’utilise ni la géométrie du maillage ni les positions des os.

1. Vérifiez **Left Eye** et **Right Eye**.

2. Si une affectation manque, sélectionnez l’os manuellement.

Si vous renommez les os :

1. Relancez la détection.

2. Vérifiez de nouveau les deux affectations.

Si le mouvement des yeux est incorrect, inspectez l’orientation des os, les contraintes et l’avatar exporté.

**Fonction :** trouve les os des yeux et les nomme `LeftEye` et `RightEye` comme l’exige VRChat. Il crée les contraintes de rotation du mouvement des yeux dans VRChat.

**Commandes principales :**

- **Auto-Detect** recherche les noms courants d’os des yeux gauche et droit
- **Left Eye** et **Right Eye** désignent les os des yeux si vous les choisissez vous-même
- **Up Limit**, **Down Limit** et **Side Limit** définissent l’amplitude de rotation en degrés
- **Create Eye Tracking** renomme les os et crée les contraintes

Description de l’image source anglaise (image omise) : Eye Tracking avant détection des os. Les limites d’exemple sont de 30 degrés vers le haut, 20 vers le bas et 30 latéralement.

*Panneau contextuel natif de compilation de test, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Eye Tracking avant détection des os. Les limites d’exemple sont de 30 degrés vers le haut, 20 vers le bas et 30 latéralement.*

---

## Pose et clés de forme {#pose--shape-keys}

**Phase du pipeline :** 5 (facultative)

### Pose to Shape Key {#pose-to-shape-key}

Le bouton actuel capture le **mélange actuel de clés de forme** du maillage sélectionné. Il ne précalcule pas la déformation des os d’armature.

1. Passez en mode Objet.

2. Sélectionnez le maillage cible.

3. Réglez ses clés de forme existantes sur le mélange à capturer.

4. Sélectionnez **Pose to Shape Key**.

5. Saisissez un nom.

6. Confirmez l’opération.

7. Remettez les valeurs des clés d’origine à 0.

8. Examinez la nouvelle clé seule.

L’outil règle la nouvelle clé sur 1 et laisse les clés d’origine actives. Conserver leurs valeurs ajoute une seconde fois leur déformation.

### Enregistrer une pose déformée par les os {#save-a-bone-deformed-pose}

Utilisez cette procédure native pour conserver une déformation due aux os d’armature. Le modificateur doit préserver la topologie du maillage.

**Save as Shape Key** conserve le modificateur Armature. **Apply as Shape Key** le retire.

1. Posez l’armature.

2. Enregistrez un point de sauvegarde.

3. Revenez en mode Objet.

4. Sélectionnez le maillage déformé.

5. Ouvrez **Properties → Modifiers**.

6. Ouvrez le menu du modificateur Armature.

7. Sélectionnez **Save as Shape Key**.

8. Réinitialisez la pose des os.

9. Réinitialisez toute valeur de clé de forme d’origine.

10. Réglez la nouvelle clé sur 1.

11. Examinez cette clé seule.

Si la pose des os ou le mélange source reste actif, il ajoute une seconde fois la déformation. Cette opération native ne met pas à jour la coche Pose To Shape du pipeline BoneCraft.

Description de l’image source anglaise (image omise) : le menu natif du modificateur Armature propose Save as Shape Key séparément d’Apply as Shape Key.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Menu natif du modificateur Armature avant exécution. Save as Shape Key conserve le modificateur ; cette image ne montre pas le résultat d’une pose capturée.*

### Shape Key to Basis {#shape-key-to-basis}

Fait de la clé de forme active autre que Basis la nouvelle Basis. Les autres clés sont ajustées par rapport à cette base.

1. Avant l’opération, enregistrez un point de sauvegarde.

2. Après l’opération, examinez les clés restantes.

Description de l’image source anglaise (image omise) : Pose to Shape Key capture le mélange actuel de clés. Shape Key to Basis fait de la clé active la nouvelle Basis.

*Panneau contextuel natif, BoneCraft 9.2.18. Pose to Shape Key capture le mélange actuel de clés. Shape Key to Basis fait de la clé active la nouvelle Basis.*

---

## Transformations et FBT {#transforms--fbt}

**Phase du pipeline :** 6 (dernière)

### Apply All Transforms {#apply-all-transforms}

Applique position, rotation et échelle au maillage et à l’armature, réinitialisant leurs canaux de transformation. Les outils précédents restent disponibles.

1. Avant l’opération, enregistrez un point de sauvegarde.

2. Comparez l’avatar avant et après l’opération.

Si la taille diffère après exportation, inspectez les transformations du maillage et de l’armature et les réglages d’échelle d’exportation et d’importation.

### Fix FBT {#fix-fbt}

Correction de transformation pour Full Body Tracking : déplace l’os racine au niveau du sol.

### Remove FBT {#remove-fbt}

Retire la correction de Fix FBT.

Description de l’image source anglaise (image omise) : Apply All Transforms, Fix FBT et Remove FBT sont les dernières actions du pipeline.

*Panneau contextuel natif, BoneCraft 9.2.18. Apply All Transforms, Fix FBT et Remove FBT sont les dernières actions du pipeline.*

---

## Outils d’os {#bone-tools}

- **Create Root Bone** ajoute un os racine (nommé par **Root Name**) à la base de la hiérarchie
- **Merge Bones** fusionne avec leurs parents les os plus courts que **Merge Threshold**
- **Duplicate Bones** duplique les os sélectionnés

Description de l’image source anglaise (image omise) : Create Root Bone, Merge Bones et Duplicate Bones. Régler les noms de racine et seuils après l’action.

*Panneau contextuel natif, BoneCraft 9.2.18. Create Root Bone, Merge Bones et Duplicate Bones. Régler les noms de racine et seuils après l’action.*

---

## Outils d’armature {#armature-tools}

**Fonction :** fusionne une armature dans une autre, par exemple celle d’une tenue dans celle du corps.

**Commandes principales :**

- **Base / Root** : armature conservée (le résultat garde son nom)
- **Incoming** : armature fusionnée dans la base. Les os de même nom sont fusionnés avec ceux de la base.
- Naming Prep : harmonise les noms d’os des deux rigs avant fusion. Il fonctionne sur tout rig, y compris ceux provenant d’autres sources que Mixamo.
- Options pour parenter automatiquement les os et joindre ensuite les maillages
- **Merge Incoming Into Base** : fusionne

Pour Naming Prep :

1. Sélectionnez Mixamo Prefixed.

2. Sélectionnez **Normalize Merge Names**.

3. Sélectionnez Mixamo Stripped.

4. Sélectionnez de nouveau **Normalize Merge Names**.

Les deux rigs ont finalement les mêmes noms.

Pour une fusion par étapes avec aperçus, utilisez Bone Merge (voir [Rig Builder](06-rig-builder.md#bone-merge)).

Description de l’image source anglaise (image omise) : choisir les armatures Base et Incoming, examiner Naming Prep, puis Merge Incoming Into Base.

*Panneau contextuel natif, BoneCraft 9.2.18. Choisir les armatures Base et Incoming, examiner Naming Prep, puis Merge Incoming Into Base.*

---

## Outils de maillage {#mesh-tools}

- **Separate by Materials** : un maillage par matériau
- **Separate by Loose Parts** : un maillage par pièce connectée
- **Separate by Shape Keys** : détache les parties déplacées par les clés de forme

Description de l’image source anglaise (image omise) : séparer les maillages par matériaux, parties disjointes ou clés de forme.

*Panneau contextuel natif, BoneCraft 9.2.18. Séparer les maillages par matériaux, parties disjointes ou clés de forme.*

---

## Smart Automatic Weights {#smart-automatic-weights}

**Smart Automatic Weights** ouvre une boîte de dialogue avec des valeurs par défaut adaptées et une sauvegarde masquée.

1. Vérifiez le maillage cible et l’armature.

2. Pour recalculer les poids depuis le rig existant, sélectionnez Body.

3. Pour transférer des poids depuis un maillage source pondéré, sélectionnez plutôt Clothing.

**Advanced Recalculation** déplie une indication d’emplacement vers **BoneCraft → Skin → Weight Tools**. Il n’ouvre pas ici les commandes complètes. Consultez [Outils de rig](05-rig-tools.md#automatic-bone-weight-recalculation).

Description de l’image source anglaise (image omise) : Smart Automatic Weights ouvre sa boîte de configuration. Advanced Recalculation indique les commandes de poids complètes.

*Panneau contextuel natif, BoneCraft 9.2.18. Smart Automatic Weights ouvre sa boîte de configuration. Advanced Recalculation indique les commandes de poids complètes.*

---

## Pipeline Status et Operation Ledger {#pipeline-status-and-operation-ledger}

Pipeline Status indique lesquelles des six phases sont terminées. Operation Ledger énumère chaque opération CATS avec son heure et son résultat : Changed, Clean ou Failed. **Copy** copie le registre dans le presse-papiers. **Clear** le vide. Consultez [Le pipeline CATS](04-cats-pipeline.md).

Suivant : [Solutions rapides et glossaire](10-reference.md)
