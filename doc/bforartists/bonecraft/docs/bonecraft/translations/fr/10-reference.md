# Solutions rapides et glossaire {#quick-fixes-and-glossary}

[← Sommaire](index.md)

## Index des solutions rapides {#quick-fix-index}

Utilisez cet index pour trouver les indications adaptées à un problème.

| Problème | Où chercher |
|---|---|
| Échec de l’envoi : os non reconnus | [Guide 4](02-guides-a.md#guide-4-fix-your-avatars-bone-names) + [VRChat Naming Extras](08-vrchat.md#vrchat-naming-extras) |
| Avatar en pose en T / ne suit pas les mouvements | [Guide 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system) + [Set Up Humanoid Bones](08-vrchat.md#set-up-humanoid-bones) |
| Maillage déformé anormalement / peau étirée | [Weight Transfer](05-rig-tools.md#weight-transfer) + [Weight Mirror](05-rig-tools.md#weight-mirror), ou recalcul avec [Automatic Bone Weight Recalculation](05-rig-tools.md#automatic-bone-weight-recalculation) |
| Poids différents entre les deux côtés du corps | [Weight Mirror](05-rig-tools.md#weight-mirror) |
| Cheveux traversant la tête | [Guide 6, étape 5](02-guides-a.md#step-5--add-colliders-recommended) — ajouter des colliders |
| Physique des cheveux immobile | [Guide 6](02-guides-a.md#guide-6-add-hair-physics) — vérifier la détection des chaînes et le préréglage PhysBone |
| Vêtements traversant le corps | [Guide 7](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body) : <ol><li>Examiner le maillage en pose.</li><li>En cas d’intersection, corriger l’ajustement ou les poids.</li></ol> **Detect Collisions** vérifie uniquement les noms d’os. |
| Synchronisation labiale inopérante | [Guide 8](03-guides-b.md#guide-8-set-up-lip-sync) + [VRChat Viseme Mapping](08-vrchat.md#vrchat-viseme-mapping) |
| Performances de l’avatar classées Very Poor | [Guide 9](03-guides-b.md#guide-9-improve-your-avatars-performance) + [Check Performance](08-vrchat.md#check-performance) |
| Échec de l’importation VRM | [Guide 2, étape 1](02-guides-a.md#step-1--install-the-vrm-add-on) — installer le complément VRM |
| Échec de l’importation MMD | [Guide 3, étape 1](02-guides-a.md#step-1--install-mmd_tools) — installer mmd_tools |
| MMD installé mais passerelle inactive | Activer mmd_tools avec **Open Add-on Preferences**. Examiner le message d’installation dans le [guide 3](02-guides-a.md#step-1--install-mmd_tools). |
| Sélection de l’atlas modifiée après actualisation | **Refresh Analysis** reconstruit les choix. <ol><li>Examiner les sources.</li><li>Sélectionner Bake Checked Sources.</li></ol> Consulter [Material Atlas Combiner](09-cats.md#material-atlas-combiner). |
| Select All laisse une texture décochée | Les textures manquantes restent exclues. La sélection groupée ne change que sa liste dans le groupe actif — [sélection des sources](09-cats.md#analyze-and-choose-sources) |
| L’atlas signale une source modifiée | <ol><li>Actualiser l’analyse.</li><li>Examiner de nouveau les sources.</li></ol> Le contrôle préalable rejette les sources analysées devenues périmées avant la création de la sauvegarde. |
| L’atlas ne propose pas Revert | **Preserve Backup Duplicate** était désactivé, ou Accept a supprimé la sauvegarde. Utiliser votre point de sauvegarde de fichier. |
| Précalcul d’atlas Metallic ou ORM bloqué | Laisser **Metallic** et **Pack ORM Channels** désactivés. Ces passes restent bloquées dans 9.2.18. |
| Texture d’atlas brouillée dans le moteur | Vérifier UV0. **Keep Source UV Maps** peut laisser `atlas_uv` sur UV1 — [réglages UV](09-cats.md#advanced-options) |
| Échec de l’exportation depuis le mode Pose ou Édition | Utiliser le bouton principal actuel Unity ou Unreal. Il restaure le mode et la sélection. Utiliser le mode Objet pour **Export (Profile)**. |
| Conflit de noms à l’exportation | Corriger le nom cible ou le mappage humanoïde — [noms des os à l’exportation](08-vrchat.md#export-bone-naming) |
| All Actions bloqué avec un préréglage de noms | Sélectionner **Active Action**, **No Animation** ou **Keep Original Names** — [exportation validée par profil](08-vrchat.md#validated-profile-export). |
| Anciennes formes de mécanismes nécessitant une version actuelle | 9.2.18 lit et applique les anciennes formes sans les réenregistrer — [Forms](07-mechanisms.md#forms) |
| Erreurs dans le validateur de rig | [Rig Validator](05-rig-tools.md#rig-validator) : <ol><li>Lancer la validation.</li><li>Suivre les messages.</li></ol> |
| Os disparus / aucun os visible | [Bone Collections](05-rig-tools.md#bone-collections) → **Show All Collections** |
| Panneaux BoneCraft introuvables | BoneCraft et Rig Builder utilisent l’étagère d’outils gauche (**T**). CATS utilise la barre latérale droite (**N**). Consulter [Où se trouvent les outils](01-start.md#where-things-are). |
| Besoin d’un exemple Mechanisms complet | [Tutoriel : Crescent Rose](12-crescent-rose.md) — 8 étapes de préparation et 30 étapes Mechanisms avec instructions écrites et descriptions d’images sources anglaises conservées, ainsi que le fichier terminé dans `examples/crescent-rose/` |
| Onglet du mauvais côté | Preferences → Add-ons → BoneCraft → Tabs → Left ou Right |
| Sections BoneCraft absentes de Properties → Scene | Preferences → Add-ons → BoneCraft → Tabs → Scene Properties → Show. Le bleu indique l’activation. Vérifier aussi les paquets d’outils dans Tools. |
| Masquer BoneCraft dans Properties → Scene | Désactiver Scene Properties → Show dans Preferences → Tabs. Les onglets de la vue et l’onglet de données Armature restent inchangés. |
| Outil lancé avant le choix de ses options | Dans 9.1, régler ses options immédiatement après dans le panneau Adjust Last Operation de la vue, avant toute autre opération |
| Place Rig Markers ne place aucun repère | <ol><li>Lancer Auto-Rig Wizard.</li><li>Avancer à une étape de repères.</li><li>Passer en mode Objet.</li><li>Cliquer sur le maillage sélectionné par l’assistant.</li></ol> Consulter [Rig Builder](06-rig-builder.md#auto-rig-wizard). |
| Build Mechanism ne sait pas quelles pièces utiliser | <ol><li>Utiliser d’abord Add Parts from Selection.</li><li>Sélectionner le rig de mécanisme ou l’une de ses pièces.</li><li>Sélectionner le type dans l’en-tête de l’outil.</li><li>Cliquer sur la première pièce.</li></ol> Consulter [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each). |
| Exportation bloquée : os humanoïdes signalés absents alors qu’ils existent | Si un os requis n’existe pas, il faut d’abord l’ajouter au rig. Si les os requis existent : <ol><li>Lancer Auto-Map All.</li><li>Lancer Fix Humanoid Map dans les contrôles lint de VRM / VRoid.</li></ol> Consulter le [guide 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system). |
| FBX exporté montrant des formes d’aide ou tubes géants | Si les maillages de contrôle ou de formes personnalisées sont inutiles, garder **Helper Meshes** désactivé. |
| Matériaux gris à l’importation dans Unity ou Unreal | <ol><li>Exporter avec Embed Textures activé.</li><li>Utiliser les options d’importation/extraction de matériaux d’Unity ou l’importation de matériaux FBX d’Unreal.</li></ol> |
| Poids associés aux mauvais os | Relancer Generate Rig dans l’assistant, utiliser [Weight Transfer](05-rig-tools.md#weight-transfer) ou **Smart Automatic Weights** dans l’onglet CATS |
| Fusionner deux rigs en un | [Guide 11 : fusionner deux rigs](03-guides-b.md#guide-11-merge-two-rigs-together) |
| Forme corrective ne s’activant pas | Vérifier l’axe et l’angle de l’os dans [Corrective Shape Keys](05-rig-tools.md#corrective-shape-keys) |
| Animation incorrecte sur un autre rig | [Retarget](05-rig-tools.md#retarget) — vérifier le mappage des os |
| Avertissement CATS « Run Fix Model first » | <ol><li>Examiner les options de nettoyage.</li><li>Décider si l’avatar en a besoin.</li></ol> L’avertissement ne verrouille pas les outils. Consulter [Le pipeline CATS](04-cats-pipeline.md). |
| Bouche se déchirant ou se séparant pendant la parole | Examiner les clés de bouche sources, la topologie et les modificateurs — [CATS : Visemes](09-cats.md#visemes) |
| Yeux de l’avatar bloqués vers le bas dans VRChat | <ol><li>Vérifier les affectations gauche/droite, l’orientation des os et les contraintes.</li><li>Examiner l’avatar exporté.</li></ol> Consulter [CATS : Eye Tracking](09-cats.md#eye-tracking). |
| Clé de forme faisant exploser le maillage | <ol><li>Tester la clé seule.</li><li>Examiner la topologie, les valeurs des clés sources et les modificateurs.</li></ol> BoneCraft capture un mélange de clés, pas la déformation des os. Consulter [CATS : Pose & Shape Keys](09-cats.md#pose--shape-keys). |
| Avatar apparaissant à la mauvaise taille dans VRChat | Vérifier les transformations du maillage et de l’armature et les réglages d’échelle d’exportation/importation. Pour restaurer l’état, utiliser Undo ou un point de sauvegarde. Consulter [Apply All Transforms](09-cats.md#apply-all-transforms). |
| Noms d’os en japonais / chinois / coréen | [CATS : Translate Bone Names](09-cats.md#translate-bone-names) |
| Avatar sans synchronisation labiale ni clé de forme de bouche | [CATS : Visemes](09-cats.md#visemes) : créer d’abord les formes de bouche de base. CATS génère 15 visèmes à partir de trois affectations sources : A, O et CH. |
| Mécanisme signalant « changed by hand » | [Mechanisms](07-mechanisms.md) — utiliser **Keep mine** ou **Restore** |

## Glossaire {#glossary}

**Adjust Last Operation :** panneau de la vue permettant de changer les options de la dernière opération. De nombreux outils de BoneCraft 9.1 s’exécutent d’abord, puis montrent leurs options ici. Réglez-les avant toute autre opération.

**Armature :** nom utilisé par Bforartists pour un squelette : un ensemble d’os que l’on peut poser et animer.

**Blend shape :** voir Clé de forme.

**Os :** segment d’un squelette. Les os forment une hiérarchie (parent → enfant) où les enfants suivent leurs parents.

**Collection d’os :** groupe nommé d’os. Vous pouvez afficher ou masquer une collection entière à la fois.

**Bone Names :** choix des noms à l’exportation. Keep Original Names conserve les noms. Unity-Preset et Unreal-Preset renomment les os reconnus sur les copies d’exportation.

**Bake Checked Sources :** action d’atlas précalculant les choix de groupes et de sources examinés sans reconstruire automatiquement l’analyse.

**CATS :** outils CATS de préparation de modèles pour VRChat avec un pipeline guidé (nettoyage, visèmes, suivi des yeux, transformations). Ils se trouvent dans l’onglet CATS.

**Pipeline CATS :** ordre en six phases des outils CATS : Fix Model → Material Atlas → Visemes → Eye Tracking → Pose to Shape → Apply Transforms. Les outils avertissent lorsqu’une phase précédente dont ils dépendent est incomplète.

**Clé de forme corrective :** clé de forme qui s’active lorsqu’un os atteint un angle, afin de corriger le maillage dans les poses extrêmes.

**Os de déformation :** os qui déplace le maillage. Certains os ne servent qu’au contrôle et ne déforment pas le maillage.

**Suivi des yeux :** outil CATS configurant les os des yeux (`LeftEye`, `RightEye`) et les contraintes de rotation utilisées par VRChat pour déplacer les yeux.

**FBT (Full Body Tracking) :** fonction de VRChat suivant le corps entier, hanches et pieds compris, avec du matériel supplémentaire comme les Vive Trackers. Fix FBT ajuste l’os racine pour cette fonction.

**FBX :** format de fichier transportant modèles 3D, squelettes et animations entre logiciels. C’est le format standard de VRChat.

**Fix Model :** opérations de nettoyage CATS sélectionnables pour les sommets en double, la géométrie isolée, les normales et d’autres données.

1. Examinez les options.

2. Exécutez uniquement les opérations nécessaires à votre avatar.

**FK (Forward Kinematics) :** création d’une pose en faisant tourner successivement les os d’une chaîne : épaule, coude, poignet. Adaptée aux grandes poses corporelles.

**IK (Inverse Kinematics) :** création d’une pose en plaçant l’extrémité d’une chaîne, par exemple une main ou un pied. Les os intermédiaires suivent. Cette méthode convient au placement précis des mains et des pieds.

**Humanoid :** système d’avatars de VRChat associant les os à des emplacements corporels standard afin que chaque avatar utilise les mêmes commandes de mouvement.

**Mécanisme :** rig d’accessoire ou de machine construit avec des os et contraintes ordinaires. Il peut être une articulation (Hinge, Slide, Telescope) ou un lien (Piston, Gear Link, Follow). Consultez [Mechanisms](07-mechanisms.md).

**Maillage :** surface 3D composant le corps visible de l’avatar.

**MMD (MikuMikuDance) :** logiciel gratuit d’animation 3D populaire au Japon et dans la communauté anime. Il utilise les fichiers de modèles `.pmx` et d’animation `.vmd`.

**Morph target :** voir Clé de forme.

**Operation Ledger :** liste CATS de toutes les opérations effectuées, avec leur heure et leur résultat.

**PhysBone :** composant VRChat faisant osciller, rebondir et entrer en collision les os. Utilisé pour les cheveux, queues et accessoires suspendus.

**Pipeline Status :** liste CATS des six phases, avec une coche pour chaque phase terminée.

**PMX :** principal format de modèles 3D de MikuMikuDance.

**Pose Mode :** mode de pose et d’animation des os.

1. Sélectionnez l’armature.

2. Appuyez sur Ctrl+Tab.

Vous pouvez aussi sélectionner Pose Mode dans le menu de mode en haut à gauche de la vue.

**Rig / rigging :** construction d’un squelette dans un modèle 3D et liaison du maillage pour pouvoir le poser et l’animer.

**Clé de forme :** version enregistrée d’un maillage dans une position déformée. Les clés se mélangent avec des intensités différentes. Elles pilotent les expressions du visage, la synchronisation labiale et les transformations du corps.

**SDK (Software Development Kit) :** pour VRChat, VRChat Creator Companion et ses outils Unity pour envoyer les avatars.

**Spline IK :** chaîne d’os suivant une courbe. Utilisée pour les queues, tentacules, longs cheveux et colonnes vertébrales.

**Pose en T :** pose de référence, debout avec les bras tendus sur les côtés.

**Étagère d’outils :** panneau gauche de la vue 3D (**T**). BoneCraft et Rig Builder l’utilisent par défaut.

**Sommet :** point dans l’espace 3D. Les maillages comprennent de nombreux sommets reliés par des arêtes et faces.

**Groupe de sommets :** ensemble nommé de sommets définissant ceux qu’un os déplace.

**Visème :** forme de bouche pour un son de parole. VRChat utilise 15 visèmes pour la synchronisation labiale.

**Poids / peinture de poids :** valeurs de 0.0 à 1.0 indiquant avec quelle intensité chaque os déplace chaque sommet. La peinture de poids permet de les ajuster visuellement.

**Assistant :** Auto-Rig Wizard de Rig Builder place des repères sur votre maillage et construit le rig à partir de ceux-ci.

**Os sans poids :** os ne déplaçant aucun sommet. Il réduit les performances sans changer l’apparence de l’avatar. Fix Model et l’optimiseur de performances suppriment ces os.

Suivant : [Nouveautés](11-whats-new.md)
