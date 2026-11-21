# Prise en main {#getting-started}

[← Sommaire](index.md)

## Qu’est-ce que BoneCraft ? {#what-is-bonecraft}

BoneCraft est un complément pour Bforartists. Il crée les rigs de personnages et d’accessoires et prépare des avatars 3D pour VRChat, VRoid / VRM et MMD. Ses panneaux automatisent la création du rig, la peinture de poids, les noms d’os, la synchronisation labiale, le suivi des yeux et l’exportation.

**Ce que BoneCraft ne peut pas faire :**

- Modéliser ou sculpter la forme du corps de votre avatar
- Créer des textures ou matériaux à partir de zéro
- Envoyer directement l’avatar dans VRChat (VRChat Creator Companion / SDK reste nécessaire)

---

## BoneCraft et BoneForge {#bonecraft-and-boneforge}

BoneCraft fonctionne uniquement dans Bforartists, un dérivé de Blender. BoneForge est un complément distinct pour Blender standard, avec moins d’outils. N’installez qu’un seul de ces compléments. Dans Blender standard, BoneCraft affiche un avis et un bouton pour obtenir Bforartists. Il ne charge pas ses outils.

BoneForge 9.0.0 et les versions suivantes ciblent Blender standard. BoneCraft est le complément distinct pour Bforartists. Tous deux possèdent Auto-Rig Wizard, Quick Rig, Mannequin et les outils partagés CATS/Material Atlas. BoneCraft possède aussi Mechanisms, Control Picker, son rig de contrôle de production, la détection d’articulations et les outils d’exportation par profil. Des emplacements similaires n’ajoutent pas ces outils à BoneForge.

## Démarrage rapide de la compilation fournie {#supplied-build-quick-start}

La compilation de Bforartists fournie à l’origine contient BoneCraft 9.2.18. Le nouvel aperçu local contient la version candidate 9.2.19. Les deux activent BoneCraft par les réglages d’usine. Dans ces compilations, vous n’installez pas de ZIP et n’activez pas BoneCraft manuellement.

1. Ouvrez la compilation de Bforartists fournie.
2. Appuyez sur **T** pour afficher l’étagère d’outils gauche.
3. Sélectionnez **BoneCraft** ou **Rig Builder**.
4. Appuyez sur **N** pour afficher la barre latérale droite.
5. Sélectionnez **CATS** pour les outils d’avatar et **Import / Export**.

Utilisez les mêmes chemins et réglages d’interface que dans ce manuel. Les outils facultatifs et dépendances conservent leurs prérequis. Les rigs de départ Rigify et les passerelles VRM/MMD nécessitent toujours les dépendances indiquées.

