# Guides 1–7 {#guides-17}

[← Sommaire](index.md)

## Guide 1 : importer votre premier avatar dans VRChat {#guide-1-get-your-first-avatar-into-vrchat}

Pour un maillage d’exercice, suivez l’[atelier écrit du mannequin](06-rig-builder.md#illustrated-mannequin-workshop). Ses étapes sont Simple Human, mannequin sans rig, Auto-Rig et IK/FK.

> **Durée :** environ 45–60 minutes pour un premier parcours complet
> **Résultat :** avatar riggé, prêt pour VRChat et exporté pour le SDK VRChat

**Avant de commencer, vérifiez ces points :**

- [ ] Votre modèle 3D est importé dans Bforartists (File > Import, choisissez son format)
- [ ] Le modèle est en pose en T (bras sur les côtés, corps droit), ou proche de cette pose
- [ ] Il n’a pas de géométrie manifestement cassée, comme des triangles flottants aléatoires
- [ ] Vous le voyez dans la vue 3D comme une forme grise pleine

---

### Étape 1 — Ouvrir Rig Builder {#step-1--open-the-rig-builder}

1. Dans la vue 3D, appuyez sur **T** pour afficher l’étagère d’outils gauche.

2. Ouvrez **Rig Builder**.

Rig Builder apparaît aussi dans **Properties → Scene** si Preferences → Tabs → Scene Properties → Show est activé. Il comprend **Auto-Rig Wizard**, Quick Rig (armatures prédéfinies) et **Mannequin**.

3. Dépliez **Auto-Rig Wizard**.

4. Sélectionnez **Start Auto-Rig**.

Vous pouvez aussi lancer l’assistant depuis Add → Armature → Auto-Rig Wizard dans la vue 3D, puis continuer dans Rig Builder.

Description de l’image source anglaise (image omise) : Auto-Rig Wizard dans l’onglet Rig Builder.

*Capture historique d’atelier. Auto-Rig Wizard dans l’onglet Rig Builder.*

---

### Étape 2 — Sélectionner votre maillage {#step-2--select-your-mesh}

L’assistant énumère les maillages de la scène.

1. Sélectionnez le maillage de l’avatar dans la liste.

2. Sélectionnez **Next**.

**Ce que vous devez voir :** une ligne « Selected: » avec le nom du maillage, puis l’étape du type de rig.

Description de l’image source anglaise (image omise) : choisir le maillage d’entrée d’Auto-Rig Wizard.

*Capture historique d’atelier. Choisir le maillage d’entrée d’Auto-Rig Wizard.*

---

### Étape 3 — Choisir le type de rig {#step-3--choose-the-rig-type}

1. Pour clignements, expressions et synchronisation labiale, sélectionnez **Body + Face**.

2. Pour un corps sans contrôles faciaux, sélectionnez plutôt **Body Only**.

3. Dans Generation Options, réglez **Kinematics** sur IK/FK, IK only ou FK only.

4. Sélectionnez **Next**.

Description de l’image source anglaise (image omise) : choisir le type de rig du corps et les méthodes IK/FK.

*Capture historique d’atelier. Choisir le type de rig du corps et les méthodes IK/FK.*

---

### Étape 4 — Placer les repères du corps {#step-4--place-body-markers}

Les repères identifient bassin, colonne, cou, tête, épaules, bras, mains, jambes et pieds. BoneCraft utilise leurs positions pour construire les os. Vérifiez chaque repère avec soin.

**Smart Detection :**

1. Sélectionnez **Detect Markers**.

2. Sélectionnez **Accept High** pour conserver les repères à forte confiance.

3. Sélectionnez **Reset Low** pour effacer ceux à faible confiance et les placer manuellement.

BoneCraft suit les membres du maillage et attribue une confiance à chaque repère. **Guess Markers from Mesh** estime plutôt les positions à partir des proportions du maillage.

**Avec l’outil de la vue :**

1. En Object Mode, activez Place Rig Markers dans la barre d’outils de la vue.

2. Cliquez sur le maillage pour placer et confirmer le repère nommé dans l’en-tête.

3. Répétez pour le prochain repère non confirmé.

4. Une fois l’étape de repères terminée, sélectionnez **Next** dans l’assistant.

L’en-tête contient aussi des verrouillages d’axes et un commutateur de miroir.

**Un repère à la fois :** chaque repère possède une ligne d’icônes. Survolez un bouton pour lire son infobulle.

1. Sélectionnez **Place Marker**, la flèche de la ligne du repère.

2. Cliquez sur l’emplacement souhaité sur l’avatar.

3. Quand la position est correcte, sélectionnez **Confirm Marker**, la coche.

**Reset Marker**, la flèche circulaire, efface un repère placé pour permettre un nouveau placement.

**Symétrie :** **Toggle Symmetry** place le repère opposé chaque fois que vous en placez un. C’est la première icône de chaque ligne de repère gauche ou droit. **Mirror L to R** et **Mirror R to L** copient chaque repère confirmé sur le côté opposé.

1. Quand tous les repères sont placés, sélectionnez **Confirm All Placed**.

2. Sélectionnez **Next**.

Description de l’image source anglaise (image omise) : examiner les repères du corps détectés avant de les ajuster.

*Capture historique d’atelier. Examiner les repères du corps détectés avant de les ajuster.*

---

### Étape 5 — Placer les repères des doigts {#step-5--place-finger-markers}

1. Dans Finger Detail, choisissez le nombre de doigts, de « 0 — No Fingers » à « 5 — Full Human Hand ».

2. Sélectionnez **Guess Finger Markers**.

3. Ajustez les positions incorrectes.

4. Sélectionnez **Next**.

BoneCraft suit chaque doigt de l’articulation à la pointe d’après la forme de la main. Une main standard utilise « 5 — Full Human Hand ».

---

### Étape 6 — Placer les repères du visage (Body + Face uniquement) {#step-6--place-face-markers-body--face-only}

1. Sélectionnez **Guess Face Markers**.

2. Ajustez yeux, paupières, sourcils, coins de bouche et mâchoire si nécessaire.

3. Sélectionnez **Next**.

Les repères des yeux conservent leurs positions attribuées manuellement.

---

### Étape 7 — Vérifier et générer {#step-7--review-and-generate}

L’étape Review énumère les avertissements et options de génération. Cliquez sur **Generate Rig**.

**Ce que vous devez voir :** des os orange dans l’avatar, dont les membres IK/FK et les doigts. Un rig Body + Face contient aussi un rig facial. La peau attachée se déforme quand les os bougent.

La dernière étape propose **Build Control Rig** et **Close Wizard**. Build Control Rig applique les options de Review que Generate Rig n’applique pas. [Rig Builder](06-rig-builder.md) décrit les deux commandes.

> Les **poids de déformation** définissent quels os déplacent chaque partie du maillage. BoneCraft les définit automatiquement. Pour les affiner, utilisez Weight Tools dans [Outils de rig](05-rig-tools.md).

Description de l’image source anglaise (image omise) : examiner les réglages du rig avant génération.

*Capture historique d’atelier. Examiner les réglages du rig avant génération.*

---

### Étape 8 — Associer les os humanoïdes de VRChat {#step-8--map-to-vrchats-humanoid-bones}

1. Appuyez sur **N** pour afficher la barre latérale droite.

2. Ouvrez **CATS → Avatar Tools → Set Up Humanoid Bones**.

3. Sélectionnez **Auto-Map All**.

4. Sélectionnez **Normalize Names**.

5. Sélectionnez **Validate**.

Auto-Map All relie les os aux emplacements corporels de VRChat. Normalize Names donne aux os associés les noms attendus par VRChat.

**Ce que vous devez voir :** chaque emplacement requis (Hips, Spine, Head, LeftUpperArm, etc.) contient un os. Le guide 5 explique les emplacements.

Consultez les [commandes de mappage humanoïde](08-vrchat.md#set-up-humanoid-bones).

---

### Étape 9 — Exporter pour VRChat {#step-9--export-for-vrchat}

Consultez les [réglages d’exportation Unity / VRChat](08-vrchat.md#export-to-vrchat).

1. Sélectionnez l’armature de l’avatar.
2. Ouvrez **CATS → Import / Export → Game Engine Export → Unity / VRChat**.
3. Réglez **Folder**.
4. Réglez **Avatar** sur le nom d’exportation.
5. Choisissez **Bone Names**.
6. Examinez l’aperçu des noms si vous utilisez un préréglage.
7. Cliquez sur **Export to VRChat (Unity)**.

**Keep Original Names** est le choix par défaut. **Unity-Preset** et **Unreal-Preset** renomment les os reconnus sur les copies d’exportation. Le rig de travail garde ses noms.

Les boutons principaux d’exportation Unity et Unreal acceptent les modes Object Mode, Pose Mode et Edit Mode. Ils restaurent le mode et la sélection précédents.

Consultez les [noms et limites d’exportation](08-vrchat.md#export-bone-naming) pour les conflits, le mappage et les restrictions d’animation.

**Ce que vous devez voir :** l’avatar exporté dans le dossier choisi, prêt pour VRChat Creator Companion et le SDK VRChat dans Unity.

---

**Ce que cela permet :** un avatar VRChat riggé. Vous pouvez ensuite ajouter la physique des cheveux (guide 6), les vêtements (guide 7), la synchronisation labiale (guide 8) et vérifier les performances (guide 9). Pour le nettoyage CATS et la configuration VRChat, consultez le [guide 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats).

---

## Guide 2 : importer un avatar VRoid dans VRChat {#guide-2-bring-a-vroid-avatar-into-vrchat}

> **Durée :** environ 15–25 minutes
> **Résultat :** avatar VRoid prêt à être exporté pour VRChat

**Avant de commencer, vérifiez ces points :**

- [ ] Vous avez exporté l’avatar de VRoid Studio en fichier `.vrm` ou l’avez téléchargé depuis VRoid Hub en `.zip`
- [ ] BoneCraft est installé et activé

---

### Étape 1 — Installer le complément VRM {#step-1--install-the-vrm-add-on}

BoneCraft nécessite le complément VRM pour lire les fichiers `.vrm`.

1. Ouvrez **CATS → Import / Export → VRM / VRoid**.

2. Installez la dépendance avant l’importation.

3. Activez la dépendance.

La passerelle inactive propose **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** et **Show Manual Instructions**.

Pour un paquet hors ligne :

1. Ouvrez les préférences natives.

2. Pour un ancien ZIP de complément, utilisez **Add-ons → Install from Disk…**.

3. Pour un paquet d’extension moderne, utilisez plutôt le menu natif d’installation des Extensions.

4. Revenez à la passerelle.

5. Vérifiez qu’elle indique **Active**.

Consultez les [commandes d’installation des passerelles de format](08-vrchat.md#vrm-bridge).

---

### Étape 2 — Importer votre avatar {#step-2--import-your-avatar}

1. Dans **VRM / VRoid**, sélectionnez **Import VRM…**.

2. Sélectionnez votre fichier `.vrm`.

Pour un téléchargement VRoid :

1. Sélectionnez plutôt **Import VRoid (.vroid / .zip)…**.

2. Sélectionnez le fichier `.zip` téléchargé.

Si vous sélectionnez un projet VRoid Studio (`.vroid`), BoneCraft affiche une carte « VRoid Studio Project ». Un projet n’est pas encore un avatar.

Pour ce fichier de projet :

1. Exportez le projet en VRM dans VRoid Studio.

2. Importez ce fichier VRM.

**Ce que vous devez voir :** le personnage VRoid dans la vue avec son squelette en place.

---

### Étape 3 — Associer les os humanoïdes de VRChat {#step-3--map-to-vrchats-humanoid-bones}

1. Ouvrez **CATS → Avatar Tools → Set Up Humanoid Bones**.

2. Sélectionnez **Auto-Map All**.

Les squelettes VRoid suivent une disposition standard ; cela remplit généralement tous les emplacements. Si l’un est incorrect, sélectionnez **Fix Humanoid Map** dans Lint, sous **VRM / VRoid**. Cela corrige les erreurs courantes de mappage des noms VRoid.

---

### Étape 4 — Corriger les noms d’os {#step-4--fix-bone-names}

Dans **Set Up Humanoid Bones**, sélectionnez **Normalize Names**. Les noms VRoid des os associés sont remplacés par ceux attendus par VRChat.

---

### Étape 5 — Configurer les visèmes (synchronisation labiale) {#step-5--set-up-visemes-lip-sync}

Les avatars VRoid ont déjà les formes de bouche nécessaires. Dans **VRM / VRoid**, cliquez sur **Map VRoid Visemes**. BoneCraft associe les clés de forme VRoid aux formes de synchronisation labiale VRChat.

---

### Étape 6 — Physique des cheveux (facultative) {#step-6--hair-physics-optional}

Les cheveux des avatars VRoid utilisent des SpringBones. **Convert SpringBones → PhysBones** dans **VRM / VRoid** les convertit en PhysBones VRChat. Le guide 6 détaille la physique des cheveux.

---

### Étape 7 — Exporter {#step-7--export}

Exportez comme dans le guide 1, étape 9.

**Ce que cela permet :** l’avatar VRoid est prêt pour VRChat Creator Companion. Vous pouvez aussi vérifier les performances (guide 9) avant l’envoi.

---

## Guide 3 : importer un avatar MMD dans VRChat {#guide-3-bring-an-mmd-avatar-into-vrchat}

> **Durée :** environ 20–30 minutes
> **Résultat :** modèle MMD `.pmx` prêt pour VRChat

**Avant de commencer, vérifiez ces points :**

- [ ] Vous possédez un modèle MMD `.pmx` ou `.pmd`
- [ ] BoneCraft est installé

---

### Étape 1 — Installer mmd_tools {#step-1--install-mmd_tools}

BoneCraft nécessite **mmd_tools** pour lire les fichiers MMD. Il reconnaît les anciens compléments et les Extensions Blender modernes.

1. Ouvrez **CATS → Import / Export → MMD / PMX**.
2. Cliquez sur **Auto-Install Latest from GitHub** lorsque la passerelle indique une dépendance manquante.
3. Utilisez **Open Add-on Preferences** pour activer une copie installée mais désactivée.
4. Vérifiez que la passerelle indique **Active** avant l’importation.

Pour une installation manuelle :

1. Dans la carte inactive de la passerelle, sélectionnez **Website** ou **Show Manual Instructions**.

2. Installez l’extension MMD officielle via **Preferences → Get Extensions**.

Pour un ZIP hors ligne :

1. Pour un paquet d’extension moderne, utilisez le menu d’installation des extensions.

2. Pour un ancien paquet de complément, utilisez plutôt **Add-ons → Install from Disk…**.

Le contenu autonome de la passerelle propose aussi **Install from .zip on Disk...** lorsqu’il est affiché.

Si l’installation signale l’absence de dépôt local d’extensions :

1. Ouvrez **Preferences → Get Extensions → Repositories**.

2. Ajoutez ou activez un dépôt local.

3. Réessayez l’installation.

Utilisez le paquet officiel du projet amont. Une erreur d’installation ou une importation annulée ne constitue pas une importation réussie.

Consultez les [commandes d’installation des passerelles de format](08-vrchat.md#vrm-bridge).

---

### Étape 2 — Importer votre fichier PMX {#step-2--import-your-pmx-file}

1. Dans **MMD / PMX**, sélectionnez **Import PMX / PMD...**.

2. Sélectionnez votre modèle.

**Ce que vous devez voir :** le personnage MMD dans la vue, avec des noms d’os japonais.

---

### Étape 3 — Corriger les noms d’os {#step-3--fix-bone-names}

Associez les os MMD aux emplacements humanoïdes Unity avant l’exportation VRChat.

1. Dans **MMD / PMX**, sélectionnez **Convert Bone Names -> Unity**.

Pour les noms dans une autre langue :

1. Ouvrez **CATS → CATS → Translate Bone Names**.

2. Sélectionnez la **Language** source.

3. Sélectionnez **Translate Bone Names**.

---

### Étape 4 — Nettoyer le modèle {#step-4--clean-up-the-model}

Les modèles MMD contiennent souvent de la géométrie supplémentaire et des pièces distinctes.

1. Ouvrez **CATS → CATS**.

2. Examinez les options **Fix Model**.

3. Sélectionnez les opérations de nettoyage nécessaires à l’avatar.

4. Lancez **Fix Model**.

5. Sélectionnez **Join Meshes** pour combiner les parties du corps en un maillage, comme recommandé pour VRChat.

Le [guide 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats) explique le pipeline CATS complet.

---

### Étape 5 — Associer les os humanoïdes de VRChat {#step-5--map-to-vrchats-humanoid-bones}

1. Ouvrez **CATS → Avatar Tools → Set Up Humanoid Bones**.

2. Sélectionnez **Auto-Map All**.

3. Pour un emplacement vide, sélectionnez son bouton.

4. Sélectionnez l’os correspondant.

Les squelettes MMD ressemblent aux squelettes VRChat ; la plupart des emplacements sont donc remplis automatiquement.

---

### Étape 6 — Physique et exportation {#step-6--physics-and-export}

**Convert Physics -> PhysBones** dans **MMD / PMX** convertit la physique des corps rigides des cheveux et jupes MMD en PhysBones VRChat. Exportez ensuite comme dans le guide 1, étape 9.

**Ce que cela permet :** l’avatar MMD est prêt pour VRChat. Vous pouvez ajouter la physique des cheveux (guide 6) et la synchronisation labiale (guide 8) avant l’envoi.

---

## Guide 4 : corriger les noms d’os de votre avatar {#guide-4-fix-your-avatars-bone-names}

> **Durée :** environ 5–15 minutes
> **Résultat :** les os nécessaires à VRChat portent des noms compatibles

**Avant de commencer, vérifiez ce point :**

- [ ] L’avatar est ouvert avec son squelette (armature) visible

---

### Étape 1 — Détecter la convention de noms actuelle {#step-1--detect-the-current-naming-style}

Consultez les [commandes Naming](08-vrchat.md#vrchat-naming-extras).

1. Ouvrez **CATS → VRChat Tools**.

2. Dans Naming, sélectionnez **Detect**.

3. Après modification des noms, sélectionnez **Force Rescan** pour vérifier de nouveau.

BoneCraft indique la convention détectée, par exemple Mixamo, VRoid ou Unity, et un score.

Pour des noms d’os japonais, chinois, coréens, portugais, espagnols ou français :

1. Ouvrez **CATS → CATS → Translate Bone Names**.

2. Sélectionnez la **Language** source.

3. Sélectionnez **Translate Bone Names**.

Les noms reconnus sont convertis en anglais.

---

### Étape 2 — Renommer selon les noms VRChat {#step-2--rename-to-vrchat-names}

Pour un renommage limité à l’exportation, gardez les noms de travail et choisissez plutôt **Unity-Preset** dans la section d’exportation. Consultez [Noms des os à l’exportation](08-vrchat.md#export-bone-naming).

1. Associez les os comme dans le guide 5, étape 2.

2. Dans **Set Up Humanoid Bones**, sélectionnez **Normalize Names**.

Chaque os associé reçoit le nom attendu par VRChat.

**Ce que vous devez voir :** des noms tels que `Hips`, `Spine`, `Chest` et `LeftUpperArm`.

---

### Étape 3 — Corrections manuelles si nécessaire {#step-3--manual-fixes-if-needed}

Le groupe Naming de **VRChat Tools** possède aussi des outils par lots pour les os restants :

- **Find and Replace** remplace un texte par un autre dans chaque nom d’os
- **Add Prefix** et **Add Suffix** ajoutent du texte au début ou à la fin de chaque nom
- **Remove Prefix** et **Remove Suffix** retirent ce texte
- **Regex Replace** fait de même avec une expression régulière

**Ce que cela permet :** des noms corrects permettent le mappage humanoïde automatique (guide 5). Sans eux, VRChat ne peut pas déterminer comment votre personnage doit bouger.

---

## Guide 5 : associer l’avatar au système corporel de VRChat {#guide-5-map-your-avatar-to-vrchats-body-system}

> **Durée :** environ 10–15 minutes
> **Résultat :** squelette relié au système de mouvement humanoïde de VRChat

**Avant de commencer, vérifiez ces points :**

- [ ] Les os sont nommés de manière cohérente (sinon, voir le guide 4)
- [ ] Le squelette est sélectionné
- [ ] Vous êtes en **Object Mode** (menu en haut à gauche de la vue)

---

### Étape 1 — Ouvrir Set Up Humanoid Bones {#step-1--open-set-up-humanoid-bones}

Dans l’onglet **CATS**, dépliez **Avatar Tools → Set Up Humanoid Bones**.

---

### Étape 2 — Associer automatiquement {#step-2--auto-map}

Cliquez sur **Auto-Map All**. BoneCraft analyse le squelette et remplit les emplacements corporels.

> Un emplacement humanoïde identifie une partie du corps, par exemple Hips, Head ou Left Hand. BoneCraft leur affecte des os. Les mappages humanoïdes enregistrés se chargent correctement à la réouverture du fichier.

**Ce que vous devez voir :** les affectations d’os et la proportion d’emplacements requis remplis. Il y a 15 emplacements requis : Hips, Spine, Head, les deux bras, avant-bras, mains, cuisses, jambes et pieds. Chest, UpperChest et Neck sont facultatifs.

---

### Étape 3 — Vérifier le mappage {#step-3--check-the-mapping}

Cliquez sur **Validate**. BoneCraft vérifie que chaque emplacement requis a un os et que la hiérarchie est cohérente.

---

### Étape 4 — Remplir les emplacements vides manuellement {#step-4--fill-empty-slots-by-hand}

Un emplacement vide affiche « (click to map) ».

1. Sélectionnez l’emplacement vide.

2. Sélectionnez le bon os.

3. Sélectionnez de nouveau **Validate**.

4. Sélectionnez **Normalize Names** pour donner les noms VRChat aux os associés.

---

### Étape 5 — Configurer le suivi des yeux (facultatif) {#step-5--set-up-eye-tracking-optional}

Si l’avatar possède des os des yeux :

1. Ouvrez **CATS → CATS → Eye Tracking**.

2. Sélectionnez **Auto-Detect** pour rechercher les noms d’os des yeux.

3. Vérifiez les affectations **Left Eye** et **Right Eye**.

4. Si nécessaire, sélectionnez les bons os manuellement.

5. Réglez les limites de rotation.

6. Sélectionnez **Create Eye Tracking**.

Le [guide 13, phase 3](03-guides-b.md#phase-3--eye-tracking) explique les réglages.

**Ce que cela permet :** le mappage humanoïde permet à l’avatar de suivre vos mouvements dans VRChat. L’IK (cinématique inverse) fait suivre vos contrôleurs aux mains dans le jeu.

---

## Guide 6 : ajouter la physique des cheveux {#guide-6-add-hair-physics}

> **Durée :** environ 15–25 minutes
> **Résultat :** les cheveux et autres parties souples de l’avatar oscillent naturellement dans VRChat

**Avant de commencer, vérifiez ces points :**

- [ ] L’avatar est ouvert avec son squelette sélectionné
- [ ] Set Up Humanoid Bones est terminé (guide 5)

> PhysBone est le composant VRChat qui fait rebondir et osciller les os comme s’ils avaient un poids. BoneCraft le configure sur des chaînes d’os de cheveux, oreilles, queues, jupes et accessoires.

---

### Étape 1 — Ouvrir Add Hair Physics {#step-1--open-add-hair-physics}

Dans l’onglet **CATS**, dépliez **Avatar Tools → Add Hair Physics**. Il comprend Hair Chain Detection, Hair Chain Generation, PhysBone Configuration et Hair Physics Colliders.

---

### Étape 2 — Trouver les chaînes de cheveux {#step-2--find-the-hair-chains}

Si les cheveux ont déjà des os, sélectionnez **Detect Hair Physics Chains**. BoneCraft recherche des chaînes semblables à des cheveux, reliées bout à bout depuis une racine. La liste montre l’os racine et la longueur de chacune.

Si les cheveux n’ont pas d’os :

1. Sélectionnez les maillages des cheveux.

2. Dans Hair Chain Generation, sélectionnez **Generate**.

3. Réglez immédiatement **Chain Density** sur Low, Medium ou High dans **Adjust Last Operation**.

**Replace** demande confirmation et crée actuellement de nouvelles chaînes sans supprimer les anciennes.

Avant de générer de nouveau :

1. Examinez la liste des os.

2. Si des chaînes indésirables existent, supprimez-les.

---

### Étape 3 — Choisir un préréglage PhysBone {#step-3--choose-a-physbone-preset}

1. Sélectionnez un os de la chaîne.

2. Dans PhysBone Configuration, sélectionnez **Hair**, **Skirt** ou **Tail**.

Skirt convient aux jupes et capes. Tail convient aux queues et cordes.

**Ce que vous devez voir :** les paramètres de la chaîne : Pull, Spring, Stiffness, Gravity et Max Angle.

---

### Étape 4 — Affiner si nécessaire {#step-4--fine-tune-optional}

Le panneau affiche les valeurs de la chaîne sans permettre de les modifier. Augmenter Stiffness réduit la flexion. Augmenter Gravity tire la chaîne vers le bas. Réduire Max Angle limite son oscillation. Pour changer les valeurs, sélectionnez un autre préréglage. Vous pouvez aussi modifier le composant PhysBone dans Unity après importation de l’avatar.

---

### Étape 5 — Ajouter des colliders (recommandé) {#step-5--add-colliders-recommended}

Les colliders sont des formes invisibles empêchant les cheveux de traverser la tête et le corps. Dans Hair Physics Colliders, sélectionnez **Place Default Colliders** pour en ajouter à la tête, aux épaules et à la poitrine. **Add Collider** et **Remove Collider** ajoutent ou retirent un collider à la fois.

**Ce que cela permet :** les cheveux bougent naturellement dans VRChat quand vous tournez la tête, sautez ou dansez. Les mêmes étapes conviennent aux queues, oreilles, jupes et accessoires suspendus.

---

## Guide 7 : attacher des vêtements qui suivent le corps {#guide-7-attach-clothing-that-moves-with-your-body}

> **Durée :** environ 20–30 minutes
> **Résultat :** vêtement attaché au squelette de l’avatar et suivant le corps

**Avant de commencer, vérifiez ces points :**

- [ ] L’avatar de base possède un squelette terminé et le corps est pondéré
- [ ] Le vêtement est dans le même fichier, avec sa propre armature s’il en avait une
- [ ] Le vêtement s’ajuste à peu près autour du corps

---

### Étape 1 — Ouvrir Attach Clothing {#step-1--open-attach-clothing}

Consultez les [commandes Clothing et l’ordre de sélection](08-vrchat.md#attach-clothing).

Dans l’onglet **CATS**, dépliez **VRChat Tools** et trouvez le groupe Clothing. Il comprend Bone Matching, Collision Detection et Clothing Merge.

---

### Étape 2 — Faire correspondre les os {#step-2--match-bones}

Si le vêtement possède une armature :

1. Passez en Object Mode.

2. Sélectionnez les armatures du vêtement et de l’avatar.

3. Sélectionnez **Match Bones** pour comparer leurs noms d’os.

**Ce que vous devez voir :** les nombres de correspondances HIGH, MEDIUM, LOW et UNMATCHED. Le panneau ne montre pas de liste de paires d’os. Pour un vêtement sans armature, sautez cette étape.

Avant de fusionner deux armatures :

1. Sélectionnez **Detect Collisions** pour vérifier les conflits de noms d’os.

2. Examinez les renommages proposés.

3. Rendez active l’armature du vêtement.

4. Sélectionnez **Resolve Collisions** pour y appliquer les renommages.

Detect Collisions vérifie uniquement les noms, pas les intersections de maillage.

---

### Étape 3 — Fusionner le vêtement {#step-3--merge-the-clothing}

1. Si le vêtement possède une armature, sélectionnez-la avec ses maillages.

2. Sinon, sélectionnez uniquement ses maillages.

3. Cliquez avec Shift sur l’armature de l’avatar en dernier pour la rendre active.

4. Sélectionnez **Merge Clothing**.

Avec une armature de vêtement, BoneCraft déplace le vêtement sur le squelette de l’avatar et fusionne les os. Sans armature de vêtement, il transfère les poids du corps aux maillages du vêtement.

> Les poids (peinture de poids) sont des nombres indiquant à chaque point du maillage dans quelle mesure chaque os le déplace. Si la manche gauche a du poids sur l’os du bras gauche, déplacer cet os entraîne la manche.

**Ce que vous devez voir :** le vêtement sous le squelette de l’avatar. Déplacer un os déplace le corps et le vêtement.

---

### Étape 4 — Vérifier les intersections {#step-4--check-for-clipping}

1. Posez l’avatar.

2. Examinez les endroits où le vêtement traverse le corps.

3. Si cela arrive, ajustez la forme du vêtement ou ses poids à ces endroits.

Consultez Weight Tools dans [Outils de rig](05-rig-tools.md). **Detect Collisions** ne vérifie pas les intersections physiques.

**Ce que cela permet :** des vêtements qui suivent naturellement le corps. Répétez pour chaque pièce de tenue.

Suivant : [Guides 8–13](03-guides-b.md)
