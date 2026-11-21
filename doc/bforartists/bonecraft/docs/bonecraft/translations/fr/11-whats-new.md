# Nouveautés {#whats-new}

[← Sommaire](index.md)

Versions les plus récentes en premier.

## 9.2.19 — Commandes des panneaux (version candidate locale) {#9219--panel-controls-local-candidate}

Cette version candidate locale n’a pas été publiée. La version autonome reste la 9.2.18.

- Collections et Visibility Bookmarks initialisent leurs réglages en dehors du dessin des panneaux.
- Les panneaux groupés utilisent leurs propres commandes et vérifient la sélection et le mode actuels.
- Hair Physics lit les os de pose sélectionnés sur les hôtes actuels.
- Bone Inspector affiche le roulis de repos des os et copie les noms avec son bouton d’en-tête.
- Eye Tracking affiche les valeurs en degrés en conservant les réglages enregistrés.

Le manuel anglais ajoute des images correspondantes pour les outils et réglages. Les images antérieures conservent leurs libellés de version d’origine.

## 9.2.18 — Formes de mécanismes enregistrées {#9218--saved-mechanism-forms}

Les anciennes formes enregistrées restent lisibles et utilisables dans les compilations actuelles de Bforartists. Ouvrir ou appliquer une forme ne la réenregistre pas. **Save Form** capture les valeurs actuelles au format actuel. Les poignées, curseurs et emplacements de panneaux existants restent inchangés.

