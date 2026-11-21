# Guides 8–13 {#guides-813}

[← Sommaire](index.md)

## Guide 8 : Configurer la synchronisation labiale {#guide-8-set-up-lip-sync}

> **Durée :** Environ 10–20 minutes
> **Résultat :** La bouche de votre avatar bouge correctement lorsque vous parlez dans VRChat

**Avant de commencer — vérifiez ces points :**

- [ ] Le maillage de la tête de votre avatar possède des clés de forme pour la bouche (également appelées blend shapes ou cibles de morphing : les différentes positions de la bouche utilisées pour parler)
- [ ] Vous connaissez approximativement le nom des clés de forme (consultez la liste Shape Keys dans les propriétés Object Data du maillage)

> Visème = une forme de bouche correspondant à un son. `aa` correspond au son « ahh », `O` au son « ohh », etc. VRChat utilise 15 visèmes pour animer la synchronisation labiale de votre avatar.
>
> Clé de forme (blend shape) = une version enregistrée de votre maillage dans une autre position. Votre clé de forme de bouche ouverte est votre maillage avec la bouche ouverte.

---

### Étape 1 — Ouvrir VRChat Viseme Mapping {#step-1--open-vrchat-viseme-mapping}

Consultez les [commandes Viseme Mapping et Face Tracking](08-vrchat.md#vrchat-viseme-mapping).

Ouvrez **CATS → VRChat Tools → Facial → VRChat Viseme Mapping**.

---

### Étape 2 — Associer automatiquement les visèmes {#step-2--auto-map-visemes}

Cliquez sur **Auto-Map All Visemes**. BoneCraft lit les clés de forme de votre maillage et les associe par leur nom aux 15 emplacements de visèmes de VRChat.

**Ce que vous devriez voir :** La liste des visèmes, dont la plupart des emplacements affichent une clé de forme associée.

---

### Étape 3 — Compléter les emplacements manquants {#step-3--fill-in-missing-slots}

Un emplacement vide affiche « (unmapped) ».

1. Sélectionnez le bouton de l’emplacement pour ouvrir la liste de recherche des clés de forme du maillage.

2. Saisissez du texte pour filtrer la liste.

3. Sélectionnez la clé de forme la plus proche.

Pour vider un emplacement, sélectionnez « (unmapped) ». Correspondances courantes :

| Visème VRChat | Son correspondant | Clé de forme à rechercher |
|---|---|---|
| `aa` | « ahh » | mouth_open, A, aa |
| `O` | « ohh » | mouth_o, OH, oh |
| `CH` | « ch » / « sh » | mouth_ch, CH |
| `PP` | lèvres jointes (P, B, M) | mouth_m, MM, lips_together |
| `SS` | « sss » / « zzz » | mouth_s, SS |

**Clés de forme de visèmes manquantes :** CATS → **Visemes** crée les 15 clés à partir de trois formes de base : A, O et CH. Si le maillage n’a aucune forme de bouche, créez d’abord ces trois formes. Consultez le [guide 13, phase 2](#phase-2--viseme-generation).

---

### Étape 4 — Vérifier une forme de bouche {#step-4--check-a-mouth-shape}

1. Dans **Properties → Object Data → Shape Keys**, réglez la valeur de la clé associée sur 1.0.

2. Examinez la forme de la bouche.

3. Remettez la valeur à 0.

---

### Étape 5 — Suivi du visage (facultatif) {#step-5--face-tracking-optional}

Sous la liste des visèmes, **Face Tracking (SteamVR)** prépare les formes d’expression pour le matériel de suivi du visage. Cette fonction est facultative : la plupart des utilisateurs n’en ont pas besoin.

**Ce que cela permet :** La bouche de votre avatar bouge lorsque vous parlez dans VRChat. Les expressions s’appuient sur les clés de forme que vous venez d’associer.

---

## Guide 9 : Améliorer les performances de votre avatar {#guide-9-improve-your-avatars-performance}

> **Durée :** Environ 15–25 minutes
> **Résultat :** Un meilleur classement de performances VRChat et un chargement plus rapide pour les autres joueurs

**Avant de commencer — vérifiez ces points :**

- [ ] Votre avatar est terminé (rig créé, vêtements ajoutés, synchronisation labiale configurée)
- [ ] Vous connaissez le classement visé (Good ou Excellent pour la plupart des utilisateurs)

> Classement de performances = l’évaluation, par VRChat, des ressources nécessaires à votre avatar. Les avatars classés Very Poor peuvent être masqués par les autres joueurs. Les avatars Good et Excellent se chargent rapidement et sont toujours affichés.

---

### Étape 1 — Vérifier le classement actuel {#step-1--check-the-current-rank}

1. Ouvrez **CATS → VRChat Tools**.

2. Dans Performance, sélectionnez **Calculate Performance Rank**.

BoneCraft indique le classement global et l’écart de chaque mesure par rapport au niveau suivant. Les mesures comprennent les polygones, les maillages déformés par un squelette, les emplacements de matériaux, les os, les PhysBones et les contacts.

Consultez les [commandes Performance](08-vrchat.md#check-performance).

---

### Étape 2 — Nettoyer {#step-2--clean-up}

VRChat Optimizer, dans la même section, propose les outils de nettoyage. **What-If Mode** est activé au départ. Chaque correction indique les modifications proposées sans les appliquer.

1. Exécutez la correction nécessaire en What-If Mode.

2. Consultez le rapport.

3. Pour appliquer ces modifications, désactivez What-If Mode.

4. Exécutez à nouveau la correction.

Corrections disponibles :

1. **Remove Zero-Weight Bones** — supprime les os qui ne déplacent aucune partie du maillage
2. **Merge Same-Material Meshes** — réunit les maillages qui partagent un matériau
3. **Remove Unused Shape Keys** — supprime les clés de forme vides dont la déformation est identique à Basis. Cette fonction ne vérifie pas les références provenant d’autres outils.
4. **Remove Unused Vertex Groups** — supprime les groupes de poids vides

---

### Étape 3 — Réduire le nombre de polygones (si nécessaire) {#step-3--reduce-the-polygon-count-if-needed}

Consultez les [commandes Performance et Decimation](08-vrchat.md#check-performance).

Si le nombre de polygones est trop élevé :

1. Sélectionnez le maillage.

2. Dans VRChat Decimation, réglez le ratio cible.

3. Sélectionnez **Preview**.

4. Examinez le résultat.

5. Pour conserver le résultat, sélectionnez **Apply**.

Un ratio de 0.5 divise le nombre de polygones par deux. Un ratio de 0.8 en retire 20%. La décimation protège les clés de forme.

> Commencez à 0.8. Réduisez progressivement le ratio en vérifiant l’apparence de l’avatar. De petites réductions peuvent améliorer les performances sans changement visuel important.

---

### Étape 4 — Fusionner les matériaux (facultatif) {#step-4--merge-materials-optional}

Si votre avatar utilise de nombreux matériaux, réunissez-les dans une seule planche de textures (un atlas). Dans l’onglet **CATS** → **CATS** → **Material Atlas** :

1. Enregistrez une copie du fichier.
2. Réglez **Target** sur les maillages à traiter.
3. Laissez **Preserve Backup Duplicate** activé.
4. Cliquez sur **Analyze Materials**.
5. Sélectionnez un groupe d’atlas.
6. Cochez au moins deux matériaux dans ce groupe activé.
7. Cochez les images de texture à inclure.
8. Utilisez **Select All** ou **Deselect All** au-dessus de l’une ou l’autre liste si nécessaire.
9. Cliquez sur **Bake Checked Sources**.
10. Consultez le résumé des vérifications préalables avant de confirmer la cuisson.
11. Examinez les matériaux cuits, la transparence et les UV.
12. Cliquez sur **Accept — Delete Backup** pour conserver le résultat.

Utilisez plutôt **Revert — Restore Originals** si le résultat doit être modifié. Accept supprime la sauvegarde. Désactiver **Preserve Backup Duplicate** retire l’option Revert.

La sélection en masse ne concerne que sa liste de sources dans le groupe actif. Les textures manquantes restent décochées. L’autre liste et les autres groupes restent inchangés.

**Refresh Analysis** reconstruit les listes de sources et leurs choix. Utilisez **Bake Checked Sources** après avoir vérifié vos choix. **Smart Combine Materials** est le raccourci automatique initial.

[Outils CATS : Material Atlas Combiner](09-cats.md#material-atlas-combiner) explique chaque réglage.

---

### Étape 5 — Vérifier à nouveau le classement {#step-5--check-the-rank-again}

Cliquez à nouveau sur **Calculate Performance Rank** pour voir l’amélioration.

**Ce que cela permet :** Un meilleur classement signifie que davantage de joueurs voient votre avatar. Un avatar Good ou Excellent se charge rapidement, sollicite moins le GPU et s’affiche par défaut chez les autres joueurs.

---

## Guide 10 : Enregistrer et réutiliser des poses {#guide-10-save-and-reuse-poses}

> **Durée :** Environ 5–10 minutes
> **Résultat :** Une bibliothèque de poses enregistrées, applicables en un clic

**Avant de commencer — vérifiez ces points :**

- [ ] Votre avatar possède un squelette terminé
- [ ] Vous êtes en **Pose Mode**

Pour passer en Pose Mode :

1. Sélectionnez l’armature.

2. Appuyez sur Ctrl+Tab.

Vous pouvez aussi sélectionner **Pose Mode** dans le menu des modes en haut à gauche de la vue.

---

### Étape 1 — Ouvrir la bibliothèque de poses {#step-1--open-the-pose-library}

Dans l’onglet **BoneCraft** de la Tool Shelf à gauche, développez **Review** → **Pose Library**.

Consultez les [commandes Pose Library](05-rig-tools.md#pose-library).

---

### Étape 2 — Poser votre avatar {#step-2--pose-your-avatar}

Placez les os dans la pose à enregistrer. Une pose peut combiner des rotations de bras, une inclinaison de tête et d’autres positions d’os.

---

### Étape 3 — Enregistrer la pose {#step-3--save-the-pose}

1. Sélectionnez **Save**.

2. Saisissez un nom de pose, par exemple « Signe de paix » ou « Réflexion ».

**Category** regroupe les poses sous des noms tels que « Salutations ». **Filter** affiche une catégorie à la fois. La pose enregistrée comprend une miniature de la vue.

---

### Étape 4 — Appliquer une pose enregistrée {#step-4--apply-a-saved-pose}

1. Sélectionnez une pose.

2. Sélectionnez **Apply**.

- **Blend** — applique la pose avec une intensité partielle, pour mélanger deux poses
- **Mirror** — applique la pose en inversant la gauche et la droite

**Rename** et **Delete** servent à gérer la liste.

---

### Étape 5 — Exporter et importer des poses {#step-5--export-and-import-poses}

**Export** enregistre votre bibliothèque de poses dans un fichier `.bfpose` que vous pouvez conserver avec le projet ou partager. **Import** charge des poses depuis un fichier `.bfpose`.

**Ce que cela permet :** Une bibliothèque personnelle de poses à réutiliser dans plusieurs projets, à mélanger pour les clés d’animation ou à partager avec d’autres utilisateurs de BoneCraft.

---

## Guide 11 : Fusionner deux rigs {#guide-11-merge-two-rigs-together}

> **Durée :** Environ 25–40 minutes selon la complexité
> **Résultat :** Deux squelettes réunis en un seul, avec tous les poids conservés

**Avant de commencer — vérifiez ces points :**

- [ ] L’avatar de base et le second rig (de vêtements ou d’accessoires) sont dans le même fichier
- [ ] Les deux possèdent un rig et des poids

> Fusion de rigs = intégration d’un squelette dans un autre pour obtenir un seul squelette combiné. Utile lorsqu’un rig de corps et un rig de cheveux ou de tenue doivent n’en former qu’un.

---

### Étape 1 — Ouvrir Bone Merge {#step-1--open-bone-merge}

Ouvrez **BoneCraft → Setup Rigging → Bone Merge**. Ses trois étapes s’ouvrent dans l’ordre à mesure que vous les terminez.

Consultez les [commandes des étapes de Bone Merge](06-rig-builder.md#bone-merge).

---

### Étape 2 — Stage 1: Scope {#step-2--stage-1-scope}

1. Sélectionnez l’armature **Base**, le squelette du corps qui sera conservé.

2. Sélectionnez l’armature de vêtements ou de cheveux à intégrer.

3. Sélectionnez **Analyze**.

Lors de la fusion finale, l’armature entrante est fusionnée dans la base, puis masquée.

Analyze compare les deux squelettes et présente les catégories suivantes :

- ✓ Matched — os présents dans les deux squelettes et alignés
- \+ Source only — os du rig à fusionner sans correspondance dans la base
- − Target only — os de la base absents du rig à fusionner

Après avoir lu la liste, cliquez sur **Acknowledge Scope — Proceed to Rename**.

---

### Étape 3 — Stage 2: Rename {#step-3--stage-2-rename}

Pour chaque os présent uniquement dans la source, choisissez le cas applicable.

Si l’os possède un équivalent dans la base :

1. Saisissez le nom de cet os de la base.

2. Sélectionnez **Apply Rename**.

Si l’os n’a pas d’équivalent, sélectionnez plutôt **Mark as Unique**. Il rejoint la base sans changer de nom.

**Normalize Both Armatures** renomme, dans les deux rigs, les os standard reconnus, comme la colonne, les bras et les jambes. **Auto-Propose Renames** propose des noms aux autres os selon leur position. **Apply Batch Pattern** renomme plusieurs os à l’aide d’un même motif.

Lorsque chaque os présent uniquement dans la source a été traité, cliquez sur **Verify Rename — Proceed to Merge**.

---

### Étape 4 — Stage 3: Merge {#step-4--stage-3-merge}

Cliquez d’abord sur **Run Merge Preview** : cette commande indique ce que fera la fusion sans rien modifier.

Lorsque le rapport vous convient, cliquez sur **Merge Armatures**. BoneCraft sauvegarde les deux armatures, puis les combine.

**Ce que vous devriez voir :** Une seule armature contenant tous les os des deux squelettes, à laquelle chaque maillage est lié par ses poids.

**Ce que cela permet :** Un seul rig, plus facile à exporter et à modifier. Nécessaire pour tout avatar possédant des rigs distincts de vêtements ou d’accessoires.

---

## Guide 12 : Résoudre les problèmes de téléversement {#guide-12-fix-upload-problems}

> **Durée :** Environ 5–15 minutes selon le problème

**Avant de commencer :** Repérez votre problème dans la liste ci-dessous et consultez la section correspondante.

---

### « Échec du téléversement — os non reconnus » {#upload-failed--bones-not-recognized}

Vos os portent des noms que VRChat ne comprend pas. → [Guide 4 : Corriger les noms des os de votre avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

---

### « L’avatar reste en T-pose / ne suit pas mes mouvements dans VRChat » {#avatar-is-in-t-pose--not-moving-with-me-in-vrchat}

L’association humanoïde est absente ou incorrecte. → [Guide 5 : Associer votre avatar au système corporel de VRChat](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)

---

### « Le maillage se déforme bizarrement / la peau s’étire mal » {#mesh-is-deforming-weirdly--skin-stretching-wrong}

Les poids des os doivent être ajustés. → Consultez Weight Transfer et Weight Mirror dans [Outils de rig](05-rig-tools.md), ou exécutez **Smart Automatic Weights** dans l’onglet CATS.

---

### « Les cheveux traversent la tête » {#hair-is-clipping-through-the-head}

Les colliders des cheveux sont absents ou trop petits. → [Guide 6 : Ajouter une physique aux cheveux](02-guides-a.md#guide-6-add-hair-physics), étape 5.

---

### « L’avatar est classé Very Poor et masqué par les autres joueurs » {#avatar-is-very-poor-performance-and-being-blocked-by-other-players}

→ [Guide 9 : Améliorer les performances de votre avatar](#guide-9-improve-your-avatars-performance)

---

### « La synchronisation labiale ne fonctionne pas » {#lip-sync-not-working}

Les visèmes ne sont pas correctement associés. → [Guide 8 : Configurer la synchronisation labiale](#guide-8-set-up-lip-sync)

---

### « Le validateur du rig affiche des erreurs » {#rig-validator-shows-errors}

1. Ouvrez **BoneCraft → Review → Rig Validator**.

2. Sélectionnez **Run Validation**.

3. Suivez la suggestion du résultat ou consultez l’[index des corrections rapides](10-reference.md#quick-fix-index).

Chaque résultat indique le problème et l’os concerné. **Export Report** enregistre les résultats dans un fichier.

---

### « L’importation VRM ne fonctionne pas » {#vrm-import-not-working}

L’extension VRM n’est peut-être pas installée. → [Guide 2](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat), étape 1.

---

### « L’importation MMD ne fonctionne pas » {#mmd-import-not-working}

Vérifiez que **mmd_tools** est installé et activé. Le pont prend en charge les Extensions modernes et les paquets hérités. Consultez le message d’installation avant de réessayer. Voir le [guide 3](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat), étape 1.

---

## Guide 13 : Préparer votre avatar pour VRChat avec CATS {#guide-13-get-your-avatar-vrchat-ready-with-cats}

> **Durée :** Environ 20–35 minutes pour un passage complet du pipeline
> **Résultat :** Un avatar propre et optimisé, doté de synchronisation labiale, de suivi des yeux et de transformations correctes, prêt pour le téléversement dans VRChat

**Avant de commencer — lisez d’abord ceci :**

Les outils CATS suivent un pipeline recommandé. Pipeline Status marque les phases terminées : Fix Model, Material Atlas, Visemes, Eye Tracking, Pose To Shape et Apply Transforms. Operation Ledger consigne chaque opération CATS.

Les outils peuvent toujours être exécutés lorsqu’une phase précédente est incomplète. Ils affichent alors un avertissement tel que « Run Fix Model first for best results ».

Commencez par examiner les options de nettoyage de Fix Model. Enregistrez un point de sauvegarde du fichier avant de modifier l’avatar.

Avant de poursuivre, lisez [Le pipeline CATS](04-cats-pipeline.md).

**Avant de commencer — vérifiez ces points :**

- [ ] Votre avatar est importé et visible dans la vue 3D
- [ ] L’onglet CATS est ouvert dans la barre latérale droite (appuyez sur N si elle est masquée)
- [ ] Votre avatar est sélectionné (cliquez dessus dans la vue ou l’Outliner)

---

### Phase 1 — Fix Model {#phase-1--fix-model}

Fix Model est la phase de nettoyage recommandée. Examinez ses options pour votre avatar importé, puis inspectez le résultat avant de poursuivre.

**Ce que fait Fix Model** (chaque partie peut être désactivée dans ses options) :

- Applique les modificateurs
- Supprime les sommets en double et la géométrie isolée (triangles flottant à distance du corps)
- Recalcule les normales (les directions qui déterminent quel côté du maillage pointe vers l’extérieur)
- Supprime les groupes de sommets vides et les os sans poids
- Supprime les contraintes et les corps rigides que VRChat ne peut pas utiliser

**Étapes :**

1. Ouvrez **CATS → CATS → Fix Model**.

2. Sélectionnez le maillage de votre avatar.

3. Sélectionnez **Fix Model**.

4. Attendez la fin de l’opération.

5. Vérifiez que Pipeline Status marque Fix Model avec ✓.

Les maillages volumineux peuvent nécessiter quelques secondes.

**Ce que vous devriez voir :** Votre avatar a le même aspect, ou paraît légèrement plus propre. Fix Model est coché dans Pipeline Status et Operation Ledger indique l’exécution.

**Si votre modèle disparaît ou semble retourné après Fix Model :**

Le symptôme seul ne permet pas d’en identifier la cause.

1. Examinez les options de nettoyage activées, la visibilité des objets, la géométrie et les normales.

2. Si une restauration est nécessaire, utilisez Undo ou un point de sauvegarde pour rétablir l’état précédent.

3. Avant de réessayer, corrigez le problème identifié.

Consultez les [commandes Fix Model](09-cats.md#fix-model).

---

### Phase 2 — Génération des visèmes {#phase-2--viseme-generation}

À exécuter après : Fix Model ✓

La section Visemes crée les 15 formes de bouche de synchronisation labiale VRChat à partir de trois formes de base que vous possédez déjà. Si votre avatar possède déjà toutes les clés de forme de visèmes, vous pouvez ignorer cette phase, mais vérifiez-les dans VRChat Viseme Mapping (guide 8).

VRChat a besoin de 15 formes de bouche (visèmes) pour animer les lèvres de votre avatar lorsque vous parlez. La plupart des avatars n’ont que quelques formes de bouche de base. CATS les combine pour créer les autres.

Les trois formes de base :

- **A Shape** — bouche grande ouverte (forme « ahh »)
- **O Shape** — bouche arrondie (forme « ohh »)
- **CH Shape** — bouche entrouverte étroite laissant voir les dents (forme « ch » / « sh »)

**Si votre avatar n’a aucune clé de forme de bouche :** sculptez ou modifiez d’abord A, O et CH en tant que clés de forme. CATS les utilise pour générer les formes restantes. Consultez l’entrée Shape Key du glossaire.

**Étapes :**

1. Ouvrez **CATS → CATS → Visemes**.

2. Choisissez ci-dessous la sélection automatique ou manuelle des sources.

   Pour une sélection automatique, sélectionnez **Auto-Detect** afin de remplir les trois formes sources.

   Pour une sélection manuelle, sélectionnez la correspondance la plus proche pour chacune des trois formes sources.

   Exemples de noms de clés : `mouth_open`, `vrc.v_O` et `mouth_wide`.

3. Sélectionnez **Generate Visemes**.

4. Vérifiez que Pipeline Status affiche Visemes ✓.

CATS crée 15 clés de forme portant les noms VRChat, dont `vrc.v_aa`, `vrc.v_O` et `vrc.v_CH`.

**Ce que vous devriez voir :** 15 nouvelles clés de forme dans la liste Shape Keys du maillage (Properties → Object Data → Shape Keys).

Consultez les [commandes CATS Visemes](09-cats.md#visemes).

---

### Phase 3 — Suivi des yeux {#phase-3--eye-tracking}

À exécuter après : Fix Model ✓

Eye Tracking configure les os des yeux pour le suivi oculaire intégré à VRChat. Les yeux peuvent ensuite bouger et regarder les autres joueurs.

**Fonctionnement :**

- Trouve les os des yeux gauche et droit
- Leur attribue les noms requis par VRChat (`LeftEye` et `RightEye`)
- Ajoute les contraintes de rotation dont VRChat a besoin pour déplacer les yeux
- Limite la rotation des yeux à une amplitude naturelle (vers le haut, le bas et les côtés)

Auto-Detect recherche les noms courants des os des yeux. Cette fonction n’examine ni la géométrie du maillage ni la position des os.

Si vous renommez les os :

1. Relancez la détection.

2. Vérifiez les deux associations des os des yeux.

Si les mouvements des yeux sont incorrects, examinez l’orientation des os, les contraintes et l’avatar exporté.

**Étapes :**

1. Ouvrez **CATS → CATS → Eye Tracking**.

2. Sélectionnez **Auto-Detect** pour rechercher les noms courants des os des yeux gauche et droit.

3. Vérifiez les champs **Left Eye** et **Right Eye**.

4. Si une association est incorrecte, sélectionnez manuellement le bon os.

5. Si nécessaire, réglez **Up Limit**, **Down Limit** et **Side Limit**.

6. Sélectionnez **Create Eye Tracking**.

7. Vérifiez que Pipeline Status affiche Eye Tracking ✓.

**Ce que vous devriez voir :** Les deux os des yeux sont renommés, avec des contraintes de rotation dans le panneau Bone Constraints.

> **Si CATS ne trouve pas les os des yeux :** votre squelette n’en possède peut-être pas. Certains formats (notamment les anciens modèles MMD) utilisent des clés de forme plutôt que des os pour cligner des yeux. Ignorez cette phase : VRChat utilise l’animation des yeux par clés de forme en l’absence d’os des yeux.

---

### Phase 4 — Pose vers clé de forme {#phase-4--pose-to-shape-key}

À exécuter après : Fix Model ✓

Le bouton actuel **Pose to Shape Key** capture le mélange actuel de clés de forme du maillage sélectionné. Il ne cuit pas la déformation provenant des os de l’armature. Pour une pose déformée par les os, utilisez la [procédure native Save as Shape Key vérifiée](09-cats.md#save-a-bone-deformed-pose).

**Étapes :**

1. Passez en Object Mode.

2. Sélectionnez le maillage cible.

3. Réglez ses valeurs de clés de forme existantes sur le mélange à capturer.

4. Gardez le maillage actif.

5. Ouvrez **CATS → CATS → Pose & Shape Keys**.

6. Sélectionnez **Pose to Shape Key**.

7. Saisissez le nom de la nouvelle clé de forme.

8. Confirmez l’opération.

9. Remettez les valeurs des clés de forme d’origine à 0.

10. Examinez la nouvelle clé seule.

11. Vérifiez que Pipeline Status affiche Pose To Shape ✓.

L’outil règle déjà la nouvelle clé sur 1.

**Ce que vous devriez voir :** Une nouvelle clé de forme reproduisant le mélange capturé. Laisser les clés d’origine actives ajoute à nouveau leur déformation.

> **Shape Key to Basis :** fait de la clé de forme active, autre que Basis, la nouvelle Basis. Cette commande ajuste les autres clés par rapport à cette Basis. Avant cette opération, enregistrez un point de sauvegarde. Ensuite, vérifiez les clés restantes.

Consultez les [commandes Pose to Shape Key](09-cats.md#pose-to-shape-key).

---

### Phase 5 — Appliquer les transformations {#phase-5--apply-transforms}

À exécuter après : toutes les phases précédentes dont vous avez besoin

Apply Transforms est la phase finale de préparation recommandée. Cette commande applique la position, la rotation et l’échelle au maillage et au squelette. Les canaux reviennent respectivement à 0, 0 et 1.

Enregistrez un point de sauvegarde avant cette opération. Comparez l’avatar avant et après. Les outils précédents restent disponibles.

Si l’avatar exporté n’a pas la bonne taille, examinez les transformations du maillage et de l’armature, ainsi que les réglages d’échelle à l’exportation et à l’importation. Utilisez Undo ou un point de sauvegarde pour restaurer un état précédent si nécessaire.

**Les outils de Transforms & FBT :**

- **Apply All Transforms** — applique ensemble la position, la rotation et l’échelle au maillage et à l’armature
- **Fix FBT** — une correction des transformations pour les configurations Full Body Tracking (déplace l’os racine au niveau du sol)
- **Remove FBT** — retire cette correction

Material Atlas et Pose To Shape sont facultatifs. Si vous avez associé des visèmes existants, Visemes reste décoché.

**Étapes :**

1. Dans Pipeline Status, vérifiez que les phases nécessaires à votre avatar sont cochées.

2. Ouvrez **CATS → CATS → Transforms & FBT**.

3. Sélectionnez **Apply All Transforms**.

4. Vérifiez que Pipeline Status affiche Apply Transforms ✓.

5. Exportez par **CATS → Import / Export → Game Engine Export → Unity / VRChat** (guide 1, étape 9).

**Ce que vous devriez voir :** Apply Transforms est coché, après les phases dont vous aviez besoin. Vérifiez l’avatar exporté dans VRChat Creator Companion.

Consultez les [commandes de transformation et de FBT](09-cats.md#apply-all-transforms).

---

**Ce que cela permet :** Un avatar préparé aux vérifications d’exportation, avec le nettoyage, les formes de bouche, le suivi des yeux et les expressions que vous avez choisis. Validez-le dans l’application cible avant le téléversement.

Suite : [Le pipeline CATS](04-cats-pipeline.md)
