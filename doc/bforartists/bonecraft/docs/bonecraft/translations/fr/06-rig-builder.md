# Rig Builder {#rig-builder}

[← Sommaire](index.md)

Pour une démonstration commentée des deux types de rigs, consultez la [découverte de l’IK/FK pour débutants et le fichier d’exercice](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

## Construire un nouveau rig {#building-a-new-rig}

Rig Builder crée un rig pour un personnage. Son onglet **Rig Builder** se trouve dans l’étagère d’outils de gauche. Appuyez sur **T** pour l’afficher. Lorsque Preferences → Tabs → Scene Properties → Show est activé, Rig Builder apparaît aussi dans l’onglet **Scene** de l’éditeur **Properties**. Une étagère étroite utilise une disposition compacte aux libellés courts. Auto-Rig Wizard vient en premier, suivi de Quick Rig et de Mannequin. Le menu Add → Armature de la vue propose aussi l’assistant et Quick Rig.

---

### Auto-Rig Wizard {#auto-rig-wizard}

**Fonction :** un assistant pas à pas qui place des repères sur votre maillage et construit à partir d’eux un rig complet avec ses poids. C’est la méthode principale pour créer le rig d’un personnage à partir de zéro.

Le [guide 1](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat) détaille la procédure.

**Étapes :** Select Mesh → Rig Type → Body Markers → Finger Markers → Face Markers → Review → Generate

**Commandes principales :**

- **Start Auto-Rig** ouvre l’assistant. **Back** et **Cancel** se trouvent en haut. **Next** est en bas des étapes de choix du maillage, du type de rig et des repères. À l’étape Review, **Generate Rig** remplace Next. La dernière étape propose **Close Wizard**
- La liste des maillages : cliquez sur votre maillage. L’étape suivante propose **Body + Face**, **Body Only** ou **Face Only** (pour une armature existante)
- **Detect Markers** (dans Smart Detection) suit les membres du maillage et place tous les repères du corps avec un niveau de confiance. **Accept High** conserve ceux à forte confiance. **Reset Low** efface ceux à faible confiance
- **Guess Markers from Mesh** et **Guess Precision** pour le corps, **Guess Finger Markers** pour les doigts (placés d’après la forme de la main) et **Guess Face Markers** pour le visage
- Finger Detail : nombre de doigts à construire, de « 0 — No Fingers » à « 5 — Full Human Hand »
- Sur la ligne de chaque repère : **Place Marker** (flèche), **Confirm Marker** (coche) et **Reset Marker** (flèche circulaire). Les repères gauche et droit possèdent aussi **Toggle Symmetry** comme première icône
- **Mirror L to R** et **Mirror R to L** copient les repères confirmés de l’autre côté de l’axe central
- **Confirm All Placed** confirme chaque repère placé de l’étape
- **Generate Rig** construit le rig à partir des repères confirmés. La dernière étape propose **Build Control Rig** (voir ci-dessous) et **Close Wizard**

**Ce que construit Generate Rig :**

- Un rig de corps avec les segments de colonne et de cou choisis, et des bras et jambes en IK/FK, IK seule ou FK seule (option **Kinematics**)
- Les os des doigts selon le nombre de doigts choisi
- Pour **Body + Face** : un rig facial, avec des formes de contrôle si **Generate Control Shapes** est activé
- Les poids de déformation à la qualité choisie. Les maillages denses sont pondérés à travers un proxy plus léger : un personnage de 678,000 sommets prend ainsi environ une minute au lieu d’échouer silencieusement.

**Build Control Rig :** l’étape Review montre aussi **Twist Bones**, **Skirt Bones**, **Face Controls** et **Joint Correctives**. Generate Rig n’applique pas ces options. Elles appartiennent au rig de contrôle du moteur. Celui-ci comprend des os de torsion, des os de jupe qui suivent les jambes, la visée des yeux, des commandes de clignement et des clés de forme correctives des articulations. Après Generate Rig, la dernière étape propose **Build Control Rig**. Cette commande construit le rig de contrôle sur l’armature générée avec les options choisies. Avant **Close Wizard**, cliquez sur **Build Control Rig** : fermer l’assistant réinitialise ses options. Le panneau Control Layer (Rig Tools) n’apparaît que sur un rig construit de cette manière.

**Emplacement :** Rig Builder → Auto-Rig Wizard

**Placer plusieurs repères avec l’outil de la vue :**

1. Lancez l’assistant.
2. Avancez jusqu’à une étape de repères du corps, des doigts ou du visage.
3. En mode Objet, activez Place Rig Markers dans la barre d’outils de la vue.

L’en-tête de l’outil nomme le prochain repère non confirmé et montre les verrouillages d’axes et le commutateur de miroir.

4. Cliquez sur le maillage de l’assistant pour placer et confirmer ce repère.
5. Lorsque l’outil indique que l’étape est terminée, appuyez sur **Next** dans l’assistant.

La symétrie suit les réglages de l’assistant. Les boutons Place propres à chaque repère restent utilisables. Cliquer ailleurs ne place aucun repère.

---

### Quick Rig {#quick-rig}

**Fonction :** ajoute en un clic le Basic Humanoid de BoneCraft ou l’un des métarigs de Rigify. Basic Humanoid possède 19 os et ne nécessite pas Rigify. Quick Rig est plus rapide que l’assistant, mais moins adapté au maillage.

**Commandes principales :**

- Le bouton Basic Humanoid et les métarigs Rigify. Pour un préréglage Rigify lorsque Rigify est désactivé, sélectionnez d’abord **Enable Rigify**
- Un bouton de rig ajoute immédiatement ce rig. Adjust Last Operation contient l’ajustement, les poids automatiques, **Add IK/FK Controllers** et **Initial Pose**
- **T-Pose** et **A-Pose** changent la pose de repos du rig sélectionné
- Dépliez Troubleshooting pour **Diagnose Quick Rig (print to console)**. Si une armature qui n’est pas un métarig est active, **Inspect Active Rig Controls** apparaît aussi
- Si un métarig Rigify est actif, Troubleshooting montre **Generate Control Rig (active metarig)** au lieu de Inspect Active Rig Controls. Cette commande génère le rig de contrôle Rigify

**Le catalogue de départ BoneCraft Rigs :** les neuf rigs de départ fournis partagent le catalogue **Starter Rigs** dans l’étagère de ressources native du bas.

1. Ouvrez le menu des catalogues à gauche de l’étagère.
2. Sélectionnez toutes les bibliothèques avec **All**.
3. Activez une fois **Starter Rigs** pour ajouter son onglet à côté des onglets de catalogues existants.
4. Sélectionnez cet onglet pour parcourir les rigs de départ.

**Add → Armature → Starter Rig Catalog** ouvre la fenêtre d’ajustement et d’ajout d’un rig de départ qui prend les dépendances en compte.

Basic Humanoid ne nécessite pas Rigify. Les autres vignettes portent le libellé **Rigify**. Si Rigify est inactif, sélectionner ou déposer l’un de ces rigs dans la fenêtre du catalogue propose **Enable Rigify & Add Rig** et Cancel. Accepter active le Rigify installé et poursuit avec ce rig de départ. Annuler n’ajoute rien. **Quick Rig** propose aussi **Enable Rigify**. Le menu contextuel du catalogue le propose lorsque Rigify n’est pas disponible. Une dépendance ou un préréglage absent produit une explication. La fenêtre n’ajoute pas de rig de remplacement si votre version installée ne possède pas ce préréglage.

L’étagère native de ressources du bas importe des ressources d’armature. Utilisez **Add → Armature → Starter Rig Catalog** pour la procédure ci-dessous qui prend les dépendances en compte.

Si un maillage est sélectionné, l’outil ajuste le rig de départ à ce maillage lors de l’ajout. Dans la fenêtre, cliquez sur une vignette pour ajouter un rig ou faites-la glisser dans la vue. La pondération automatique et la génération des contrôles sont désactivées au départ. Ajustez ensuite ces options dans **Adjust Last Operation**.

Si aucun maillage n’était sélectionné :

1. Sélectionnez le nouveau rig de départ.
2. Dans Quick Rig, sélectionnez **Mesh**.
3. Cliquez sur **Fit Dropped Rig**.

L’ajustement redimensionne et positionne le squelette. Avant de générer des contrôles ou des poids :

1. Inspectez la position des articulations.
2. Corrigez-la si nécessaire.

Glisser hors de la vue, appuyer sur Esc ou faire un clic droit annule sans rien ajouter.

**Emplacement :** Rig Builder → Quick Rig ; Add → Armature → Quick Rig ajoute aussi les rigs prédéfinis

---

### Mannequin {#mannequin}

**Fonction :** construit un maillage de prévisualisation autour d’un rig existant pour examiner sa déformation sans maillage de personnage terminé. Si vous n’avez pas encore de rig, ajoutez-en un avec Quick Rig. Avant Mannequin, sélectionnez l’armature ou un maillage qui lui est parenté. Le mannequin sert uniquement d’aperçu : remplacez-le par votre propre maillage avant l’utilisation finale.

**Commandes principales :**

- **Quick Mannequin** construit un aperçu avec des valeurs par défaut fixes, en remplaçant le mannequin précédent de ce rig
- **Add Mannequin** construit un aperçu avec les réglages de la scène. Il remplace par défaut un mannequin existant. Replace Existing se trouve dans Adjust Last Operation après le clic
- **Regenerate** reconstruit l’aperçu existant à partir de ses réglages enregistrés
- **Remove** supprime le maillage du mannequin et conserve l’armature
- Options, sous les boutons, contient **Mode**, **Body Type**, la densité et **Radius Scale**. Advanced, dans Options, contient les échelles par région et les réglages de sortie. Pour utiliser les nouveaux réglages de la scène, cliquez de nouveau sur **Add Mannequin**

**Emplacement :** Rig Builder → Mannequin

---

## Atelier du mannequin : instructions écrites {#illustrated-mannequin-workshop}

<!-- Keep each illustrated step together and preserve the manual's print scale. -->
<style>
section.chapter:has(#ch-06-rig-builder) img { max-width: 100%; max-height: 155mm; width: auto; height: auto; }
@media print {
  [id="06-rig-builder--illustrated-mannequin-workshop"] { break-before: page; break-after: avoid; }
  h4[id^="06-rig-builder--"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] + h4 { break-before: avoid; }
  section.chapter:has(#ch-06-rig-builder) h4 + p { break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) { break-before: avoid; break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) + p { break-before: avoid; }
}
</style>

Suivez ces trois parties dans l’ordre :

1. [A — de Simple Human au mannequin](#part-a-simple-human-to-mannequin).
2. [B — mannequin sans rig avec Auto-Rig](#part-b-rigless-mannequin-through-auto-rig).
3. [C — tester les poids et utiliser l’IK/FK](#part-c-test-weights-and-use-ikfk).

Le texte source anglais fournit une véritable capture d’interface pour chaque étape numérotée de l’atelier ; les nombres rouges correspondent aux légendes. Ces captures ont été réalisées avec **BoneCraft 9.1.2** dans `Bforartists 5.2.0`. Cette édition sans images omet les captures et conserve les étapes écrites, descriptions d’images et légendes. La disposition des panneaux et les raccourcis de Blender peuvent différer. Fiez-vous aux noms des commandes.

Les captures du texte source anglais, omises ici, conservent leurs libellés de version 9.1.2. La navigation actuelle est **Rig Builder → Quick Rig**, **Rig Builder → Auto-Rig Wizard** et **BoneCraft → Skin → Weight Tools**. Starter Rigs utilise désormais l’onglet de catalogue natif du bas. Cette édition sans images ne prétend pas que l’atelier a été rejoué avec 9.2.18 ou 9.2.19.

Cet exercice produit un aperçu simple en capsules pour apprendre le rigging. La tête, les mains et le torse sont provisoires. Ce n’est pas un personnage terminé. Commencez dans un nouveau fichier. Conservez les deux points de sauvegarde pour refaire la conversion sans perdre le métarig initial.

Le dépôt contient les deux points de sauvegarde dans `examples/mannequin/` : `SimpleHuman_Mannequin.blend` est le résultat neutre de la partie A ; `Mannequin_AutoRig.blend` est l’exemple terminé et posé de la partie C, avec les poids corrigés.

### Partie A : de Simple Human au mannequin {#part-a-simple-human-to-mannequin}

#### A1. Activer Rigify {#a1-enable-rigify}

1. Commencez dans une nouvelle scène.
2. Ouvrez **Scene Properties → Rig Builder → Quick Rig**.
3. Si les préréglages Rigify ne sont pas disponibles, cliquez sur **Enable Rigify**.

Ce tutoriel utilise le métarig Rigify `Simple Human`. **BoneCraft Basic Humanoid (19 bones)** est un autre préréglage.

Description de l’image source anglaise (image omise) : A1 : activer Rigify

*1 — Scene Properties. 2 — Enable Rigify.*

#### A2. Ajouter Simple Human {#a2-add-simple-human}

Cliquez sur `Simple Human` dans Quick Rig. Vous obtenez un métarig modifiable, pas encore un maillage. Il possède 29 os dans cette version.

Description de l’image source anglaise (image omise) : A2 : ajouter Simple Human

*1 — Préréglage Simple Human.*

#### A3. Examiner le métarig {#a3-inspect-the-metarig}

1. Placez le pointeur dans la vue.
2. Appuyez sur `Numpad 1` pour la vue orthographique de face.
3. Vérifiez que le squelette entier est visible.
4. Utilisez la molette pour cadrer le squelette.

Le nouveau métarig peut commencer en mode Pose.

Description de l’image source anglaise (image omise) : A3 : examiner le métarig

*1 — Vue de face. 2 — Squelette Simple Human.*

#### A4. Revenir en mode Objet {#a4-return-to-object-mode}

Avant de changer la pose de repos ou de générer le mannequin :

1. Dans le menu de mode de la vue, sélectionnez **Object Mode**.
2. Gardez `SimpleHumanArmature` sélectionné.

Description de l’image source anglaise (image omise) : A4 : revenir en mode Objet

*1 — Menu des modes. 2 — Object Mode.*

#### A5. Utiliser une pose en T {#a5-use-a-t-pose}

Dans Quick Rig, cliquez sur **T-Pose**. Les bras s’étendent horizontalement. Pour un corps personnalisé, ajustez le métarig en mode Édition avant de générer l’aperçu. Dans cet exercice, gardez les articulations gauche et droite symétriques.

Description de l’image source anglaise (image omise) : A5 : utiliser une pose en T

*1 — Commande T-Pose.*

#### A6. Générer le mannequin {#a6-generate-the-mannequin}

1. Dépliez **Mannequin → Options**.
2. Réglez `Mode: Universal`.
3. Réglez `Body Type: Neutral`.
4. Sélectionnez **Medium**.
5. Réglez `Radius Scale: 1.00`.
6. Dans Advanced, gardez les échelles régionales à 1.00.
7. Sélectionnez `Joined (non-manifold)`.
8. Sélectionnez **Flat colour**.
9. Activez **Joint Smoothing**.
10. Laissez Unified Volume désactivé.
11. Cliquez sur **Add Mannequin**.

La capture du texte source anglais, omise ici, montre le maillage en capsules obtenu. Add utilise les options actuelles. Regenerate réutilise les réglages enregistrés du mannequin.

Description de l’image source anglaise (image omise) : A6 : générer le mannequin

*1 — Add Mannequin. 2 — Réglages Universal et du corps. 3 — Sortie Joined et lissage.*

#### A7. Essayer une pose d’os {#a7-try-a-bone-pose}

La gauche du personnage se trouve à votre droite en vue de face.

1. Sélectionnez l’armature.
2. Passez en **Pose Mode**.
3. Cliquez sur l’os de l’avant-bras gauche.
4. Avec l’outil de rotation, faites légèrement tourner l’os.

Le mannequin attaché suit. C’est un aperçu pondéré sur le métarig. Il ne possède pas encore les contrôles d’animation utilisés dans la partie C.

Description de l’image source anglaise (image omise) : A7 : essayer une pose d’os

*1 — Pose Mode. 2 — Avant-bras sélectionné et son gizmo de transformation.*

#### A8. Restaurer et sauvegarder l’aperçu {#a8-restore-and-save-the-preview}

1. Avec le pointeur dans la vue, sélectionnez tous les os de pose.
2. Appuyez sur **F3**.
3. Recherchez `Clear Pose Transforms`.
4. Sélectionnez **All**.
5. Vérifiez que le mannequin revient à sa pose en T.
6. Ouvrez **File → Save As**.
7. Enregistrez le fichier sous `SimpleHuman_Mannequin.blend`.

Conservez ce point de sauvegarde avant de continuer.

Description de l’image source anglaise (image omise) : A8 : restaurer et sauvegarder l’aperçu

*1 — Recherche Clear Pose Transforms. 2 — All réinitialise les os de pose sélectionnés.*

### Partie B : mannequin sans rig avec Auto-Rig {#part-b-rigless-mannequin-through-auto-rig}

#### B1. Sélectionner le maillage du mannequin {#b1-select-the-mannequin-mesh}

Repartez du point de sauvegarde neutre de la partie A. Cette partie retire volontairement le rig du mannequin avant de lancer l’assistant.

1. Passez en **Object Mode**.
2. Dans l’Outliner, sélectionnez `SimpleHumanArmature_Mannequin`.

Pour préserver la partie A, enregistrez le résultat sous un autre nom de fichier.

Description de l’image source anglaise (image omise) : B1 : sélectionner le maillage du mannequin

*1 — Sélectionnez le maillage, pas l’armature.*

#### B2. Convertir l’aperçu en maillage {#b2-bake-the-preview-into-a-mesh}

Gardez le mannequin dans sa pose en T restaurée. Gardez uniquement le mannequin sélectionné.

1. Appuyez sur **F3**.
2. Recherchez `Convert Mesh`.
3. Exécutez `Convert Mesh`.

Cette opération conserve la géométrie neutre visible et retire le modificateur Armature.

Description de l’image source anglaise (image omise) : B2 : convertir l’aperçu en maillage

*1 — Commande Convert Mesh.*

#### B3. Supprimer le parent {#b3-clear-the-parent}

1. Appuyez sur **Alt+P**.
2. Sélectionnez `Clear and Keep Transformation`.

Le maillage est détaché de l’ancien métarig sans être déplacé.

Description de l’image source anglaise (image omise) : B3 : supprimer le parent

*1 — Clear and Keep Transformation.*

#### B4. Supprimer les anciens poids {#b4-remove-the-old-weights}

Cette opération concerne uniquement ce maillage d’exercice jetable. Les groupes appartiennent à l’ancien métarig. L’assistant en créera de nouveaux.

1. Ouvrez **Object Data Properties → Vertex Groups**.
2. Dans le menu de la liste, sélectionnez `Delete All Groups`.

Description de l’image source anglaise (image omise) : B4 : supprimer les anciens poids

*1 — Menu Vertex Groups. 2 — Delete All Groups.*

#### B5. Vérifier le point de sauvegarde sans rig {#b5-verify-the-rigless-checkpoint}

1. Masquez l’ancien `SimpleHumanArmature` avec son icône en forme d’œil dans l’Outliner.
2. Vérifiez que le mannequin reste visible.
3. Vérifiez que son panneau Modifiers ne contient aucun modificateur Armature.
4. Vérifiez que sa liste Vertex Groups est vide.

C’est le mannequin sans rig à utiliser en entrée. BoneCraft 9.1.2 génère les mannequins à partir d’une armature. Détacher cet aperçu fournit un maillage d’exercice sans rig.

Description de l’image source anglaise (image omise) : B5 : vérifier le point de sauvegarde sans rig

*1 — Masquer l’ancien métarig. 2 — Pile de modificateurs vide.*

#### B6. Activer l’onglet Rig Builder de la vue {#b6-enable-the-viewport-rig-builder-tab}

Sur l’hôte 9.1.2 testé, Place Marker lancé depuis Scene Properties n’acceptait pas les clics dans la vue. Utilisez l’onglet de la vue pour placer les repères.

1. Ouvrez **Edit → Preferences → Add-ons → BoneCraft → Tabs**.
2. Activez **Rig Builder**.
3. Sélectionnez **Left**.
4. Fermez Preferences.
5. Placez le pointeur au-dessus de la vue.
6. Si l’étagère d’outils gauche est masquée, appuyez sur **T**.

Description de l’image source anglaise (image omise) : B6 : activer l’onglet Rig Builder de la vue

*1 — Activer Rig Builder. 2 — Placement dans l’étagère d’outils gauche.*

#### B7. Lancer Auto-Rig {#b7-start-auto-rig}

Le mannequin sans rig étant sélectionné, cliquez sur **Start Auto-Rig**. La capture du texte source anglais, omise ici, montre le bouton équivalent de Scene Properties. L’onglet Rig Builder de la vue, activé à l’étape précédente, propose la même commande en haut.

Description de l’image source anglaise (image omise) : B7 : lancer Auto-Rig

*1 — Start Auto-Rig.*

#### B8. Choisir le maillage d’entrée {#b8-choose-the-input-mesh}

Ne sélectionnez pas de widget ni un autre objet d’aperçu.

1. Dans `Select Mesh`, sélectionnez le mannequin.
2. Vérifiez la coche du maillage sélectionné.
3. Cliquez sur **Next**.

Description de l’image source anglaise (image omise) : B8 : choisir le maillage d’entrée

*1 — Mannequin d’entrée. 2 — Next.*

#### B9. Choisir un rig de corps avec les deux méthodes {#b9-choose-a-body-rig-with-both-methods}

Ce mannequin en capsules n’a pas de topologie faciale ; Body + Face est donc inutile.

1. Sélectionnez **Body Only**.
2. Sélectionnez `Kinematics: IK + FK`.
3. Gardez **Generate Control Shapes** activé.
4. Cliquez sur **Next**.

Description de l’image source anglaise (image omise) : B9 : choisir un rig de corps avec les deux méthodes

*1 — Body Only. 2 — IK + FK. 3 — Next.*

#### B10. Détecter les premiers repères du corps {#b10-detect-initial-body-markers}

Les positions détectées sont un point de départ. Ne les acceptez pas sans les vérifier.

1. Pour ce mannequin symétrique, gardez **Mirror Symmetry** activé.
2. Dans Body Markers, cliquez sur **Detect Markers** sous Smart Detection.

Description de l’image source anglaise (image omise) : B10 : détecter les premiers repères du corps

*1 — Detect Markers. 2 — Mirror Symmetry.*

#### B11. Examiner les positions détectées {#b11-review-the-detected-positions}

Cet aperçu segmenté produit plusieurs estimations de faible confiance. Avant la génération :

1. Comparez le sommet de la tête, la base du cou, le bassin, les poignets et les chevilles au maillage visible.
2. Examinez les repères principaux et les repères de précision facultatifs.
3. Corrigez-les si nécessaire.

Les libellés de confiance décrivent la détection initiale. Une coche verte au début d’une ligne indique que la position actuelle est confirmée.

Description de l’image source anglaise (image omise) : B11 : examiner les positions détectées

*1 — Résumé de confiance de la détection. 2 — Lignes des repères du corps.*

#### B12. Placer un poignet sur le maillage {#b12-place-a-wrist-on-the-mesh}

En vue de face, le poignet gauche du personnage est à droite de l’écran.

1. Si le repère est déjà confirmé, réinitialisez sa ligne pour faire apparaître le bouton de placement.
2. Dans l’onglet **Rig Builder** de la vue, cliquez sur la pipette **Place Marker** de Wrist Left.
3. Cliquez sur la surface du poignet dans la vue.

Description de l’image source anglaise (image omise) : B12 : placer un poignet sur le maillage

*1 — Commande de placement de Wrist Left. 2 — Cliquer sur la surface du poignet.*

#### B13. Vérifier le poignet opposé et les chevilles {#b13-check-the-mirrored-wrist-and-ankles}

1. Vérifiez que les deux lignes de poignets ont des coches vertes et des coordonnées X opposées.
2. Répétez le placement de `Ankle Left` au niveau de l’articulation, pas des orteils.

La symétrie fournit Ankle Right. Vérifiez-la sur le maillage. Ne recopiez pas les coordonnées de l’exemple sur un personnage d’une autre taille.

Description de l’image source anglaise (image omise) : B13 : vérifier le poignet opposé et les chevilles

*1 — Paire de poignets confirmée. 2 — Poignet symétrique sur le maillage.*

#### B14. Affiner les épaules et les coudes {#b14-refine-shoulders-and-elbows}

1. Faites défiler jusqu’à Precision Markers.
2. Réinitialisez `Shoulder Left`.
3. Placez `Shoulder Left` au pivot du bras.
4. Réinitialisez `Elbow Left`.
5. Placez `Elbow Left` dans l’espace du coude.
6. Confirmez les repères symétriques correspondants.
7. Gardez le poignet à l’extrémité de l’avant-bras, côté main.

Ces points déterminent la chaîne du bras. Corrigez toute épaule ou tout coude détecté sur la mauvaise capsule.

Description de l’image source anglaise (image omise) : B14 : affiner les épaules et les coudes

*1 — Lignes des repères d’épaule et de coude. 2 — Épaule. 3 — Coude.*

#### B15. Affiner les hanches et les genoux {#b15-refine-hips-and-knees}

1. Placez `Hip Left` en haut de la cuisse.
2. Placez `Knee Left` dans l’espace entre la cuisse et le tibia.
3. Vérifiez le côté opposé fourni par symétrie.
4. Gardez le bassin sur l’axe central, entre les hanches.

Description de l’image source anglaise (image omise) : B15 : affiner les hanches et les genoux

*1 — Lignes de hanche et de genou. 2 — Surface de la hanche. 3 — Espace du genou.*

#### B16. Vérifier la profondeur et les orteils de profil {#b16-check-depth-and-toes-from-the-side}

1. Le pointeur au-dessus de la vue, appuyez sur `Numpad 3`.
2. Vérifiez les repères en vue orthographique droite, ainsi que de face.
3. Placez `Toe Left` près de l’avant du pied.
4. Vérifiez le repère symétrique correspondant.

Un repère peut sembler correct de face, tout en étant trop en avant ou en arrière du corps.

Description de l’image source anglaise (image omise) : B16 : vérifier la profondeur et les orteils de profil

*1 — Vue orthographique droite. 2 — Ligne du repère d’orteil. 3 — Surface du pied.*

#### B17. Placer les talons {#b17-place-the-heels}

1. Si un talon a été mal estimé, réinitialisez-le.
2. De profil, placez `Heel Left` près de l’arrière du pied.
3. Vérifiez Heel Right.

Ces repères sont facultatifs. Les laisser tous deux à zéro produisait un avertissement de proximité dans la version testée. Les placer sur les pieds supprimait cet avertissement.

Description de l’image source anglaise (image omise) : B17 : placer les talons

*1 — Paire de talons confirmée. 2 — Emplacement du talon.*

#### B18. Confirmer et continuer {#b18-confirm-and-continue}

1. Examinez le sommet de la tête, la base du cou, le bassin et chaque paire de repères.
2. Cliquez sur **Confirm All Placed**.
3. Cliquez sur **Next**.

Les coches vertes près des noms montrent l’état de confirmation. Les libellés de confiance initiaux REVIEW/ADJUST peuvent rester visibles dans 9.1.2.

Description de l’image source anglaise (image omise) : B18 : confirmer et continuer

*1 — Confirm All Placed. 2 — Next.*

#### B19. Ignorer les doigts pour ce maillage {#b19-skip-fingers-for-this-mesh}

Ce mannequin possède des capsules de mains, mais aucune géométrie de doigts.

1. Sélectionnez `0 — No Fingers`.
2. Cliquez sur **Next**.

Pour un vrai maillage de main :

1. Sélectionnez le nombre de doigts approprié.
2. Placez les repères des doigts.

Description de l’image source anglaise (image omise) : B19 : ignorer les doigts pour ce maillage

*1 — No Fingers. 2 — Next.*

#### B20. Vérifier et générer {#b20-review-and-generate}

Avant de continuer, exigez **All checks passed**. Ces réglages conviennent à ce mannequin d’exercice simple. Ce ne sont pas des exigences universelles d’exportation.

1. Sélectionnez **IK + FK**.
2. Activez les formes de contrôle.
3. Réglez `Spine Segments: 3`.
4. Réglez `Neck Segments: 1`.
5. Sélectionnez `No Fingers`.
6. Sélectionnez **Game Ready**.
7. Désactivez Twist Bones.
8. Désactivez Skirt Bones.
9. Désactivez Preserve Volume.
10. Désactivez Joint Correctives.
11. Cliquez sur **Generate Rig**.

Description de l’image source anglaise (image omise) : B20 : vérifier et générer

*1 — Vérifications des repères. 2 — Réglages de génération. 3 — Generate Rig.*

#### B21. Construire les contrôles d’animation {#b21-build-the-animator-controls}

Après la génération, cliquez sur **Build Control Rig**. Generate Rig fournit le rig du corps et les poids. Build Control Rig ajoute la couche de contrôle utilisée ci-dessous. Le maillage d’entrée est déjà présent, même si le panneau de fin affiche son offre générique de mannequin. Ne cliquez pas de nouveau sur Quick Mannequin.

Description de l’image source anglaise (image omise) : B21 : construire les contrôles d’animation

*1 — Build Control Rig.*

#### B22. Terminer l’assistant {#b22-finish-the-wizard}

1. Attendez le message de fin du rig de contrôle.
2. Cliquez sur **Close Wizard**.
3. Gardez l’ancien métarig Simple Human masqué.

La nouvelle armature apparaît dans l’Outliner. Le nouveau rig doit déformer le maillage. Voir des os ne suffit pas à prouver que la déformation fonctionne.

Description de l’image source anglaise (image omise) : B22 : terminer l’assistant

*1 — Le bouton de construction est désormais désactivé. 2 — Close Wizard.*

### Partie C : tester les poids et utiliser l’IK/FK {#part-c-test-weights-and-use-ikfk}

Dans la version testée, l’armature générée porte ce nom d’objet (utilisez-le dans l’Outliner et l’outil de poids) :

```text
BoneForge_Rig
```

`FK (Forward Kinematics)` propage les rotations dans une hiérarchie. La rotation du bras affecte l’avant-bras, puis la main. Elle convient aux grands mouvements et aux membres libres. `IK (Inverse Kinematics)` part d’une extrémité. Lorsque vous déplacez une cible de poignet ou de cheville, le solveur plie la chaîne pour l’atteindre. Elle convient aux pieds posés et aux mains qui doivent toucher une surface.

| Tâche | Contrôle à utiliser | Point à surveiller |
|---|---|---|
| Balancer un bras | Contrôles FK d’épaule et de coude | Les contrôles enfants suivent leur parent |
| Placer une main | Cible IK du poignet | L’épaule et le coude se résolvent vers la cible |
| Poser un pied | Cible IK de cheville de cette jambe | Déplacez le corps pendant que la cible accessible reste en place |
| Orienter le pli du coude ou du genou | Contrôle de pôle IK | Le pôle règle la direction du pli ; ce n’est pas la cible du poignet ou de la cheville |
| Changer de méthode | Boutons IK/FK du membre | Vérifiez la pose ajustée avant d’insérer des clés d’animation |

L’exercice ci-dessous compare un bras dans les deux modes. Chaque membre possède son propre commutateur. `Bake IK / Bake FK` sont des outils de conversion d’animation. Changer de méthode sur une pose ne remplace ni le précalcul ni l’insertion des clés d’une animation. Consultez [Control Layer](05-rig-tools.md#control-layer-ikfk) pour les autres commandes.

#### C1. Ouvrir la couche de contrôle {#c1-open-the-control-layer}

1. Sélectionnez l’**armature générée**.
2. Sélectionnez **Pose Mode**.
3. Ouvrez **BoneCraft → Review → Control Layer**.
4. Sélectionnez **arm-L → FK**.

Chaque bras et jambe possède un commutateur IK/FK distinct. Gauche et droite désignent les côtés du personnage. De face, arm-L apparaît à votre droite.

Description de l’image source anglaise (image omise) : C1 : ouvrir la couche de contrôle

*1 — Pose Mode. 2 — Control Layer et commutateur arm-L.*

#### C2. Afficher les contrôles d’animation {#c2-show-the-animator-controls}

1. Ouvrez **Object Data Properties → Bone Collections** de l’armature.
2. Sélectionnez l’étoile Solo de `Controls`.
3. Sélectionnez l’étoile Solo de **FK**.
4. Si le maillage cache les contrôles, activez **In Front** dans Viewport Display.
5. Lorsque vous utiliserez les cibles, incluez **IK**.

Les sélections Solo isolent ces formes de contrôle. Cette liste native de collections fonctionne aussi si le panneau Collections de BoneCraft ne s’affiche pas sur cet hôte.

Description de l’image source anglaise (image omise) : C2 : afficher les contrôles d’animation

*1 — Étoiles Solo de Controls et FK. 2 — In Front.*

#### C3. Sélectionner le contrôle FK de l’avant-bras {#c3-select-the-forearm-fk-control}

1. De face, cliquez sur le contrôle circulaire du coude gauche du personnage.
2. Vérifiez que le nom de la sélection dans la vue est **forearm.fk-L**.

Un contrôle FK d’avant-bras tourne autour du coude. Sélectionner celui de l’épaule ferait tourner le bras et ses enfants à la place.

Description de l’image source anglaise (image omise) : C3 : sélectionner le contrôle FK de l’avant-bras

*1 — Contrôle forearm.fk-L sélectionné. 2 — FK actif pour arm-L.*

#### C4. Tourner et examiner la déformation {#c4-rotate-and-inspect-the-deformation}

Pour cet exemple de face, le but est une rotation d’environ `−45°` autour de l’axe global **Y**. Utilisez l’une de ces méthodes :

- Avec l’outil de rotation, faites tourner le contrôle FK sélectionné.
- Avec la configuration de touches de Bforartists montrée, suivez ces étapes :

1. Appuyez sur **Ctrl+E**.
2. Appuyez sur **Y**.
3. Saisissez **-45**.
4. Appuyez sur **Enter**.

Le raccourci de rotation par défaut de Blender est **R**. La capture du texte source anglais, omise ici, montre volontairement le problème initial de poids : la capsule du bras s’incline avec l’avant-bras. N’acceptez pas ce résultat comme un rig terminé.

Description de l’image source anglaise (image omise) : C4 : tourner et examiner la déformation

*1 — Mouvement incorrect du bras lors du test FK.*

#### C5. Recalculer les poids du mannequin {#c5-recalculate-the-mannequin-weights}

Si le test de pose ci-dessus échoue, suivez ces étapes :

1. Passez en **Object Mode**.
2. Sélectionnez le maillage.
3. Ouvrez **BoneCraft → Skin → Weight Tools → Automatic Bone Weight Recalculation**.
4. Réglez Mesh to Reweight sur le mannequin.
5. Réglez Existing Armature sur l’**armature générée**.
6. Sélectionnez **Body**.
7. Sélectionnez `Body Method: Bone Heat`.
8. Réglez `New Weight Strength: 1.00`.
9. Réglez `Smooth Passes: 0`.
10. Réglez `Max Bones per Vertex: 0`.
11. Réglez `Minimum Weight: 0.001`.
12. Gardez **Keep Weight Backup** activé.
13. Exécutez **Automatic Bone Weight Recalculation**.

Cette opération a corrigé l’aperçu segmenté dans la version testée.

Description de l’image source anglaise (image omise) : C5 : recalculer les poids du mannequin

*1 — Maillage et armature. 2 — Bone Heat. 3 — Réglages de remplacement et sauvegarde. 4 — Recalculer.*

#### C6. Vérifier le pli FK corrigé {#c6-verify-the-repaired-fk-bend}

1. Sélectionnez de nouveau l’armature générée.
2. Revenez en **Pose Mode**.

Le bras doit maintenant rester horizontal de l’épaule au coude, tandis que l’avant-bras se relève depuis le coude. L’objet masqué `WEIGHTS_BACKUP_…` conserve les anciens poids. Avant d’animer votre personnage, testez aussi les autres membres. Un squelette généré ne prouve pas à lui seul que la déformation est correcte.

Description de l’image source anglaise (image omise) : C6 : vérifier le pli FK corrigé

*1 — Le bras reste en place. 2 — L’avant-bras se plie au coude.*

#### C7. Passer le même bras en IK {#c7-switch-the-same-arm-to-ik}

Cliquez sur **arm-L → IK**. Le changement ajuste la cible à la pose actuelle ; le bras doit donc rester levé. Si les cibles sont masquées, ajoutez **IK** aux collections Solo visibles. Le changement détermine quels contrôles pilotent la chaîne. Il n’enregistre pas de nouvelle animation.

Description de l’image source anglaise (image omise) : C7 : passer le même bras en IK

*1 — Commutateur IK de arm-L. 2 — Pose conservée lors du changement.*

#### C8. Sélectionner la cible IK du poignet {#c8-select-the-wrist-ik-target}

1. Cliquez sur le contrôle au poignet.
2. Vérifiez que le nom de la sélection est **forearm.ik-L**.

Malgré son nom d’avant-bras, c’est la cible d’extrémité de la chaîne du bras. Déplacez-la pour placer la main. Le solveur change les angles de l’épaule et du coude pour atteindre la cible.

Description de l’image source anglaise (image omise) : C8 : sélectionner la cible IK du poignet

*1 — Cible de poignet sélectionnée. 2 — Nom de sélection.*

#### C9. Déplacer la cible et comparer {#c9-move-the-target-and-compare}

Gardez la cible à portée du bras. Le but est un léger déplacement du poignet vers l’intérieur, selon l’axe global **X**. Dans cet exemple, `−0.15 m` crée un pli visiblement différent. Utilisez l’une de ces méthodes :

- Faites glisser la flèche X de l’outil de déplacement.
- Avec la configuration de touches montrée, suivez ces étapes :

1. Appuyez sur **Ctrl+W**.
2. Appuyez sur **X**.
3. Saisissez `-0.15`.
4. Appuyez sur **Enter**.

Le raccourci de déplacement par défaut de Blender est **G**. Comparez le bras entier à l’exemple FK. L’extrémité mène le mouvement et les deux segments du bras suivent.

Description de l’image source anglaise (image omise) : C9 : déplacer la cible et comparer

*1 — Extrémité du poignet. 2 — Réponse de la chaîne. 3 — Exemple de déplacement X.*

#### C10. Revenir en FK et sauvegarder l’exemple {#c10-switch-back-and-save-the-example}

1. Cliquez de nouveau sur **arm-L → FK**.

Les contrôles FK s’ajustent à la pose IK actuelle.

2. Vérifiez que le maillage ne saute pas.
3. Ouvrez **File → Save As**.
4. Enregistrez `Mannequin_AutoRig.blend`.

La capture du texte source anglais, omise ici, montre l’exemple enregistré avec FK actif. Pour une copie d’exercice neutre :

1. Gardez les quatre membres en FK.
2. Sélectionnez tous les contrôles de pose visibles.
3. Appuyez sur **F3**.
4. Recherchez `Clear Pose Transforms`, comme dans la partie A.
5. Sélectionnez **All**.
6. Enregistrez la copie neutre sous un autre nom.

Description de l’image source anglaise (image omise) : C10 : revenir en FK et sauvegarder l’exemple

*1 — FK de nouveau actif. 2 — Pose conservée. 3 — Nom du fichier enregistré.*

**Vérification finale :** l’aperçu du métarig initial reste sauvegardé. Le mannequin détaché possède un nouveau rig de corps et des contrôles. Les poids de l’aperçu sont corrigés. Vous avez comparé une rotation FK à un déplacement de cible IK. Conservez le rig enregistré comme exemple d’apprentissage. Pour la production, remplacez l’aperçu par une géométrie de personnage adaptée.

---

### Transfert d’animation {#animation-retargeting}

Le transfert d’une animation d’un squelette à un autre est traité dans [Rig Tools : Retarget](05-rig-tools.md#retarget).

Consultez la [description de Retarget](05-rig-tools.md#retarget) pour ses commandes de clips.

---

## Bone Merge {#bone-merge}

**Fonction :** combine deux armatures en une seule, par exemple un rig de corps et un rig de vêtements ou de cheveux, en conservant tous les poids.

Le [guide 11](03-guides-b.md#guide-11-merge-two-rigs-together) décrit la procédure pas à pas.

**Les trois étapes :**

- Scope : sélection des deux armatures et examen de leurs différences
- Rename : résolution des conflits de noms et identification des nouveaux os
- Merge : aperçu, puis fusion finale

**Commandes principales :**

- **Base** : l’armature conservée. L’autre est fusionnée avec elle, puis masquée
- **Analyze** compare les deux squelettes. **Acknowledge Scope — Proceed to Rename** ouvre l’étape 2
- **Normalize Both Armatures** renomme les os standard des deux rigs selon une convention commune : Mixamo Prefixed, Mixamo Stripped ou personnalisée
- **Auto-Propose Renames** suggère des noms pour les os propres au rig à fusionner
- **Apply Rename** renomme une entrée (une étape d’annulation). **Apply Batch Pattern** en renomme plusieurs selon un motif (avec `{bone}`, `{side}` et `{index}`)
- **Mark as Unique** conserve un os comme nouvel os au lieu de le fusionner
- **Verify Rename — Proceed to Merge** ouvre l’étape 3
- **Run Merge Preview** indique ce que ferait la fusion sans rien modifier
- **Merge Armatures** sauvegarde les deux armatures et les fusionne

**Emplacement :** BoneCraft → Setup Rigging → Bone Merge

Description de l’image source anglaise (image omise) : Bone Merge commence par l’étape 1 : Scope. Les étapes suivantes restent verrouillées tant que les vérifications précédentes ne sont pas terminées.

*Panneau contextuel natif, BoneCraft 9.2.18. Bone Merge commence par l’étape 1 : Scope. Les étapes suivantes restent verrouillées tant que les vérifications précédentes ne sont pas terminées.*

Suivant : [Mechanisms](07-mechanisms.md)