Ces instructions décrivent l’aperçu local de la contribution. Le paquet officiel de Bforartists 5.2.3 ne contient pas cet ensemble. Consultez la [proposition de contribution](https://github.com/Bforartists/Bforartists/pull/7067) pour son historique de revue.

## Installer BoneCraft {#installing-bonecraft}

Cette section concerne le ZIP autonome du Toolkit. Les utilisateurs de la compilation fournie peuvent commencer avec les onglets existants ci-dessus.

Le ZIP public lié est en version 9.2.18. Jusqu’à leur publication, utilisez l’aperçu local pour les corrections de la version candidate 9.2.19.

**Prérequis :**

- Bforartists (BoneCraft est testé sur Bforartists 5.2)
- Le fichier autonome [BoneCraft-BFA-9.2.18.zip](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/bonecraft-v9.2.18/BoneCraft-BFA-9.2.18.zip)

**Étapes :**

Pour une mise à jour :

1. Enregistrez votre travail.

2. Désactivez l’ancienne version autonome du complément BoneCraft.

3. Supprimez l’ancienne version autonome du complément BoneCraft.

4. Redémarrez Bforartists avant d’installer le nouveau ZIP.

Pour une première installation, commencez ici :

1. Ouvrez Bforartists.
2. Ouvrez **Edit** → **Preferences** → **Add-ons**.
3. Sélectionnez **Install from Disk…**.

4. Sélectionnez le fichier `.zip` de BoneCraft.

5. Cochez la case près de BoneCraft pour l’activer.
6. Vérifiez que Preferences indique **9.2.18** pour le ZIP publié lié.

7. Dépliez l’entrée BoneCraft pour voir **Language**, **Tabs**, **Shelf Width**, **Show Helpers** et **Tools**.

Ces étapes installent le ZIP autonome du Toolkit. Suivez le démarrage rapide si la compilation fournie comprend déjà BoneCraft. Évitez d’activer des copies autonome et intégrée en double.

**Vous devez voir :** les onglets BoneCraft et Rig Builder dans l’étagère d’outils gauche (**T**) et l’onglet CATS dans la barre latérale droite (**N**).

## Où se trouvent les outils {#where-things-are}

Chaque onglet contient un groupe de travail. Setup Rigging, Skin, Review, Avatar Tools et Facial sont des sections dépliables à l’intérieur des onglets. Les chemins ci-dessous utilisent les libellés anglais. Les libellés traduits dépendent de la préférence Language.

| Onglet | Emplacement par défaut | Sections |
| --- | --- | --- |
| Rig Builder | Étagère d’outils gauche (T) | Auto-Rig Wizard, Quick Rig - armatures prédéfinies, Mannequin |
| BoneCraft | Étagère d’outils gauche (T) | Overview, Setup Rigging, Skin, Mechanisms, Review |
| CATS | Barre latérale droite (N) | CATS, Avatar Tools, VRChat Tools, Import / Export |

Description de l’image source anglaise (image omise) : BoneCraft est sélectionné dans l’étagère d’outils gauche et CATS dans la barre latérale droite. Appuyez sur T ou N pour afficher ces côtés.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. BoneCraft est sélectionné dans l’étagère d’outils gauche et CATS dans la barre latérale droite. Appuyez sur T ou N pour afficher ces côtés.*

| Outil | Chemin à ouvrir |
| --- | --- |
| Bone Merge | BoneCraft → Setup Rigging → Bone Merge |
| Delta Mush / Proximity Wrap | BoneCraft → Skin → Delta Mush / Proximity Wrap |
| Viseme Library / Lip Sync | CATS → Avatar Tools → Viseme Library → Lip Sync |
| VRChat Viseme Mapping / Face Tracking | CATS → VRChat Tools → Facial |
| Humanoid / Hair | CATS → Avatar Tools → Set Up Humanoid Bones / Add Hair Physics |
| Exportation VRChat | CATS → Import / Export → Game Engine Export → Unity / VRChat |
| Exportation Unreal et Bone Names | CATS → Import / Export → Game Engine Export → Unreal Engine 5 |
| Exportation validée par profil | CATS → Import / Export → Game Export → Export (Profile) |
| Material Atlas | CATS → CATS → Material Atlas → Analyze Materials / Refresh Analysis → Bake Checked Sources |
| VRM / MMD / I/O Hub | CATS → Import / Export → VRM / VRoid, MMD / PMX, Game Engine Export |
| Performance / Clothing / Naming | CATS → VRChat Tools → Check Performance / Attach Clothing / VRChat Naming Extras |

Pour les commandes de rig et de bibliothèque de visèmes, sélectionnez une armature. Pour Delta Mush et Proximity Wrap, sélectionnez un maillage en mode Objet. Lip Sync nécessite une armature en mode Pose. Dépliez le triangle de la section pour voir ses boutons. Les groupes Options contiennent les réglages facultatifs. Si un outil s’exécute immédiatement, réglez-le dans Adjust Last Operation avant toute autre opération.

Les trois procédures faciales ont des buts différents. La génération de visèmes CATS crée des clés de forme de bouche. Viseme Library / Lip Sync stocke des poses et insère des clés d’animation. Facial associe des clés de forme existantes pour VRChat ou configure le suivi facial.

Les commandes de rangement UV se trouvent dans **CATS → CATS → Material Atlas → Advanced Options → UV Packing**. Les anciennes instructions appellent ce groupe Override Inherited Settings. BoneCraft fournit des utilitaires UV d’atlas partagés, pas le complément UVToolkit autonome complet.

**Starter Rigs :**

1. Activez **Starter Rigs** dans le menu des catalogues de l’étagère de ressources du bas.

2. Si nécessaire, sélectionnez toutes les bibliothèques avec **All**.

La version 9.2.5 a supprimé les anciennes commandes Starter Rigs en haut à gauche. **Add → Armature → Starter Rig Catalog** fournit l’ajustement et la génération avec vérification des dépendances.

**Déplacer un onglet :**

1. Ouvrez **Edit** → **Preferences** → **Add-ons** → BoneCraft → **Tabs**.

2. Sélectionnez **Left** ou **Right** pour cet onglet.

Chaque onglet a aussi un commutateur d’affichage. Les changements s’appliquent immédiatement. Quand un onglet est masqué, ses boutons Left et Right deviennent gris mais fonctionnent toujours.

**Éditeur Properties :** **Scene Properties**, dans Preferences → Tabs, est activé au départ. Il montre Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools et Import / Export dans l’onglet Scene de l’éditeur Properties.

Sélectionnez **Show** pour afficher ou masquer ces sections. Le bleu indique qu’elles sont visibles. Ce commutateur ne change ni les onglets de la vue ni l’onglet de données Armature.

Avec une armature sélectionnée, les outils d’armature BoneCraft apparaissent aussi dans l’onglet de données Armature. Ils ne suivent pas les commutateurs de visibilité. Rig Builder, Mechanisms et les sections CATS utilisent l’onglet Scene.

Pour retirer un outil de tous les emplacements, désactivez son paquet dans **Tools**. Vous pouvez aussi désactiver le complément.

**Shelf Width :** Widen Narrow Shelves est activé au départ. Il élargit une fois les étagères contenant des onglets BoneCraft si leur largeur est inférieure au minimum Left ou Right. À une échelle d’interface de 1×, les valeurs par défaut sont de 240 pixels à gauche et de 260 pixels à droite. Si vous réduisez ensuite une étagère en faisant glisser son bord, elle conserve la largeur choisie. Pour contrôler manuellement les largeurs, désactivez le commutateur. Ses champs de largeur deviennent inactifs.

Description de l’image source anglaise (image omise) : Tabs place BoneCraft et Rig Builder à gauche et CATS à droite. Shelf Width et Show Helpers se trouvent dessous.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Tabs place BoneCraft et Rig Builder à gauche et CATS à droite. Shelf Width et Show Helpers se trouvent dessous.*

**Menus et onglets intégrés de l’étagère d’outils :** vous pouvez aussi accéder aux outils depuis les menus d’en-tête de la vue 3D :

| Emplacement | Outils |
| --- | --- |
| Add → Armature | Quick Rig, Auto-Rig Wizard, Mannequin for Active Rig |
| Pose → BoneCraft (mode Pose) | Outils de pose, sélecteur, collections d’os, configuration et vérification du rig |
| Weights → BoneCraft (mode peinture de poids) | Remplir, symétriser et normaliser les poids |
| Object → Mechanisms (mode Objet) | Ajouter des pièces, articulations et liens ; tester le mouvement |
| Tool Shelf → Pose ou Weights → BoneCraft | Boutons pour les opérations courantes de pose ou de poids |

Les boutons Pose et Weights affichent du texte dans une étagère large. Une étagère étroite affiche une grille d’icônes. Survolez une icône pour lire son infobulle. Ces emplacements utilisent les mêmes outils que les onglets BoneCraft. Seuls les paquets d’outils activés sont disponibles.

**Outils de la vue :** Place Rig Markers place le prochain repère de l’assistant Auto-Rig lorsque vous cliquez sur le maillage. Build Mechanism démarre une articulation ou un lien guidé lorsque vous cliquez sur une pièce. Consultez [Rig Builder](06-rig-builder.md#auto-rig-wizard) et [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each) pour la préparation et les commandes.

**Exécuter d’abord, régler ensuite :** Quick Rig, Fit Dropped Rig, Weight Mirror, Weight Transfer, Flood to Custom, Ribbon, Spline IK et Delta Mush s’exécutent immédiatement.

1. Sélectionnez l’outil.

2. Réglez immédiatement ses options dans le panneau Adjust Last Operation de la vue.

3. Terminez ces réglages avant toute autre opération.

D’autres panneaux contiennent des réglages facultatifs dans un groupe sous les boutons d’action. Dépliez-le pour les utiliser. Si un panneau nécessite une autre sélection, il peut rester visible et expliquer quoi sélectionner.

**Show Helpers :** BoneCraft explique ses sections par de courtes lignes « quoi / quand » et des notes « How this works ». Pour les masquer, désactivez **Show Helpers** dans les préférences du complément. Dans Avatar Tools, **Compact Mode** commande le même commutateur.

**Language :** le réglage **Language** des préférences du complément traduit les panneaux propres à BoneCraft en English, 日本語, 한국어, 中文, Français, Português ou Español.

Description de l’image source anglaise (image omise) : l’aperçu local indique BoneCraft 9.2.19 et English comme Language.

*Aperçu local, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. L’aperçu local indique BoneCraft 9.2.19 et English comme Language.*

**Examiner le nettoyage avant exécution :**

1. Examinez les options de Fix Model.

2. Sélectionnez les opérations nécessaires à votre avatar.

3. Enregistrez un point de sauvegarde avant les changements.

4. Après l’opération, inspectez le résultat.

Pipeline Status et Operation Ledger consignent la progression. Consultez [Le pipeline CATS](04-cats-pipeline.md).

**Panneau rapide :** appuyez sur **Ctrl+Shift+R** dans la vue 3D pour ouvrir le panneau de rig BoneCraft sous le curseur.

---

## Par où commencer ? {#where-should-i-start}

Sélectionnez le guide adapté à votre tâche :

> **Créer le rig d’un nouveau modèle FBX, OBJ ou Blender pour VRChat.**
> → Consultez le [guide 1 : importer votre premier avatar dans VRChat](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)

> **Préparer un avatar VRM exporté depuis VRoid Studio.**
> → Consultez le [guide 2 : importer un avatar VRoid dans VRChat](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)

> **Préparer un modèle MMD (fichier PMX) pour VRChat.**
> → Consultez le [guide 3 : importer un avatar MMD dans VRChat](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)

> **Corriger des noms d’os qui empêchent l’envoi d’un avatar déjà riggé.**
> → Consultez le [guide 4 : corriger les noms d’os de votre avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

> **Préparer la synchronisation labiale, le suivi des yeux et le maillage d’un avatar riggé pour VRChat.**
> → Consultez le [guide 13 : préparer votre avatar pour VRChat avec CATS](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)

> **Trouver la solution à un problème particulier.**
> → Consultez l’[index des solutions rapides](10-reference.md#quick-fix-index)

Suivant : [Guides 1–7](02-guides-a.md)
