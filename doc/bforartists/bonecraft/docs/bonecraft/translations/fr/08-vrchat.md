# Outils VRChat {#vrchat-tools}

[← Sommaire](index.md)

## Outils VRChat {#vrchat-tools-1}

Les outils VRChat se trouvent dans la section **Avatar Tools** de l’onglet **CATS**, dans la barre latérale droite. Appuyez sur **N** pour l’afficher. Avatar Tools couvre les os humanoïdes, la physique des cheveux et Viseme Library / Lip Sync. L’exportation VRChat se trouve dans CATS → Import / Export → Unity / VRChat. La section distincte **VRChat Tools** située dessous regroupe Check Performance, Attach Clothing, Facial et VRChat Naming Extras. Quand Preferences → Tabs → Scene Properties → Show est activé, elle apparaît aussi dans l’onglet **Scene** de l’éditeur **Properties**. Ce commutateur ne masque pas l’onglet CATS de la vue.

---

### Set Up Humanoid Bones {#set-up-humanoid-bones}

Associe les os du squelette aux emplacements humanoïdes de VRChat et vérifie le mappage.

Consultez le [guide 5 : associer l’avatar au système corporel de VRChat](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system).

Description de l’image source anglaise (image omise) : emplacements humanoïdes requis avant Auto-Map All. Après mappage, examiner chaque emplacement et combler les manques.

*Panneau contextuel natif, BoneCraft 9.2.18. Emplacements humanoïdes requis avant Auto-Map All. Après mappage, examiner chaque emplacement et combler les manques.*

---

### Add Hair Physics {#add-hair-physics}

Configure des chaînes PhysBone sur cheveux, oreilles, queues et accessoires, avec des colliders.