Cette version corrige les diagnostics de compatibilité sur les hôtes plus récents. Le diagnostic seul ne prouvait pas que les hôtes antérieurs ne pouvaient pas utiliser les formes enregistrées. Consultez [Forms](07-mechanisms.md#forms) et les [notes de version](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md).

Il s’agit de la publication autonome du Toolkit. Elle ne constitue pas une acceptation dans Bforartists officiel. Les limites historiques des captures et tests de tutoriels restent précisées dans les chapitres.

## 9.2.17 — Noms à l’exportation et restauration du mode {#9217--export-naming-and-mode-restoration}

**Unity / VRChat** et **Unreal Engine 5** proposent désormais **Bone Names** : **Keep Original Names**, **Unity-Preset** et **Unreal-Preset**. L’aperçu montre les os reconnus et les noms proposés. Le renommage concerne les copies d’exportation, y compris les groupes de sommets, canaux d’animation et références du fichier annexe Unity. Le rig de travail conserve ses noms.

Les deux boutons principaux d’exportation vers les moteurs acceptent désormais les modes Objet, Pose et Édition. Ils restaurent le mode et la sélection d’origine après l’exportation ou le nettoyage. Le précalcul FBX de l’action active ne nécessite plus de bande NLA distincte.

Les os humanoïdes facultatifs reconnus, doigts et orteils participent au renommage. Les conflits de noms ou mappages ambigus le bloquent. Ces profils conservent hiérarchie, orientation et pose de repos. Ils ne construisent pas de squelette Manny/Quinn.

La sortie renommée d’**Export (Profile)** prend en charge **Active Action** et **No Animation**. **All Actions** nécessite **Keep Original Names**. Consultez [Game Engine Export](08-vrchat.md#game-engine-export) et les [notes 9.2.17](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.17/RELEASE-NOTES.md).

## 9.2.15 — Procédure d’atlas de matériaux avec examen {#9215--reviewed-material-atlas-workflow}

Le panneau présente maintenant trois étapes : sélection des cibles, sélection des matériaux et textures, puis précalcul et examen. **Smart Combine Materials** est le raccourci automatique initial. Après analyse, **Refresh Analysis** reconstruit les listes. **Bake Checked Sources** précalcule les choix examinés.

Les deux listes de sources ont **Select All** et **Deselect All**. Ils ne changent les cases Include que dans le groupe et la liste de sources actifs. Les textures manquantes restent décochées. La sélection groupée n’active pas un groupe désactivé. **Object → Atlas Source Selection** propose les mêmes actions.

**Source Details** est replié au départ. **Copy Debug Report** se trouve sous **Advanced Options**. Backup, Accept et Revert restent visibles. Ces changements d’interface conservent la procédure et les contraintes de préservation du précalcul existantes.

## 9.2.14 — Maillages à couleur seule {#9214--color-only-meshes}

Les maillages à couleur seule sans UV créés reçoivent la couche UV de l’atlas précalculé lors de l’assemblage final.

## 9.2.13 — Comptage des matériaux {#9213--material-counts}

Les estimations et résultats de matériaux comptent les emplacements d’atlas de chaque maillage de sortie. Revert réinitialise ces résultats.

## 9.2.12 — Exporter UV0 {#9212--export-uv0}

Le maillage d’atlas reconstruit exporte `atlas_uv` comme UV0 si **Keep Source UV Maps** est désactivé. Conserver les cartes sources peut laisser l’atlas sur UV1.

## 9.2.11 — Vérification des sources modifiées {#9211--changed-source-checks}

Le contrôle préalable rejette les sources de matériaux analysées manquantes ou modifiées avant de créer une sauvegarde d’atlas.

1. Actualisez l’analyse.

2. Examinez de nouveau les choix de sources.

## 9.2.10 — Matériaux exclus {#9210--excluded-materials}

L’assemblage d’atlas préserve les matériaux exclus et les références de matériaux partagées.

## 9.2.9 — Sources masquées au rendu {#929--render-hidden-sources}

Le combinateur précalcule les sources masquées au rendu à travers des copies temporaires. Revert restaure la visibilité d’origine.

## 9.2.8 — Entrées de shader connectées {#928--connected-shader-inputs}

Le combinateur préserve les graphes de teinte Principled, de mappage et d’alpha connectés durant le précalcul. MToon conserve sa voie de repli. **Metallic** et **Pack ORM Channels** restent bloqués par le contrôle préalable.

## 9.2.7 — Classification de la transparence {#927--transparency-classification}

La classification des matériaux gère l’opacité DITHERED moderne et l’alpha lié ou constant. Le seul réglage de rendu ne force plus un matériau opaque dans un groupe transparent.

## 9.2.6 — Installation de MMD et PMX {#926--mmd-and-pmx-installation}

L’installateur reconnaît les Extensions MMD modernes et les anciens compléments. L’installation d’une extension conserve ses dépendances et signale les dépôts locaux indisponibles. Une extension activée est reconnue même sans métadonnées d’ancien complément. Une importation PMX annulée reste annulée au lieu d’être signalée comme réussie.

Le [relevé daté des corrections](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md) couvre 9.2.6–9.2.15 et leurs vérifications sur scènes générées. La [revue de l’interface 9.2.15](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md) consigne les vérifications des opérateurs et les limites des tests visuels. Ces relevés historiques ne prétendent pas qu’un nouveau parcours du manuel complet a été effectué dans 9.2.18.

## 9.2.5 — Onglet du catalogue Starter Rigs {#925--starter-rigs-catalog-tab}

Starter Rigs utilise désormais un onglet de catalogue dans l’étagère native de ressources du bas. Il remplace les commandes en haut à gauche de la vue. Pour afficher l’onglet près des autres catalogues, activez une fois **Starter Rigs** dans le menu des catalogues de l’étagère. L’importation native de ressources et **Add → Armature → Starter Rig Catalog** restent disponibles.

## 9.2.4 — Task Board et outils natifs {#924--task-board-and-native-tools}

**Open Health Check** lance désormais la validation du rig et ouvre les résultats. Avant de l’utiliser, sélectionnez une armature ou son maillage lié. **Quick Wins** montre jusqu’à trois recommandations. **Remaining Tasks** exclut ces cartes. **Refresh Task Board** vérifie de nouveau.

Place Rig Markers et Build Mechanism restent disponibles comme outils de la vue. Leur enregistrement ne perturbe plus Grab/Move natif ni le passage entre outils en modes Objet et Pose.

## 9.2.3 — Emplacement de l’exportation VRChat {#923--vrchat-export-location}

Supprime le panneau Export to VRChat en double dans Avatar Tools. L’exportation reste sous CATS → Import / Export → Unity / VRChat.

## 9.2.2 — Interface actuelle {#922--current-interface}

Chaque onglet contient un groupe de travail. Setup Rigging, Skin, Review, Avatar Tools et Facial sont des sections dépliables à l’intérieur des onglets. Les chemins ci-dessous utilisent les libellés anglais. Leur traduction dépend de la préférence Language.

- Bone Merge → BoneCraft → Setup Rigging
- Delta Mush / Proximity Wrap → BoneCraft → Skin
- Viseme Library / Lip Sync → CATS → Avatar Tools
- VRChat Viseme Mapping / Face Tracking → CATS → VRChat Tools → Facial

## 9.2.0 (octobre 2026) {#920-october-2026}

- **Catalogue de départ complet :** les neuf squelettes et métarigs fournis ont des vignettes dès le départ : Basic Humanoid, Simple Human, Full Human, Basic Quadruped, Cat, Horse, Wolf, Bird et Shark. Le sélecteur de catalogue regroupe Humans, Quadrupeds et Other Animals.
- **Rigify selon les besoins :** Basic Humanoid fonctionne indépendamment. Les rigs de départ Rigify restent visibles si Rigify est désactivé. En sélectionner un propose **Enable Rigify & Add Rig** ou Cancel. Une annulation, un échec d’activation ou un préréglage indisponible n’ajoute aucun rig.
- **Étagère facultative, emplacement historique 9.2.0 :** le commutateur **Starter Rigs** de l’en-tête de la vue est revenu à l’étagère de ressources habituelle. Le choix persistait dans les préférences. La version 9.2.5 remplace ce commutateur par un onglet de catalogue natif. **Add → Armature → Starter Rig Catalog** ouvre toujours le sélecteur en fenêtre contextuelle.
- **Cliquer ou glisser :** cliquer sur un rig de départ l’ajoute, comme le déposer dans la vue. L’ajustement au maillage est activé au départ. La pondération et la génération de contrôles sont désactivées. Adjust Last Operation règle ces options. Les vérifications de clic, dépôt, annulation et annulation/rétablissement natifs ont utilisé Bforartists 5.2.0.

## 9.1.2 (octobre 2026) {#912-october-2026}

- **Commutateur Scene Properties :** Preferences > Tabs possède une nouvelle ligne Scene Properties. Son bouton Show contrôle toutes les sections BoneCraft dans Properties > Scene : Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools et Import / Export. Le commutateur est activé au départ et bleu lorsqu’il est activé. Il ne désactive pas le complément et ne change pas les onglets de la vue ou Armature. Consultez [Où se trouvent les outils](01-start.md#where-things-are).

## 9.1.1 (octobre 2026) {#911-october-2026}

- **Icônes plus claires :** chaque icône conserve désormais le même sens dans toute l’interface. Environ 60 boutons ont reçu des icônes Bforartists plus adaptées à leur fonction : Apply All Transforms, Decimate, Normalize Names, Translate, Merge, Separate, Blend Pose et Lip Sync, entre autres. Chaque bouton utilise la même icône dans tous les panneaux.
- **Panneaux plus sobres :** les titres et textes fixes ne portent plus d’icônes thématiques. Les indications d’état montrent une icône d’information, d’avertissement ou de validation.
- **Grille d’icônes lisible :** chaque bouton des onglets Pose et Weights de l’étagère possède sa propre icône, rendant une étagère étroite lisible.

## 9.1.0 (octobre 2026) {#910-october-2026}

- **Outils aux emplacements natifs de Bforartists :** BoneCraft ajoute des entrées à Add → Armature et aux menus Pose, Weights et Object. Il ajoute aussi des panneaux de boutons aux onglets Pose et Weights de l’étagère d’outils Bforartists.
- **Exécuter puis régler :** Quick Rig, Fit Dropped Rig et les outils de poids s’exécutent immédiatement avec leurs dernières valeurs. Ribbon, Spline IK, Delta Mush et les outils d’os CATS font de même. Adjust Last Operation contrôle ensuite leurs options. Les outils utilisent moins de confirmations contextuelles.
- **Actions en premier, options repliées :** plusieurs panneaux affichent les boutons au-dessus d’un groupe de réglages facultatifs. Les entrées requises et options de nettoyage de Fix Model restent au-dessus de l’action. Les réglages utilisent des cases à cocher plutôt que des boutons. Les en-têtes n’ont pas d’icônes.
- **Outils gestuels :** Place Rig Markers et Build Mechanism se trouvent dans la barre d’outils de la vue. Place Rig Markers place le prochain repère d’Auto-Rig Wizard quand vous cliquez sur le maillage. Build Mechanism démarre une articulation ou un lien quand vous cliquez sur une pièce.
- **Sections d’avatar, emplacement historique 9.1.0 :** Avatar Tools contenait le mappage humanoïde, les cheveux, visèmes et l’exportation. La section VRChat Tools distincte regroupe Performance, Clothing et Naming. L’exportation est maintenant sous **Import / Export → Game Engine Export → Unity / VRChat**.
- **Infobulles :** chaque opérateur et chaque option s’explique.
- **Montrer plutôt que masquer :** sans rig disponible, les sections restent visibles et expliquent quoi sélectionner. Auto-Rig Wizard apparaît en premier dans Rig Builder. Les étagères commencent assez larges pour être lisibles.
- **Corrections :** Generate Spline IK fonctionne de nouveau. Add Influence utilise l’os choisi. Les aperçus de visèmes utilisent leur ensemble.

## 9.0.0 (octobre 2026) {#900-october-2026}

- **Mechanisms :** une nouvelle section dans l’onglet BoneCraft et l’onglet Scene de Properties crée des rigs d’accessoires et machines. Ses types sont Hinge, Slide, Telescope, Piston, Gear Link, Follow et Sequence. Des étapes guidées les construisent. Test vérifie leur mouvement. BoneCraft n’écrase jamais automatiquement une retouche manuelle. **Keep mine** conserve la retouche. **Restore** reconstruit le mécanisme. Consultez [Mechanisms](07-mechanisms.md).
- **Fichier d’exemple :** `examples/crescent-rose/` contient Crescent Rose avec un rig Mechanisms (formes faux, fusil et compacte) ; le [chapitre 12](12-crescent-rose.md) du manuel le construit pas à pas.
- **Côté des onglets :** chaque onglet de la vue peut se placer dans l’étagère gauche ou la barre latérale droite (Preferences → Tabs → Left / Right). BoneCraft et Rig Builder commencent à gauche, CATS à droite.
- **Rig Builder :** apparaît toujours dans l’onglet Scene de Properties et possède aussi son propre onglet de la vue. Une disposition compacte s’adapte aux étagères étroites. La bibliothèque de ressources BoneCraft Rigs comprend Basic Humanoid. Fit Dropped Rig ajuste un rig déposé depuis l’étagère de ressources.
- **Onglet CATS :** Import / Export a été déplacé dans l’onglet CATS. CATS, VRChat et Import / Export sont aussi toujours dans l’onglet Scene.
- **Show Helpers :** une préférence affiche ou masque le texte pédagogique de BoneCraft. Compact Mode commande la même préférence.
- **Rig Validator :** les noms d’os avec traits d’union sont acceptés. Les pilotes n’entraînent un avertissement que pour des expressions nécessitant Python. Les vérifications couvrent aussi les rigs Mechanisms. La tâche de validation du Task Board produit de nouveau ses résultats.
- **Nom :** le complément s’appelle BoneCraft.

## 8.9.x (septembre–octobre 2026) {#89x-septemberoctober-2026}

- **8.9.6 :** la robe entière suit les os de jupe sans traverser les hanches. Les correctifs des coins de bouche à mâchoire ouverte permettent des lèvres qui restent jointives.
- **8.9.5 :** le commutateur IK/FK du coude préserve la pose sans saut. La détection des épaules est symétrique. Les repères des yeux ne sautent plus. Control Picker montre la sélection. Autres changements : coins de bouche plus arrondis, correction de robe sur la cuisse, clavicules plus détendues lors du transfert et exportation en pose en T.
- **8.9.4 :** les correctifs remplacent Preserve Volume pour des genoux plus arrondis. Cette version ajoute aussi des clés de contact pour les flexions profondes et un mélange de jonction d’épaule.
- **8.9.3 :** les os de jupe à deux segments suivent les jambes. Les jambes poussent aussi ces os.
- **8.9.2 :** des clés de forme créent les clignements sans plis de paupières. L’ouverture de bouche est ovale.
- **8.9.1 :** la pondération des maillages denses est plus rapide (678,000 sommets : de 232 s à 57 s). Bone heat utilise un proxy plus léger au lieu d’échouer silencieusement.
- **8.9.0 :** cette version ajoute des clés de forme correctives d’articulations et des contrôles faciaux de visée des yeux, clignement et suivi des lèvres. Les vêtements se plient avec les articulations.
- La version 8.9 ajoute aussi le recalcul automatique des poids d’os et une sélection d’atlas plus claire.

## 8.7–8.8 (septembre 2026) {#8788-september-2026}

- **8.8.0 :** le panneau de transfert fonctionne sur les hôtes Blender 5. Le placement des repères de doigts utilise la forme de la main. Autres changements : étirement IK jusqu’à la peau, option Preserve Volume et correction de liaison de Delta Mush.
- **8.7.0 :** cette version ajoute un rig de contrôle intégré, la détection d’articulations par suivi des membres, le transfert à directions correspondantes et les os de torsion.

## 8.5–8.6 (juillet 2026) {#8586-july-2026}

- **8.6.1–8.6.3 :** Material Atlas ajoute des diagnostics de tuiles après précalcul et un meilleur partitionnement des matériaux mélangés. Il compare la transparence MToon à l’alpha réel de la texture et la préserve pendant la création de l’atlas.
- **8.5.5–8.5.10 :** les matériaux VRM / MToon respectent le mode alpha. L’alpha fonctionne sur les hôtes Blender 5. D’autres changements empêchent une émission excessive et ajoutent des diagnostics du magenta et des noms d’atlas sûrs.
- **8.5.4 :** les mappages humanoïdes se chargent correctement. Cette version ajoute aussi les indications Naming Prep.
- **8.5.2–8.5.3 :** ces versions ajoutent l’importation des téléchargements VRoid (.zip) et une carte de transfert de projet VRoid.
- **8.5.1 :** l’exportation FBX préserve les blend shapes.

## Versions antérieures {#earlier-versions}

**8.5.0 :** après précalcul, Smart Combine définit par défaut `atlas_uv` comme UV0 à l’exportation. Sauf si **Keep Source UV Maps** est activé dans Advanced, il retire la carte UV source pré-atlas du maillage d’atlas généré. La compilation Blender ouverte partage maintenant les commandes dérivées de CATS / Material Combiner / UVToolkit. Les systèmes de production de rigging, contrôle, transfert/exportation et publication réservés à B4Artists restent exclusifs à B4Artists.

8.5.0 actualise aussi l’exportation et la validation. Les exportations VRChat, VRM, MMD et Unreal ont maintenant des commandes de dossier et de nom de fichier dans les panneaux BoneCraft. Les réglages ne dépendent plus uniquement des valeurs du navigateur de fichiers Blender. Les exportations FBX VRChat/Unity et Unreal activent **Embed Textures** par défaut pour simplifier l’importation des matériaux. Sauf si **Helper Meshes** est activé, l’exportation VRChat exclut du FBX les maillages d’aide ou de formes de contrôle. Le panneau VRM ajoute **Lint Now** et **Fix Humanoid Map**. Fix Humanoid Map corrige les alias humanoïdes périmés avant l’exportation sans renommer les os.

**8.4.5 :** pendant le précalcul, Smart Combine fait échantillonner les textures sources sur l’UV pré-atlas conservé. Il valide le maillage d’atlas généré avant de masquer les originaux. Il réaffecte toutes les faces d’atlas à l’emplacement du matériau d’atlas final. Cela évite les sections grises ou brouillées sur les robes et vêtements.

**8.4.4 :** Material Atlas Combiner ajoute des commandes d’examen avant précalcul pour conserver une qualité équivalente : diagnostics de shaders et matériaux, libellés de rôle des textures, repères de sources dupliquées ou partagées, tailles propres à chaque matériau et préréglages de rangement. Les sorties facultatives couvrent Normal/Emission/Roughness. Le contrôle préalable bloque Metallic/ORM tant que cette voie n’est pas vérifiée.

**8.4.3 :** Material Atlas Combiner ajoute des méthodes de rangement UV sélectionnables à la procédure existante : Smart Pack, Grid Pack, Seeded Variation, Oriented Pack, Fit 0-1 Bounds, Advanced Variation et Rotation Step. Le rapport de débogage et le registre de précalcul consignent les détails de la méthode UV.

**8.4.2 :** pendant le précalcul, Material Atlas Combiner cible l’UV d’atlas généré. Les nœuds de texture source copiés lisent explicitement l’UV pré-atlas. Cela corrige les erreurs d’atlas de robes et vêtements dues à l’échantillonnage de cartes UV différentes par les textures sources et l’atlas précalculé. Les lignes sélectionnables de matériaux et textures de 8.4.1 restent disponibles.

**7.1.3 (clarification des préférences) :** deux commutateurs des préférences ont des libellés correspondant à leurs onglets. « VRChat Avatar Tools » devient **CATS**, comme l’onglet CATS. « Task Board & Sidebar » devient **Rig Builder**, comme l’onglet Rig Builder. Seuls les libellés des commutateurs dans Edit > Preferences > Add-ons > BoneCraft ont changé. Aucun outil n’a été supprimé.

**7.1.1 :** BoneCraft ajoute la suite CATS complète pour nettoyer, optimiser et configurer les avatars VRChat. CATS possède son propre onglet de barre latérale. Son pipeline guide l’ordre des opérations.

Suivant : [Tutoriel : Crescent Rose avec Mechanisms](12-crescent-rose.md)
