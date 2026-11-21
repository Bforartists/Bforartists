# Outils de rig {#rig-tools}

[← Sommaire](index.md)

Ce chapitre présente les outils de rigging, d’animation et de pondération de BoneCraft. Consultez-le pour les détails des fonctions ou les situations que les guides ne couvrent pas.

Chaque entrée explique le rôle de l’outil, ses usages, ses principaux contrôles et son emplacement. La ligne « Où le trouver » indique le mode requis. Les contrôles de rig nécessitent le mode Pose. Weight Mirror et Weight Transfer nécessitent le mode Weight Paint. Delta Mush nécessite le mode Objet. Lorsqu’un outil ne peut pas s’exécuter, certaines sections restent visibles avec un message sur la sélection.

Depuis 9.1, de nombreux outils s’exécutent immédiatement et affichent leurs options dans le panneau Adjust Last Operation. Modifiez ces options juste après le clic, avant de lancer une autre opération. Les opérations courantes disposent de raccourcis dans les menus Pose → BoneCraft et Weights → BoneCraft. Les onglets Pose et Weights de l’étagère d’outils de Bforartists comportent aussi des panneaux de boutons BoneCraft. [Prise en main](01-start.md#where-things-are) répertorie ces accès.

Les illustrations montrent des exemples de rigs et de réglages. Suivez le chemin de chaque outil pour ouvrir ses contrôles.

Pour l’export vers un moteur, utilisez [Outils VRChat : Game Engine Export](08-vrchat.md#game-engine-export). Les préréglages **Bone Names** modifient les copies d’export. Leur rôle diffère de celui des outils qui renomment le rig de travail.

---

## Outils d’interface du rig {#rig-ui-tools}

Ces outils contrôlent la visibilité et l’organisation des os, ainsi que les accès rapides lorsque vous travaillez avec des armatures.

---

### Collections d’os {#bone-collections}

**Rôle :** Affiche les collections d’os du squelette sous forme de lignes. Cliquez sur le nom d’une collection pour sélectionner ses os. L’icône en forme d’œil affiche ou masque la collection.

> Une collection d’os est un groupe nommé d’os, par exemple « IK Controls », « Face Bones » ou « Deform Bones ». Masquer une collection masque ces os dans la vue, ce qui permet de se concentrer sur une partie du rig.

**Principaux contrôles :**

- Chaque ligne : couleur d’accentuation, **Toggle Collection Visibility** (icône d’œil), nom de la collection, **Solo Collection** et **Rename Collection Display**. Le nom de la collection sélectionne ses os. **Rename Collection Display** définit un nom d’affichage personnalisé pour la ligne. Pour identifier un bouton sans texte, survolez-le et lisez son infobulle
- **Show All Collections** et **Hide All Collections** (icônes d’œil ouvert et fermé au-dessus de la liste) — agissent sur toutes les collections à la fois
- Sections — regroupent plusieurs collections sous un en-tête repliable

**Où le trouver :** onglet BoneCraft → Review → Collections

Description de l’image de la source anglaise (image omise) : collections d’os et contrôles de visibilité, de sélection, d’isolement et de nom d’affichage.

*Panneau contextuel natif d’une version de test, candidat BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Collections d’os et contrôles de visibilité, de sélection, d’isolement et de nom d’affichage.*

---

### Signets de visibilité {#visibility-bookmarks}

**Rôle :** Mémorise les collections d’os visibles pour passer instantanément d’une vue enregistrée à une autre.

**Exemple d’utilisation :** « Face Only » peut mémoriser une vue des seuls os du visage pour travailler les expressions. « Full Rig » peut mémoriser une vue de tous les os pour peindre les poids. Un clic passe d’une vue enregistrée à une autre.

**Principaux contrôles :** chaque emplacement occupe une ligne.

- Le nom du signet — cliquez dessus pour appliquer la vue enregistrée
- **Save Bookmark** — enregistre la visibilité actuelle dans l’emplacement. Survolez son icône pour voir l’infobulle
- L’échantillon de couleur — attribue un code couleur au signet
- **Clear Bookmark** et **Remove Bookmark** (icônes de fermeture) — vident l’emplacement ou suppriment un emplacement ajouté
- **Add Bookmark** — ajoute un emplacement

**Signets par défaut :** FK Arms, IK Body, Face Only, Full Rig

**Où le trouver :** onglet BoneCraft → Review → Collections → Visibility Bookmarks

Description de l’image de la source anglaise (image omise) : Visibility Bookmarks avec une vue Full Rig enregistrée et trois emplacements disponibles.

*Panneau contextuel natif d’une version de test, candidat BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Visibility Bookmarks avec une vue Full Rig enregistrée et trois emplacements disponibles.*

---

### Panneau rapide par raccourci {#hotkey-quick-panel}

**Rôle :** Ouvre le panneau de rig de BoneCraft (collections et signets) dans une fenêtre contextuelle à la position du pointeur.

**Utilisation :**

1. Dans la vue 3D, appuyez sur **Ctrl+Shift+R**.
2. Pour fermer la fenêtre contextuelle, cliquez à l’extérieur.

**Où le trouver :** raccourci **Ctrl+Shift+R** dans la vue 3D (il n’a pas de panneau distinct)

Le panneau rapide utilise les [contrôles de signets illustrés ci-dessus](#visibility-bookmarks).

---

## Outils d’animation {#animation-tools}

---

### Bibliothèque de poses {#pose-library}

**Rôle :** Conserve des poses nommées avec des miniatures, que vous pouvez appliquer au rig en un clic.

**Principaux contrôles :**

- **Save** — enregistre la position actuelle des os comme pose nommée, avec une miniature de la vue
- **Apply** — place les os dans la pose enregistrée
- **Blend** — applique partiellement la pose en la mélangeant avec la position actuelle
- **Mirror** — applique la pose en inversant gauche et droite
- **Delete**, **Rename** et **Category** — gèrent la liste. **Filter** affiche une catégorie
- **Export** et **Import** — enregistrent dans un fichier `.bfpose` ou chargent son contenu

Blend s’applique immédiatement. Après avoir cliqué sur Blend, réglez l’intensité du mélange dans Adjust Last Operation.

**Où le trouver :** onglet BoneCraft → Review → Pose Library

Description de l’image de la source anglaise (image omise) : une pose d’exemple enregistrée affiche Apply, Mirror, Blend et les contrôles de la bibliothèque.

*Panneau contextuel natif, BoneCraft 9.2.18. Une pose d’exemple enregistrée affiche Apply, Mirror, Blend et les contrôles de la bibliothèque.*

---

### Sélecteur de contrôles {#control-picker}

**Rôle :** Présente une carte cliquable des contrôles du rig. Cliquez sur une forme pour sélectionner son os. Le sélecteur met en surbrillance les contrôles sélectionnés.

**Principaux contrôles :**

- **Generate Picker** — construit la disposition à partir du rig
- **Edit Layout** — modifie la disposition. La ligne de chaque contrôle comporte des icônes **Move Picker Control**, **Resize Picker Control** et **Relabel Picker Control**. **Snap** aligne les contrôles sur une grille. **Rebuild Layout** reconstruit la disposition
- **Mirror Selection** — sélectionne les contrôles symétriques
- **Pop-up Picker** — ouvre le sélecteur dans une fenêtre flottante, qui propose aussi **Add Selection Set**

**Où le trouver :** onglet BoneCraft → Review → Control Picker

Description de l’image de la source anglaise (image omise) : le Control Picker généré montre des contrôles d’exemple, la modification de la disposition, la sélection symétrique et l’action d’ouverture du sélecteur contextuel.

*Panneau contextuel natif, BoneCraft 9.2.18. Le Control Picker généré montre des contrôles d’exemple, la modification de la disposition, la sélection symétrique et l’action d’ouverture du sélecteur contextuel.*

---

### Couche de contrôle (IK/FK) {#control-layer-ikfk}

Pour une comparaison pratique écrite, suivez [Tester les poids et utiliser IK/FK](06-rig-builder.md#part-c-test-weights-and-use-ikfk).

**Rôle :** Contrôle les membres d’un rig créé par **Build Control Rig**. Permet de faire passer un membre d’IK à FK sans saut de pose. Convertit aussi l’animation IK en FK, ou FK en IK, sur une plage d’images.

**Principaux contrôles :**

- **IK** et **FK** — changent le mode du membre et ajustent les nouveaux contrôles à sa position actuelle. Le coude ou le genou ne saute pas
- **Bake IK** et **Bake FK** — convertissent l’animation d’une plage d’images en IK ou en FK
- **Pole Follow**, **Pin** et **Lock-Free**, ainsi que **Global Rig Scale**, qui conserve les verrouillages protégés

**Où le trouver :** onglet BoneCraft → Review → Control Layer (avec un rig créé par **Build Control Rig** sélectionné ; voir [Constructeur de rigs](06-rig-builder.md))

Description de l’image de la source anglaise (image omise) : Control Layer montre les boutons IK/FK des membres, les actions de conversion et les réglages du rig.

*Capture historique de l’atelier. Control Layer montre les boutons IK/FK des membres, les actions de conversion et les réglages du rig.*

---

### Outils Rigify {#rigify-tools}

**Rôle :** Détecte un rig de contrôle Rigify et relie le panneau de collections, les signets et les curseurs de propriétés de BoneCraft aux contrôles standard de Rigify.

> Rigify est le système intégré de Bforartists qui génère des rigs prêts pour l’animation. Si vous avez créé le rig avec Rigify, cette fonction relie l’interface de BoneCraft aux contrôles IK/FK de Rigify.

**Principaux contrôles :**

- **Auto-Enhance** — configure les panneaux de BoneCraft pour le rig Rigify sélectionné
- **Re-run Enhancement** — les reconstruit à partir de zéro
- **Enable Rigify** se trouve dans Quick Rig. Sa section Troubleshooting contient **Generate Control Rig (active metarig)** (voir [Constructeur de rigs](06-rig-builder.md))
- Rigify Properties — curseurs IK/FK, d’étirement, d’espace parent et de suivi tête/cou du rig

**Où le trouver :** onglet BoneCraft → Setup Rigging → Rigify Tools (et section Rigify Properties)

Description de l’image de la source anglaise (image omise) : Rigify Tools montre l’accès à l’amélioration du rig. Sélectionnez un rig Rigify généré pour utiliser les contrôles applicables.

*Panneau contextuel natif, BoneCraft 9.2.18. Rigify Tools montre l’accès à l’amélioration du rig. Sélectionnez un rig Rigify généré pour utiliser les contrôles applicables.*

---

### Transfert d’animation {#retarget}

**Rôle :** Transfère l’animation entre squelettes, par exemple un clip de capture de mouvement vers votre avatar. Associe les os selon leur nom et leur direction pour préserver l’orientation des membres. Une association souple des clavicules évite une rotation excessive des épaules.

**Principaux contrôles :**

- **Import Clip** et **Browse Library** — chargent un clip ou définissent un dossier de bibliothèque. Cliquez sur le nom d’un clip pour le sélectionner
- **Auto-Match Bones** (coche sur la ligne d’un clip) — associe les os source et cible. La liste Bone Mapping montre les paires
- **Preview** et **Stop Preview** — permettent d’essayer le résultat
- **Apply** — convertit le clip en clés sur votre rig

**Où le trouver :** onglet BoneCraft → Setup Rigging → Retarget

Description de l’image de la source anglaise (image omise) : Retarget commence par Import Clip et Browse Library. La correspondance des os du clip et la prévisualisation apparaissent après le chargement d’un clip.

*Panneau contextuel natif, BoneCraft 9.2.18. Retarget commence par Import Clip et Browse Library. La correspondance des os du clip et la prévisualisation apparaissent après le chargement d’un clip.*

---

### Clés de forme correctives {#corrective-shape-keys}

**Rôle :** Des clés de forme qui s’activent lorsqu’un os atteint un angle donné, pour corriger les pincements ou les affaissements dans les poses extrêmes.

**Exemple d’utilisation :** Le coude du personnage s’affaisse lorsqu’il est complètement plié. Une correction sculptée du coude, liée à l’os du bras, s’applique automatiquement à mesure que le coude se plie.

**Principaux contrôles :**

- New Corrective — réglages de **Shape Key**, **Driver Bone**, de l’axe de rotation, de l’angle de pleine intensité et de l’apparition progressive
- Liste des correctifs — **Edit** et **Delete**, sous la liste, agissent sur le correctif sélectionné

Le maillage enfant de l’armature doit posséder une clé de forme de base. Sélectionnez l’armature pour afficher New Corrective. Son maillage enfant fournit les clés de forme.

Pour créer un correctif :

1. Sélectionnez **Shape Key**.
2. Sélectionnez **Driver Bone**.
3. Sélectionnez l’axe de rotation.
4. Réglez l’angle auquel la forme atteint sa pleine intensité.
5. Réglez la progressivité de son apparition.
6. Sélectionnez **Create Corrective**.

Pour sélectionner un correctif existant, cliquez sur le nom de sa clé de forme dans la liste.

Edit part des valeurs actuelles du correctif. Après avoir cliqué sur Edit :

1. Dans Adjust Last Operation, modifiez l’angle.
2. Modifiez l’atténuation.

**Où le trouver :** onglet BoneCraft → Skin → Correctives (le maillage doit posséder une clé de forme de base)

Description de l’image de la source anglaise (image omise) : sélectionnez l’armature pour afficher New Corrective. Son maillage enfant fournit les clés de forme.

*Panneau contextuel natif, BoneCraft 9.2.18. Sélectionnez l’armature pour afficher New Corrective. Son maillage enfant fournit les clés de forme.*

---

### Outils de courbes {#graph-tools}

**Rôle :** Outils de finition de l’animation pour les images clés et les courbes.

- **Interactive Breakdown** (Breakdowner) — mélange la pose actuelle entre les images clés les plus proches lorsque vous faites glisser vers la gauche ou la droite. Son raccourci dans la vue 3D est **Ctrl+Shift+B**
- **Apply Delta** (Delta Mover) — décale les os sélectionnés d’une quantité exacte dans l’espace écran ou l’espace monde. Son raccourci dans la vue 3D est **Ctrl+Shift+D**
- **Capture** et **Swap** (Buffer Curves) — conservent une copie des courbes et permettent de basculer entre cette copie et vos modifications
- **Smart Bake** — convertit l’animation pilotée par contraintes en clés et supprime les clés redondantes (**Tol** règle la tolérance)
- **Euler Filter** — corrige les retournements de rotation provoqués par le verrouillage de cardan
- Tangent Handles — définit le type de poignées des clés sélectionnées : **Auto**, **Vector**, **Aligned**, **Free** ou **Auto Clamped**

**Où le trouver :** onglet BoneCraft → Review → Graph Tools

Description de l’image de la source anglaise (image omise) : Interactive Breakdown lance un glissement sur les os de pose sélectionnés.

*Panneau contextuel natif, BoneCraft 9.2.18. Interactive Breakdown lance un glissement sur les os de pose sélectionnés.*

Description de l’image de la source anglaise (image omise) : Apply Delta et ses options de décalage.

*Panneau contextuel natif, BoneCraft 9.2.18. Apply Delta et ses options de décalage.*

Description de l’image de la source anglaise (image omise) : Buffer Curves, Euler Filter et Smart Bake. La section Options est fermée.

*Panneau contextuel natif, BoneCraft 9.2.18. Buffer Curves, Euler Filter et Smart Bake. La section Options est fermée.*

Description de l’image de la source anglaise (image omise) : Tangent Handles propose Auto, Vector, Aligned, Free et Auto Clamped.

*Panneau contextuel natif, BoneCraft 9.2.18. Tangent Handles propose Auto, Vector, Aligned, Free et Auto Clamped.*

---

## Outils de poids {#weight-tools}

Ces outils contrôlent la déformation du maillage lorsque les os bougent. Les poids indiquent à chaque partie du maillage quels os suivre et dans quelle proportion.

---

### Recalcul automatique des poids des os {#automatic-bone-weight-recalculation}

**Rôle :** Recalcule les poids d’un maillage à partir du rig existant, sans modifier le maillage. Pour les maillages denses, utilise un maillage proxy plus léger afin de ne pas échouer silencieusement.

**Principaux contrôles :** Body calcule les poids à partir du rig existant. Clothing transfère les poids depuis un maillage source correctement pondéré. Les réglages se trouvent au-dessus du bouton.

1. Dans **Mesh to Reweight**, sélectionnez le maillage cible.
2. Dans **Existing Armature**, sélectionnez l’armature.
3. Sélectionnez le mode Body ou Clothing.

Pour le mode Body, sélectionnez la méthode.

Pour le mode Clothing :

1. Dans **Weighted Body**, sélectionnez le maillage source correctement pondéré.
2. Sélectionnez la méthode.

Pour les deux modes :

1. Réglez le mélange.
2. Réglez le lissage.
3. Réglez le nombre maximal d’influences d’os par sommet.
4. Réglez le poids minimal.
5. Choisissez de conserver ou non une sauvegarde.
6. Sélectionnez **Automatic Bone Weight Recalculation**.

Le raccourci CATS **Smart Automatic Weights** ouvre une boîte de dialogue pour le maillage cible, l’armature et le mode. En mode Clothing, elle contient aussi le maillage source.

**Où le trouver :** onglet BoneCraft → Skin → Weight Tools

Description de l’image de la source anglaise (image omise) : réglages d’Automatic Bone Weight Recalculation avec le maillage et l’armature d’exemple sélectionnés.

*Panneau contextuel natif d’une version de test, candidat BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Réglages d’Automatic Bone Weight Recalculation avec le maillage et l’armature d’exemple sélectionnés.*

---

### Symétrie des poids {#weight-mirror}

**Rôle :** Copie les poids d’un côté de l’avatar vers l’autre. À utiliser pour les personnages symétriques.

**Principaux contrôles :**

- **Mirror All Weights** — copie par symétrie chaque groupe d’os vers le côté opposé
- **Mirror Active Weight** — copie par symétrie uniquement le groupe d’os actif
- **Axis** et **Direction** — choisissent l’axe de réflexion et le côté qui fournit les poids
- **Search Distance** — distance autorisée entre la position réfléchie d’un sommet et son correspondant spatial
- **Select Unmatched** — sélectionne les sommets sans correspondant. **Normalize Weights** ramène ensuite la somme des poids à 1.0

La symétrie utilise les positions spatiales, pas la topologie du maillage.

1. Cliquez sur un bouton de symétrie.
2. Dans Adjust Last Operation, sélectionnez **Axis**.
3. Sélectionnez **Direction**.
4. Réglez **Search Distance**.

**Mirror Active Weight** se trouve aussi dans Weights → BoneCraft et dans l’onglet Weights de l’étagère d’outils.

**Où le trouver :** onglet BoneCraft, en mode Weight Paint → Weight Mirror

Description de l’image de la source anglaise (image omise) : actions Weight Mirror. Après le clic, définissez l’axe dans Adjust Last Operation. Réglez-y les options de recherche.

*Panneau contextuel natif, BoneCraft 9.2.18. Actions Weight Mirror. Après le clic, définissez l’axe dans Adjust Last Operation. Réglez-y les options de recherche.*

---

### Transfert des poids {#weight-transfer}

**Rôle :** Copie les poids d’un maillage source vers le maillage actif. Sert à attacher des vêtements à un corps ou à transférer les poids d’un maillage haute résolution vers un maillage moins détaillé.

**Principaux contrôles :** **Normalize**, dans Adjust Last Operation, maintient la somme des poids à 1.0. **Select Problem Vertices** sélectionne les sommets dont la correspondance est médiocre.

Gardez le maillage cible actif en mode Weight Paint.

1. Dans **Source Mesh**, sélectionnez le maillage source.
2. Cliquez sur **Transfer Weights**.
3. Dans Adjust Last Operation, sélectionnez la méthode de transfert.
4. Sélectionnez le filtre d’os.

Le résultat affiche la distance moyenne et la distance maximale.

**Où le trouver :** onglet BoneCraft, en mode Weight Paint → Weight Transfer (aussi sous Skin → Weight Tools)

Description de l’image de la source anglaise (image omise) : choisissez une Source Mesh avant Transfer Weights. Les champs de distance restent à leurs valeurs initiales dans cet exemple.

*Panneau contextuel natif, BoneCraft 9.2.18. Choisissez une Source Mesh avant Transfer Weights. Les champs de distance restent à leurs valeurs initiales dans cet exemple.*

---

### Tableau des poids {#weight-table}

**Rôle :** Affiche le poids exact du sommet sélectionné pour chaque os. Vous pouvez définir des valeurs précises.

**Utilisation :**

1. Passez en mode Weight Paint.
2. Activez le **masquage par sélection de sommets**.
3. Sélectionnez un sommet.

Le tableau répertorie les os et les poids du sommet sélectionné.

4. Cliquez sur l’icône de main de la ligne d’un os.
5. Dans Adjust Last Operation, réglez **Weight**.

Add Influence utilise l’os que vous sélectionnez. Après Add Influence, réglez aussi son nouveau poids dans Adjust Last Operation. Si plusieurs sommets sont sélectionnés, **Normalize All Vertices** normalise tous les sommets sélectionnés.

**Où le trouver :** onglet BoneCraft, en mode Weight Paint → Weight Table

Description de l’image de la source anglaise (image omise) : Weight Table avec plusieurs sommets sélectionnés. Sélectionnez un seul sommet pour modifier les poids en détail.

*Panneau contextuel natif, BoneCraft 9.2.18. Weight Table avec plusieurs sommets sélectionnés. Sélectionnez un seul sommet pour modifier les poids en détail.*

---

### Remplissage global {#flood-fill}

**Rôle :** Modifie les poids du groupe de sommets actif sur tout le maillage, y compris les sommets non sélectionnés.

Avant toute action Flood Fill :

1. Sélectionnez le maillage.
2. Passez en mode Weight Paint.
3. Rendez actif le groupe de sommets voulu.

**Actions :**

- **Flood to 0.0** retire les poids positifs attribués au groupe actif sur tout le maillage. Les autres groupes de sommets restent inchangés.
- **Flood to 1.0** attribue 1.0 au groupe actif sur chaque sommet. Pour chaque sommet, supprime les autres poids positifs si leur total dépasse 1e-6.
- **Flood to Custom** attribue une **Value** positive au groupe actif sur chaque sommet. Avec **Normalize** activé, normalise aussi les poids de tout le maillage. Une **Value** de 0 n’effectue aucune attribution ni normalisation. Pour effacer les poids, utilisez **Flood to 0.0**.

Le menu et l’étagère Weights nomment les boutons à valeur fixe Flood to Zero et Flood to One.

Pour un remplissage personnalisé :

1. Sélectionnez **Flood to Custom**.
2. Juste après, réglez **Value** dans Adjust Last Operation.
3. Activez ou désactivez **Normalize**.

**Où le trouver :** en mode Weight Paint : onglet BoneCraft → Skin → Weight Tools ; aussi Weights → BoneCraft et Tool Shelf → Weights → BoneCraft

Description de l’image de la source anglaise (image omise) : actions Flood Fill. Après le clic, réglez la valeur personnalisée dans Adjust Last Operation.

*Panneau contextuel natif, BoneCraft 9.2.18. Actions Flood Fill. Après le clic, réglez la valeur personnalisée dans Adjust Last Operation.*

---

### Os de déformation et de contrôle {#deform-vs-control}

**Rôle :** Sépare les os de déformation des os de contrôle. Les os de déformation déplacent le maillage. L’animateur déplace les os de contrôle. L’outil identifie les os de déformation et les renomme selon une nomenclature de déformation. Il exporte aussi un squelette de déformation uniquement.

**Où le trouver :** onglet BoneCraft, en mode Pose → Deform vs Control

Description de l’image de la source anglaise (image omise) : listes Deform et Control sur le rig d’exemple. Ce rig comporte 19 os de déformation et aucun os de contrôle.

*Panneau contextuel natif d’une version de test, candidat BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Listes Deform et Control sur le rig d’exemple. Ce rig comporte 19 os de déformation et aucun os de contrôle.*

---

### Delta Mush {#delta-mush}

**Rôle :** Déformation avec lissage qui réduit les pincements aux articulations. Le maillage conserve sa forme au repos, mais se déforme plus proprement en mouvement.

**Utilisation :** Ces actions nécessitent le mode Objet et un maillage actif.

1. Cliquez sur **Add Delta Mush**.

L’outil ajoute le modificateur et le lie à la forme de repos. Juste après cette opération, ajustez ses options :

2. Dans Adjust Last Operation, réglez **Iterations**.
3. Réglez **Smooth Strength**.
4. Activez ou désactivez **Pin Borders**.
5. Activez ou désactivez **Only Smooth Deform**.

Une fois le modificateur présent, le panneau affiche **Rebind** et **Remove**. Sa section Settings contient les contrôles d’itérations, d’intensité du lissage et de fixation des bords du modificateur.

**Où le trouver :** BoneCraft → Skin → Delta Mush (mode Objet ; Mesh)

Description de l’image de la source anglaise (image omise) : Add Delta Mush lance la configuration. Ajustez ses options juste après le clic.

*Panneau contextuel natif, BoneCraft 9.2.18. Add Delta Mush lance la configuration. Ajustez ses options juste après le clic.*

---

### Déformation par proximité {#proximity-wrap}

**Rôle :** Fait suivre à un maillage la surface d’un autre, comme une seconde peau. Utile pour les vêtements près du corps.

**Utilisation :** Ces actions nécessitent le mode Objet et un maillage cible actif. Gardez l’armature du maillage pilote dans sa pose de repos lors de la liaison.

1. Sélectionnez le maillage cible.
2. Sélectionnez un autre **Driver Mesh**.
3. Cliquez sur **Bind Proximity Wrap**.

La section Options sous le bouton contient **Falloff Type** et **Max Distance**. Dans 9.1.2, la configuration enregistre ces valeurs, mais elles ne modifient pas sa liaison Surface Deform. Après la liaison, le panneau affiche **Rebind** et **Unbind**. Unbind désactive le modificateur dans la vue et au rendu. Il ne supprime pas le modificateur.

**Où le trouver :** BoneCraft → Skin → Proximity Wrap (mode Objet ; Mesh)

Description de l’image de la source anglaise (image omise) : choisissez un Driver Mesh avant Bind Proximity Wrap. La section Options est fermée.

*Panneau contextuel natif, BoneCraft 9.2.18. Choisissez un Driver Mesh avant Bind Proximity Wrap. La section Options est fermée.*

---

## Contrôles du rig {#rig-controls}

Ces outils apparaissent dans l’onglet BoneCraft en mode Pose.

---

### Changement d’espace {#space-switch}

**Rôle :** Change l’espace qu’un os suit pendant l’animation. Une main tenant un accessoire peut passer du suivi du corps à une position fixe dans le monde en un clic.

**Principaux contrôles :**

- **Add Space** et **Remove Space** (icône X sous Manage Spaces) — espaces qu’un os peut suivre (World, Origin ou un autre os)
- Un bouton par espace, portant le nom de cet espace. L’espace actuel porte une marque ●. Pour changer l’espace de l’os, cliquez sur le bouton d’un autre espace

**Où le trouver :** onglet BoneCraft, en mode Pose → Space Switch

Description de l’image de la source anglaise (image omise) : Space Switch avant la définition d’un espace. Add Space lance la configuration.

*Panneau contextuel natif, BoneCraft 9.2.18. Space Switch avant la définition d’un espace. Add Space lance la configuration.*

---

### IK sur courbe {#spline-ik}

**Rôle :** Fait suivre une courbe à une chaîne d’os. Sert pour les queues, tentacules, cordes, cheveux longs et colonnes vertébrales qui nécessitent des mouvements amples et fluides.

**Utilisation :**

1. Rendez actif l’os de départ.
2. Cliquez sur **Generate Spline IK**.
3. Dans Adjust Last Operation, réglez **Chain Length**.
4. Réglez **Curve Resolution**.
5. Réglez **Stretch**.
6. Réglez **Volume Preservation**.

**Remove Spline IK** supprime la configuration.

**Où le trouver :** onglet BoneCraft, en mode Pose → Spline IK

Description de l’image de la source anglaise (image omise) : actions Spline IK. Réglez les options de chaîne dans Adjust Last Operation après la génération.

*Panneau contextuel natif, BoneCraft 9.2.18. Actions Spline IK. Réglez les options de chaîne dans Adjust Last Operation après la génération.*

---

### Dynamique de chaîne {#chain-dynamics}

**Rôle :** Ajoute un mouvement secondaire de type physique à une chaîne d’os. Les os prennent du retard sur un parent en mouvement et rebondissent lorsqu’il s’arrête. Convient notamment aux mèches de cheveux, aux queues et aux accessoires.

**Utilisation :**

1. Sélectionnez la chaîne d’os.
2. Cliquez sur **Add Chain Dynamics**.
3. Dans Adjust Last Operation, réglez **Stiffness**.
4. Réglez **Damping**.
5. Réglez **Mass**.
6. Réglez **Gravity Scale**.

La section Settings sous l’action présente aussi ces paramètres. Une fois la dynamique présente, le panneau affiche **Bake** et **Remove**. Les collisions utilisent une forme sphérique simplifiée ; les surfaces concaves peuvent donc ne pas entrer correctement en collision.

**Où le trouver :** onglet BoneCraft, en mode Pose → Chain Dynamics

Description de l’image de la source anglaise (image omise) : Add Chain Dynamics lance la configuration. Dépliez Settings pour accéder à ses paramètres.

*Panneau contextuel natif, BoneCraft 9.2.18. Add Chain Dynamics lance la configuration. Dépliez Settings pour accéder à ses paramètres.*

---

### Ruban {#ribbon}

**Rôle :** Construit un ruban de Bendy Bones — des os qui se courbent et se tordent progressivement — pour les lèvres, sourcils, ceintures et autres zones souples et courbes.

**Utilisation :**

1. Sélectionnez la chaîne d’os.
2. Cliquez sur **Generate Ribbon**.
3. Dans Adjust Last Operation, réglez **Control Bones**.
4. Réglez **Ribbon Width**.

**Remove Ribbon** supprime la configuration.

**Où le trouver :** onglet BoneCraft, en mode Pose → Ribbon

Description de l’image de la source anglaise (image omise) : actions Ribbon et longueur de chaîne. Ajustez le ruban généré juste après le clic.

*Panneau contextuel natif, BoneCraft 9.2.18. Actions Ribbon et longueur de chaîne. Ajustez le ruban généré juste après le clic.*

---

### Bibliothèque de visèmes {#viseme-library}

**Rôle :** Crée et gère des jeux de visèmes (formes de bouche) liés à des clés de forme. Génère aussi des clés de synchronisation labiale à partir d’un texte. Pour l’association des visèmes VRChat, utilisez VRChat Viseme Mapping. Pour générer de nouveaux visèmes, utilisez la section CATS Visemes.

**Principaux contrôles :**

- **New Set** et **Delete** — créent ou suppriment un jeu de visèmes
- Dans chaque jeu, un bouton par visème (avec une icône de haut-parleur) permet de le prévisualiser
- Lip Sync — conversion du texte en clés de visèmes, avec un nombre d’images par phonème et un lissage

**Où le trouver :** CATS → Avatar Tools → Viseme Library (Armature) ; Lip Sync (mode Pose)

Description de l’image de la source anglaise (image omise) : Viseme Library commence par New Set. Passez en mode Pose pour utiliser Lip Sync.

*Panneau contextuel natif, BoneCraft 9.2.18. Viseme Library commence par New Set. Passez en mode Pose pour utiliser Lip Sync.*

Description de l’image de la source anglaise (image omise) : texte Lip Sync et Generate Lip Sync. Dépliez Options pour les réglages de rythme et de lissage.

*Panneau contextuel natif, BoneCraft 9.2.18. Texte Lip Sync et Generate Lip Sync. Dépliez Options pour les réglages de rythme et de lissage.*

---

### Clé pilotée {#set-driven-key}

**Rôle :** Relie une valeur de transformation d’un os à une autre sans expression Python. Par exemple, déplacer un os de contrôle selon X peut faire monter un os cible selon Z. Ce panneau crée des cibles de transformation d’os.

1. Sélectionnez **Driver Bone**.
2. Sélectionnez **Driver Attribute**.
3. Sélectionnez **Target Bone**.
4. Sélectionnez **Target Attribute**.
5. Posez les os.
6. Enregistrez chaque point.
7. Sélectionnez **Create SDK**.

**Principaux contrôles :**

- **Driver Bone** et **Driver Attribute** — ce qui pilote
- **Target Bone** et **Target Attribute** — ce qui est piloté
- **Set Value** et **Record Point** — enregistrent un point sur la courbe
- **Create SDK** — crée le pilote

**Où le trouver :** onglet BoneCraft, en mode Pose → Set Driven Key

Description de l’image de la source anglaise (image omise) : choisissez les os pilote et cible avant d’enregistrer un point de clé pilotée. Ces champs ne sont pas renseignés dans l’exemple.

*Panneau contextuel natif, BoneCraft 9.2.18. Choisissez les os pilote et cible avant d’enregistrer un point de clé pilotée. Ces champs ne sont pas renseignés dans l’exemple.*

---

### Validation du rig {#rig-validator}

**Rôle :** Vérifie le rig selon un ensemble de règles et signale les problèmes. Les vérifications portent sur les noms, les os manquants, les contraintes rompues, la hiérarchie, les poids, les pilotes nécessitant Python et les règles de Mechanisms. Les noms d’os avec des traits d’union (comme `DEF-upper_arm.L`) sont acceptés.

**Principaux contrôles :**

- **Run Validation** — lance toutes les vérifications et répertorie les résultats
- **Export Report** — enregistre les résultats dans un fichier

Le Task Board (onglet BoneCraft → Overview → Task Board) affiche une tâche de validation lorsqu’une vérification échoue.

**Où le trouver :** onglet BoneCraft → Review → Rig Validator

Description de l’image de la source anglaise (image omise) : la validation signale un avertissement sur les collections. Comme le rig d’exemple n’a pas de maillage enfant, la validation ignore la vérification des poids.

*Panneau contextuel natif d’une version de test, candidat BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. La validation signale un avertissement sur les collections. Comme le rig d’exemple n’a pas de maillage enfant, la validation ignore la vérification des poids.*

---

### Notes du rig {#rig-notes}

**Rôle :** Notes écrites attachées aux os du rig : configuration effectuée, rappels, notes destinées aux collaborateurs.

**Principaux contrôles :** **Add Note**, et **Remove** sur chaque note. Rig Readme affiche les notes du rig dans une page en lecture seule.

**Où le trouver :** onglet BoneCraft → Overview → Rig Notes, et Review → Rig Readme

Description de l’image de la source anglaise (image omise) : une note attachée à Hips en mode Pose. Add Note crée une annotation. Remove supprime cette annotation.

*Panneau contextuel natif d’une version de test, candidat BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Une note attachée à Hips en mode Pose. Add Note crée une annotation. Remove supprime cette annotation.*

Suivant : [Constructeur de rigs](06-rig-builder.md)