Consultez le [guide 6 : ajouter la physique des cheveux](02-guides-a.md#guide-6-add-hair-physics).

Description de l’image source anglaise (image omise) : chaînes Hair Physics, actions de génération, préréglages et commandes de colliders. Examiner les chaînes détectées avant d’appliquer la physique.

*Panneau contextuel natif de compilation de test, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Chaînes Hair Physics, actions de génération, préréglages et commandes de colliders. Examiner les chaînes détectées avant d’appliquer la physique.*

---

### Attach Clothing {#attach-clothing}

**Emplacement :** onglet CATS → VRChat Tools → Clothing

Fusionne les vêtements avec le squelette de l’avatar et transfère leurs poids.

Consultez le [guide 7 : attacher des vêtements qui suivent le corps](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body).

Description de l’image source anglaise (image omise) : commandes Clothing et ordre de sélection Pre-Merge. Avant la fusion, faire correspondre les os et vérifier les conflits de noms.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Commandes Clothing et ordre de sélection Pre-Merge. Avant la fusion, faire correspondre les os et vérifier les conflits de noms.*

---

### VRChat Naming Extras {#vrchat-naming-extras}

**Emplacement :** onglet CATS → VRChat Tools → Naming

**Fonction :** détecte le style de noms du squelette et renomme les os par lots.

Consultez le [guide 4 : corriger les noms d’os de votre avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names).

**Outils par lots :** **Find and Replace**, **Add Prefix**, **Remove Prefix**, **Add Suffix**, **Remove Suffix** et **Regex Replace**

Description de l’image source anglaise (image omise) : Naming détecte Unity Humanoid avec une confiance de 16/24 dans cet exemple. Examiner les noms avant les actions par lots.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Naming détecte Unity Humanoid avec une confiance de 16/24 dans cet exemple. Examiner les noms avant les actions par lots.*

---

### VRChat Viseme Mapping {#vrchat-viseme-mapping}

**Emplacement :** CATS → VRChat Tools → Facial. Face Tracking se trouve dans la même section.

**Fonction :** associe les clés de forme du maillage aux 15 visèmes de synchronisation labiale de VRChat.

Consultez le [guide 8 : configurer la synchronisation labiale](03-guides-b.md#guide-8-set-up-lip-sync). Pour créer des visèmes absents de l’avatar, consultez [Outils CATS : Visemes](09-cats.md#visemes).

**Les 15 emplacements de visèmes VRChat :** `sil`, `PP`, `FF`, `TH`, `DD`, `kk`, `CH`, `SS`, `nn`, `RR`, `aa`, `E`, `I`, `O`, `U`

Description de l’image source anglaise (image omise) : emplacements de visèmes et Face Tracking avant mappage. Cet exemple a des visèmes non associés et 0 expression associée sur 55.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Emplacements de visèmes et Face Tracking avant mappage. Cet exemple a des visèmes non associés et 0 expression associée sur 55.*

---

### Check Performance {#check-performance}

**Emplacement :** onglet CATS → VRChat Tools → Performance

**Fonction :** mesure le rang de performance VRChat de l’avatar et propose des corrections.

Consultez le [guide 9 : améliorer les performances de votre avatar](03-guides-b.md#guide-9-improve-your-avatars-performance).

**Rangs de performance, du meilleur au pire :** Excellent → Good → Medium → Poor → Very Poor

**Outils :**

- **Calculate Performance Rank** : rang actuel, détaillé par polygones, maillages déformables, emplacements de matériaux, os, PhysBones et contacts
- L’optimiseur propose **Remove Zero-Weight Bones**, **Merge Same-Material Meshes**, **Remove Unused Shape Keys** et **Remove Unused Vertex Groups**. **What-If Mode** indique ce que ces corrections changeraient
- VRChat Decimation réduit le nombre de polygones selon un rapport en protégeant les clés de forme

Pour VRChat Decimation :

1. Sélectionnez le maillage de l’avatar.
2. Sélectionnez **Preview**.
3. Sélectionnez **Apply**.

Description de l’image source anglaise (image omise) : mesures de performance et commandes What-If. Sélectionner un maillage d’avatar pour utiliser les actions de nettoyage.

*Panneau contextuel natif, BoneCraft 9.2.18. Mesures de performance et commandes What-If. Sélectionner un maillage d’avatar pour utiliser les actions de nettoyage.*

Description de l’image source anglaise (image omise) : réglages de décimation avant Preview ou Apply. L’exemple utilise Ratio 0.50 et Shape Key Safety. What-If Mode est activé pour les actions de nettoyage ci-dessous.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Réglages de décimation avant Preview ou Apply. L’exemple utilise Ratio 0.50 et Shape Key Safety. What-If Mode est activé pour les actions de nettoyage ci-dessous.*

---

### Exporter vers VRChat {#export-to-vrchat}

**Fonction :** exporte l’avatar terminé en FBX pour le SDK VRChat dans Unity. Sauf si **Remove Shape Keys** est activé, l’exportation conserve les clés de forme (blend shapes).

**Réglages :**

- **Folder** : dossier de destination
- **Avatar** : nom du fichier exporté
- **Sidecar** : écrit aussi un fichier de réglages `.bfvrc` pour l’importateur Unity de BoneCraft
- **Merge Meshes** : joint les maillages de la copie d’exportation en un seul
- **Separate Clothing** : garde les vêtements comme maillages distincts
- **Remove Shape Keys** : applique les clés de forme à la base de la copie d’exportation
- **Embed Textures** : intègre les textures au FBX pour qu’Unity les trouve
- **Helper Meshes** : inclut les maillages masqués ou d’aide. Pour un avatar normal, laisser désactivé
- **Bone Names** : **Keep Original Names**, **Unity-Preset** ou **Unreal-Preset**, appliqué aux copies d’exportation

**Emplacement :** CATS → Import / Export → Game Engine Export → Unity / VRChat.

Avant l’exportation :

1. Si des emplacements requis manquent, lancez ici **Auto-Map Humanoid**.
2. Examinez les emplacements.

Pour vérifier les performances avant l’exportation, sélectionnez **Check Performance Rank**. Avant un préréglage **Bone Names**, corrigez les conflits de mappage ou de noms. La section **Noms des os à l’exportation** ci-dessous les explique. Avant l’exportation, rendez locaux les objets liés. Pour écrire le FBX, sélectionnez **Export to VRChat (Unity)**.

**Normalize Names** renomme le rig de travail. Les préréglages **Bone Names** renomment les copies d’exportation.

L’exportateur Unity/VRChat écrit la pose de repos sans animation. Les boutons principaux Unity et Unreal acceptent les modes Objet, Pose et Édition. Ils utilisent temporairement le mode Objet, puis restaurent le mode et la sélection précédents.

Description de l’image source anglaise (image omise) : réglages Unity / VRChat avant la configuration du dossier et du mappage humanoïde. Cet exemple montre 0 emplacement requis associé sur 15.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Réglages Unity / VRChat avant la configuration du dossier et du mappage humanoïde. Cet exemple montre 0 emplacement requis associé sur 15.*

---

### Nettoyage {#cleanup}

Le nettoyage avant exportation se trouve dans les outils CATS : **Fix Model**, **Join Meshes** et **Apply All Transforms**. Consultez [Outils CATS](09-cats.md).

---

## Passerelle VRM {#vrm-bridge}

Les outils VRM se trouvent dans l’onglet **CATS → Import / Export → VRM / VRoid**. Ils nécessitent le complément VRM. Une passerelle inactive propose **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** et **Show Manual Instructions**.

Pour un paquet hors ligne, utilisez les préférences natives. Un ancien ZIP de complément utilise **Add-ons → Install from Disk…**. Un paquet d’extension moderne utilise le menu natif d’installation des Extensions.

1. Installez le paquet par le menu natif adapté.
2. Activez la dépendance.
3. Vérifiez que la passerelle indique **Active**.

La carte inactive du hub n’a pas de bouton d’installation ZIP.

Description de l’image source anglaise (image omise) : aucune passerelle de format n’est activée dans cet exemple. Installer la passerelle requise avant l’apparition de ses commandes d’importation et d’exportation.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Aucune passerelle de format n’est activée dans cet exemple. Installer la passerelle requise avant l’apparition de ses commandes d’importation et d’exportation.*

---

### Importation VRM et VRoid {#vrm-and-vroid-import}

**Fonction :** importe les avatars `.vrm` (VRoid Studio, Virtual Cast et autres avatars VRM) avec leurs matériaux, squelette et clés de forme.

- **Import VRM…** : fichier `.vrm`
- **Import VRoid (.vroid / .zip)…** : téléchargement VRoid Hub (`.zip`). Un projet VRoid Studio (`.vroid`) affiche une carte expliquant comment l’exporter d’abord en VRM.

---

### Exportation VRM {#vrm-export}

**Fonction :** exporte le personnage riggé en VRM ou au format de l’application cible.

**Réglages :**

- **Folder** et **File** : destination et nom. L’extension suit la cible
- **Target** : VRM 1.0, VRM 0.x, VRChat FBX, VSeeFace, Warudo ou Resonite
- **Scope** : armature active ou toutes les armatures avec données VRM
- Skip lint : exporte sans vérifier la cible. À utiliser uniquement si vous comprenez le risque signalé

Cliquez sur **Export…**.

---

### Vérification VRM Lint {#vrm-lint}

**Fonction :** vérifie l’armature par rapport à la cible sélectionnée avant exportation : mappage humanoïde, métadonnées VRM, visèmes cibles et attentes de l’application.

**Lint Now** lance la vérification sans rien modifier. Sauf si vous sautez lint, les erreurs bloquent l’exportation. Les avertissements identifient du contenu que l’application cible peut importer avec des performances réduites.

Si lint signale des os humanoïdes manquants qui existent, cliquez sur **Fix Humanoid Map**. BoneCraft détecte de nouveau les emplacements et enregistre le mappage. Il ne renomme pas les os.

**Également ici :** **Convert SpringBones → PhysBones** (physique des cheveux VRoid vers VRChat) et **Map VRoid Visemes**.

---

## Passerelle MMD {#mmd-bridge}

Les outils MMD se trouvent dans **CATS → Import / Export → MMD / PMX**. Ils nécessitent **mmd_tools**, installé et activé. BoneCraft reconnaît les anciens paquets et les Extensions Blender modernes.

Une passerelle inactive propose **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** et **Show Manual Instructions**. Le contenu autonome de la passerelle propose aussi **Install from .zip on Disk...** lorsqu’il est affiché. Consultez le [guide 3](02-guides-a.md#step-1--install-mmd_tools) pour l’installation et la vérification des dépôts locaux d’extensions.

---

### Importation MMD {#mmd-import}

- **Import PMX / PMD...** : modèles MMD
- **Import VMD Motion...** : animations MMD
- **Import VPD Pose...** : poses MMD

Vérifiez que l’importation réussit. Une importation PMX annulée ou une erreur d’installation laisse la tâche incomplète. Les modèles importés peuvent nécessiter une vérification des matériaux et du mappage des os avant conversion.

---

### Exportation MMD {#mmd-export}

**Réglages :** **Folder** définit la destination. Chaque format possède des réglages de nom et de portée :

- **PMX File** et **PMX Scope**.
- **VMD File** et **VMD Scope**.
- **VPD File** et **VPD Scope**.

Chaque portée choisit le modèle actif ou tous les modèles MMD de la scène.

**Boutons :** **Export PMX...**, **Export VMD Motion...** et **Export VPD Pose...**

**Également ici :** **Convert Bone Names -> Unity** et **Convert Physics -> PhysBones**.

---

## Exportation vers les moteurs de jeu {#game-engine-export}

**Game Engine Export** est la zone intégrée sous **CATS → Import / Export**. Elle contient **Unity / VRChat** et **Unreal Engine 5**. Le panneau enfant distinct **Game Export** propose l’exportation validée par profil.

### Unreal Engine 5 {#unreal-engine-5}

Avec **Bake Anim** activé, l’exportateur précalcule l’action active. Aucune bande NLA distincte n’est requise. Il n’exporte pas toutes les actions sans rapport.

Avant un préréglage **Bone Names**, corrigez les conflits de mappage ou de noms. La section **Noms des os à l’exportation** ci-dessous les explique. Avant l’exportation, rendez locaux les objets liés.

1. Sélectionnez l’armature et ses maillages.
2. Ouvrez **CATS → Import / Export → Game Engine Export → Unreal Engine 5**.
3. Réglez **Folder**.
4. Réglez **File** sur le nom FBX.
5. Examinez **Bone Names** et son aperçu.
6. Si l’exportation nécessite l’animation active, activez **Bake Anim**.
7. Cliquez sur **Export to Unreal (FBX)**.

**Selected Only** est activé au départ. Incluez l’armature avec ses maillages. **Unit Scale** est activé, **Leaf Bones** désactivé et **Embed Textures** activé au départ. Le panneau abrège **Bake Animation** en **Bake Anim**.

**Import from Unreal (FBX)** ouvre le navigateur de fichiers d’importation.

Description de l’image source anglaise (image omise) : réglages Unreal Engine 5 avant le choix du dossier de sortie. Examiner Bone Names, Selected Only et Bake Anim avant l’exportation.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Réglages Unreal Engine 5 avant le choix du dossier de sortie. Examiner Bone Names, Selected Only et Bake Anim avant l’exportation.*

### Noms des os à l’exportation {#export-bone-naming}

Les deux sections moteur proposent les mêmes choix **Bone Names** :

| Choix | Résultat exporté |
| --- | --- |
| Keep Original Names | Conserve les noms d’os existants. C’est le choix par défaut. |
| Unity-Preset | Utilise les noms Unity Humanoid reconnus, notamment `Hips`, `LeftUpperArm` et `LeftIndexProximal`. |
| Unreal-Preset | Utilise les noms humanoïdes Unreal reconnus, notamment `pelvis`, `spine_01`, `upperarm_l`, `index_01_l` et `ball_l`. |

Sélectionnez une armature pour voir l’aperçu. Il affiche les nombres **Recognized / renamed** et jusqu’à trois changements proposés. Les os non reconnus gardent leurs noms.

Les mappages humanoïdes enregistrés priment sur la détection des noms. Les os facultatifs reconnus de poitrine, cou, épaules, yeux, mâchoire, doigts et orteils participent aussi. Un `Root` distinct reconnu devient `root` avec **Unreal-Preset**.

Les conflits de noms cibles, os ambigus et emplacements humanoïdes réutilisés bloquent le renommage. Corrigez le conflit avant l’exportation. BoneCraft n’ajoute pas de suffixes `.001` pour résoudre ces conflits.

Avant l’exportation, rendez locaux les objets liés. Les préréglages renomment les copies temporaires d’exportation. Le rig de travail conserve ses noms d’os. Les groupes de sommets exportés, canaux d’animation et références d’os du fichier annexe Unity suivent les noms choisis. Le nettoyage retire les données temporaires en cas de réussite ou d’échec.

Ces préréglages changent uniquement les noms. Ils conservent hiérarchie, orientations et pose de repos. Ils n’ajoutent pas d’articulations manquantes et ne construisent pas de squelette Manny/Quinn complet. Le mappage Unity Avatar ou le transfert Unreal peut rester nécessaire.

### Exportation validée par profil {#validated-profile-export}

**Fonction :** exporte avec un profil validé : Unreal humanoid ou universal, Unity humanoid, Godot humanoid, FBX générique ou GLB. La liste des constats montre les corrections disponibles. Les corrections nécessitent votre action explicite.

Utilisez le mode Objet pour cette procédure par profil. La garantie de restauration Objet/Pose/Édition concerne les deux boutons principaux d’exportation vers les moteurs.

Avant un préréglage **Bone Names**, corrigez les conflits de mappage ou de noms. La section **Noms des os à l’exportation** ci-dessus les explique. Avant l’exportation, rendez locaux les objets liés.

**Réglages du navigateur de fichiers :** **Profile**, **Animation**, **Bone Names**, **Root Motion**, **Interpolation** et **T-Pose**. **Bone Names** suit au départ la sélection de la section Unreal. Le profil de format d’exportation reste un choix distinct.

Pour un préréglage de noms, sélectionnez **Active Action** ou **No Animation**. **All Actions** nécessite **Keep Original Names**, car il peut inclure des actions d’autres rigs.

La valeur par défaut de **T-Pose** suit le profil. Les profils Unity humanoid et VRChat utilisent une pose en T. L’exportation en pose en T comprend la pose de repos sans animation. Pour conserver la pose de repos modélisée, sélectionnez **Export as modelled**.

1. Sélectionnez l’armature et ses maillages.
2. Ouvrez **CATS → Import / Export → Game Export**.
3. Cliquez sur **Check for Export**.
4. Examinez les constats et les corrections explicites.
5. Cliquez sur **Export (Profile)**.
6. Sélectionnez les réglages dans le navigateur de fichiers.
7. Sélectionnez le fichier de sortie.
8. Confirmez l’exportation.

Description de l’image source anglaise (image omise) : options d’exportation par profil avant confirmation. Cet exemple utilise Generic FBX, Active Action et Keep Original Names.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Options d’exportation par profil avant confirmation. Cet exemple utilise Generic FBX, Active Action et Keep Original Names.*

**Boutons :**

- **Check for Export** : vérifie le rig par rapport au profil et énumère les constats
- **Apply Transforms (Fix)** : l’une des corrections explicites proposées par la vérification
- **Export (Profile)** : exporte avec le profil

**Emplacement :** onglet **CATS → Import / Export → Game Export**

Consultez le [guide autonome des noms à l’exportation](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/export-bone-naming.md) pour d’autres détails sur les noms et la vérification historique de l’hôte.

Description de l’image source anglaise (image omise) : Check for Export, corrections explicites et Export (Profile). L’exemple n’a pas encore de résultats de vérification du profil.

*Panneau contextuel natif, BoneCraft 9.2.18. Check for Export, corrections explicites et Export (Profile). L’exemple n’a pas encore de résultats de vérification du profil.*

---

## Task Board {#task-board}

**Fonction :** résume le rig actuel avec un score de santé, des améliorations rapides et des tâches par catégorie : os humanoïdes manquants, noms non résolus, visèmes manquants et avertissements de validation. **Quick Wins** montre jusqu’à trois tâches recommandées. **Remaining Tasks** ne contient que les autres. **Open Health Check** lance la validation et ouvre ses résultats. **Refresh Task Board** vérifie de nouveau.

**Emplacement :** onglet **BoneCraft → Overview → Task Board**

Description de l’image source anglaise (image omise) : Task Board énumère les constats de santé et les actions rapides pour le rig d’exemple actif.

*Panneau contextuel natif, BoneCraft 9.2.18. Task Board énumère les constats de santé et les actions rapides pour le rig d’exemple actif.*

---

### Bone Inspector {#bone-inspector}

**Fonction :** affiche les dimensions de repos de l’os de pose actif, son parent, ses contraintes, données personnalisées, pilotes et poids de déformation.

Les informations sont en lecture seule. Avec un os actif en mode Pose, ouvrez ce panneau. Pour copier le nom de l’os, sélectionnez **Copy Name** dans l’en-tête.

**Emplacement :** onglet **BoneCraft → Review → Bone Inspector**

Description de l’image source anglaise (image omise) : Bone Inspector montre les détails de repos de l’os, contraintes, données personnalisées, pilotes et poids de déformation. L’en-tête contient Copy Name.

*Panneau contextuel natif de compilation de test, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Bone Inspector montre les détails de repos de l’os, contraintes, données personnalisées, pilotes et poids de déformation. L’en-tête contient Copy Name.*

Suivant : [Outils CATS](09-cats.md)
