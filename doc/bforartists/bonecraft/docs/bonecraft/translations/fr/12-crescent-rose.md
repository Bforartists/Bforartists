# Tutoriel : Crescent Rose avec Mechanisms {#tutorial-crescent-rose-with-mechanisms}

[← Sommaire](index.md)

<!-- Print layout is scoped to this illustrated chapter; the shared renderer is unchanged. -->
<style>
@media print {
  h3[id^="12-crescent-rose--"] { break-before: page; break-after: avoid; }
  h2:has(+ h3[id^="12-crescent-rose--"]) { break-before: page; break-after: avoid; }
  h2 + h3[id^="12-crescent-rose--"] { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) { break-after: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) + p { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) table { break-inside: avoid; }
  [id="12-crescent-rose--what-you-built"] { break-before: page; break-after: avoid; }
}
</style>

## Ce que vous allez construire {#what-you-will-build}

Crescent Rose combine une faux et un fusil. Ce tutoriel crée le rig du modèle avec Mechanisms. Un curseur transforme la faux en fusil. Un second replie le fusil dans sa forme compacte.

Le tutoriel utilise tous les types actuels d’articulation et de lien sauf Gear Link. Il comprend huit Hinges, trois Slides, un Telescope, un Piston et un Follow. Il crée aussi deux Sequences et trois Forms.

Les formes sont des poses pédagogiques pour ce modèle réalisé par un fan. Mechanisms ne détecte pas les collisions et ne produit pas une réplique conçue selon les règles de l’ingénierie physique. Si vous adaptez le rig, vérifiez les dégagements.

Le résultat est le fichier `examples/crescent-rose/CrescentRose_Mechanisms.blend`. Ouvrez-le à tout moment pour comparer.

## Avant de commencer {#before-you-start}

- Fichiers : `examples/crescent-rose/CrescentRose_parts.blend` contient le modèle divisé en 15 objets. Commencez le tutoriel depuis ce fichier. `CrescentRose_Mechanisms.blend` est le rig terminé.
- Durée : prévoyez une séance pour préparer le FBX et une autre pour la leçon Mechanisms. Ces exercices sont conséquents. Enregistrez des points de sauvegarde entre les étapes.
- Vocabulaire : lisez d’abord « Fonctionnement de Mechanisms » dans [Mechanisms](07-mechanisms.md). Cette section définit les pièces, articulations, liens, poignées, Sequences et Forms.
- Langue : les captures du texte source anglais, omises ici, montrent Bforartists et les panneaux de BoneCraft en anglais. Les panneaux BoneCraft suivent la préférence **Language**. Le reste de Bforartists suit sa langue d’interface. Si BoneCraft ne prend pas en charge votre langue Bforartists, ses panneaux restent en anglais. Les instructions écrites de cette édition sans images restent applicables.
- Point de départ : utilisez P1-P8 ci-dessous pour le FBX d’origine ou passez à l’étape 1 avec le fichier préparé. Les deux parcours utilisent les mêmes 15 pièces.
- Vérifications historiques du texte source anglais : instructions et véritables captures d’interface ont été vérifiées avec BoneCraft `9.1.2` dans Bforartists `5.2.0`, avec sa configuration de touches par défaut. Aucune nouvelle capture ni reprise du tutoriel n’a été réalisée pour cette édition sans images.

**Navigation actuelle :** dans 9.2.18, utilisez **BoneCraft → Mechanisms** ou **Properties → Scene → Mechanisms**. Si les sections Scene sont masquées, activez **Tabs → Scene Properties → Show**. Parts, Joints & Links, Sequences et Controls gardent leur nom. Les anciennes captures du texte source anglais, omises ici, peuvent montrer une disposition antérieure autour de ces sections.

Cette édition sans images conserve les limites historiques de capture et de reprise en 9.1.2 du texte source anglais ; les images sont omises. La revue du code source 9.2.18 ne les remplace pas par une nouvelle exécution du tutoriel. Les anciennes Forms enregistrées restent lisibles et utilisables. Les ouvrir ou les appliquer ne réenregistre pas leurs valeurs. Consultez [Forms](07-mechanisms.md#forms).

Les images du texte source anglais utilisent des marques rouges numérotées pour indiquer où cliquer, quoi saisir ou quoi examiner. Cette édition sans images les omet et conserve leurs descriptions écrites et légendes d’actions. Suivez les étapes et les indications d’action dans l’ordre (1, puis 2, puis 3). Ces nombres désignent les annotations de la source anglaise et recommencent pour chaque image. Dans ces preuves sources, un rectangle indique un résultat à vérifier et un cercle une pièce ou un bouton à utiliser.

## Préparer le FBX d’origine (P1-P8) {#prepare-the-original-fbx-p1-p8}

Si vous utilisez `CrescentRose_parts.blend`, sautez cette section.

1. Travaillez dans un nouveau fichier.

2. Gardez le FBX source et son dossier `CrescentRoseTextures` ensemble.

Ces étapes ont été rejouées dans Bforartists 5.2.0 avec la configuration de touches par défaut. Utilisez le menu de mode visible. Dans cette configuration, Tab peut basculer les superpositions au lieu d’entrer en mode Édition.

### P1 - Importer le FBX {#p1---import-the-fbx}

Utilisez l’importateur Legacy pour cette procédure.

1. Commencez avec une scène vide.

2. Sélectionnez **File > Import > FBX (.fbx) (Legacy)**.

3. Sélectionnez `CrescentRose.fbx`.

4. Gardez l’échelle d’importation Scale à `1.00`.

5. Sélectionnez Import FBX.

6. Appuyez sur Numpad 3 pour la vue droite.

7. Appuyez sur Home pour cadrer les objets importés.

L’Outliner contient une racine et trois maillages de matériaux : `Black01`, `Blades01` et `Red01`.

Description de l’image source anglaise (image omise) : P1 : options d’importation FBX Legacy, Scale à 1.00

*1 : sélectionner CrescentRose.fbx. 2 : garder Scale à 1.00. 3 : cliquer sur Import FBX ; utiliser l’importateur Legacy.*

### P2 - Préserver le placement et régler la taille {#p2---preserve-placement-and-set-the-size}

L’arme importée mesure environ `0.32 m` de haut. Le fichier préparé est déjà à l’échelle. N’effectuez ce redimensionnement qu’une fois sur les maillages importés.

1. Passez en mode Objet.

2. Sélectionnez les trois maillages.

3. Sélectionnez **Object > Parent > Clear and Keep Transformation**.

4. Supprimez de la scène de travail la racine devenue inutile.

5. Les trois maillages sélectionnés, choisissez **Object > Apply > Rotation & Scale**.

6. Appuyez sur Ctrl+R pour lancer Scale dans cette configuration de touches Bforartists.

7. Saisissez `6.25` pour redimensionner ensemble les trois maillages.

8. Confirmez l’échelle.

9. Sélectionnez de nouveau **Object > Apply > Rotation & Scale**.

L’arme complète mesure désormais environ `1.997 m` de haut.

Description de l’image source anglaise (image omise) : P2 : supprimer le parent en conservant le placement

*1 : appuyer sur F3 et rechercher Clear Parent Keep Transform. 2 : choisir Clear and Keep Transformation. Répéter pour les trois maillages avant de supprimer la racine.*

Description de l’image source anglaise (image omise) : P2 : rotation et échelle appliquées à l’arme importée

*1 : après avoir redimensionné ensemble les trois maillages par 6.25, appliquer Rotation & Scale ; Rotation doit afficher 0. 2 : Scale doit afficher 1 sur tous les axes.*

Le champ Dimensions d’un objet mesure uniquement ce maillage de matériau. Vérifiez l’étendue totale de bas en haut pour mesurer l’arme. Les trois objets doivent avoir une rotation nulle et une échelle de 1 avant la séparation.

### P3 - Connecter les matériaux {#p3---connect-the-materials}

1. Passez à l’espace de travail Shading.

2. Sélectionnez Material Preview.

Chacun des trois matériaux utilise quatre images de `CrescentRoseTextures` :

| Image | Espace colorimétrique |
|---|---|
| `BaseColor` | **sRGB** |
| `Metallic` | `Non-Color` |
| `Roughness` | `Non-Color` |
| `Normal` | `Non-Color` |

Pour chaque matériau, traitez une image à la fois :

1. Chargez l’image correspondante depuis `CrescentRoseTextures`.

2. Réglez son espace colorimétrique selon le tableau.

3. Pour BaseColor, Metallic ou Roughness, reliez la sortie Color d’Image Texture à l’entrée correspondante de Principled BSDF.

Pour chaque image Normal, utilisez cette branche de connexion distincte :

1. Insérez un nœud **Normal Map**.

2. Gardez ce nœud en `Tangent Space`.

3. Reliez Color de l’image Normal à Color de Normal Map.

4. Reliez Normal de Normal Map à Normal de Principled BSDF.

Conservez les UV existants.

Description de l’image source anglaise (image omise) : P3 : quatre textures et Normal Map en Tangent Space connectées au matériau noir

*1 : relier Color de BaseColor à Base Color du BSDF. 2 : garder BaseColor en sRGB. 3 : régler toutes les textures de données sur Non-Color. 4 : relier image Normal > Normal Map > Normal du BSDF, en Tangent Space.*

Description de l’image source anglaise (image omise) : P3 : les trois matériaux dans Material Preview

*1 : vérifier le matériau de la lame. 2 : vérifier les matériaux rouges et noirs du corps dans Material Preview ; aucune texture manquante rose.*

La procédure s’applique aux matériaux noir, de lame et rouge. Après avoir sélectionné chaque image, vérifiez son espace colorimétrique. Ce réglage appartient à l’image. L’arme doit être rouge, noire et métallique, sans texture manquante rose.

### P4 - Séparer les pièces disjointes {#p4---separate-loose-pieces}

1. Sélectionnez les trois maillages de matériaux.

2. Sélectionnez **Edit Mode** dans le menu de mode de la vue.

3. Sélectionnez toute la géométrie.

4. Sélectionnez **Mesh > Separate > By Loose Parts**.

5. Revenez en mode Objet.

Il y a désormais **37** objets de maillage. Les suffixes numériques générés peuvent varier. Identifiez les objets par leur position et leur forme.

Description de l’image source anglaise (image omise) : P4 : entrer en mode Édition et choisir By Loose Parts

*1 : passer en mode Édition et sélectionner toute la géométrie. 2 : appuyer sur F3, rechercher Separate Loose et choisir By Loose Parts.*

Description de l’image source anglaise (image omise) : P4 : les 37 pièces disjointes après séparation

*1 : vérifier que le total d’objets est de 37 après séparation. 2 : utiliser l’Outliner pour sélectionner les pièces par forme et emplacement ; les suffixes peuvent varier.*

### P5 - Joindre les 15 groupes mobiles {#p5---join-the-15-moving-groups}

Le tableau répertorie chaque îlot source. Les noms de matériaux décrivent l’apparence, pas le nom final des objets.

| Objet final | Pièces à combiner | Sommets après assemblage |
|---|---|---:|
| `BladeTip` | Bouton noir d’articulation de pointe et pointe métallique | 252 |
| `Blade2` | Deux plaques métalliques du deuxième segment et deux caches rouges | 1000 |
| `Blade1` | Deux plaques métalliques du premier segment, au plus près de la tête | 512 |
| `HeadMount` | Bloc arrière noir, capot supérieur et noyau ; deux plaques intérieures rouges et deux caches supérieurs fins | 1395 |
| `PlateL` | Une plaque extérieure rouge de tête du côté X négatif | 676 |
| `PlateR` | Une plaque extérieure rouge de tête du côté X positif | 676 |
| `RearSpike` | Deux lames métalliques de pointe, deux caches rouges de pivot et deux plaques rouges de fixation | 1194 |
| `Receiver` | Corps noir et petit bouton, anneau métallique au-dessus de la culasse et long carter rouge | 2609 |
| `Grip` | Bloc rouge de poignée sous le boîtier | 194 |
| `Magazine` | Tube noir sous le corps | 96 |
| `Bolt` | Cylindre rouge de culasse et ses deux pièces de bouton | 362 |
| `Pole` | Manche inférieur métallique et collier rouge | 148 |
| `ButtSpike` | Pointe métallique inférieure | 110 |
| `StrutBase` | Fine tige rouge entre le boîtier et la tête | 34 |
| `StrutRod` | Manchon noir cranté autour de cette tige | 108 |

Ne fusionnez pas les plaques extérieures avec Blade1. Ne fusionnez pas les deux pièces de la biellette. Celle-ci possède déjà deux pièces distinctes. Aucune coupe Bisect n’est nécessaire.

Travaillez de la pointe de la lame vers l’intérieur, puis sur le boîtier et le manche. Pour chaque groupe mobile :

1. Sélectionnez les pièces qui doivent bouger ensemble.

2. Pour des pièces appariées de côtés opposés, faites pivoter la vue pour sélectionner les deux.

3. Vérifiez la sélection avant l’assemblage.

4. Sélectionnez **Object > Join** (Ctrl+J).

5. Renommez l’objet assemblé dans l’Outliner.

Le total doit être de **15 maillages et 9,366 sommets**. L’étape 2 reprend les noms définitifs des pièces et leurs relations de parenté ultérieures.

Description de l’image source anglaise (image omise) : P5 : les 15 groupes mobiles nommés dans l’Outliner

*1 : renommer chaque groupe assemblé dans l’Outliner pour correspondre aux 15 noms du tableau.*

Description de l’image source anglaise (image omise) : P5 : les deux plaques sources de Blade1 sélectionnées avant assemblage

*1 : sélectionner les deux plaques métalliques opposées de Blade1. 2 : vérifier que les deux objets sont sélectionnés, puis utiliser Join et renommer le résultat Blade1.*

Description de l’image source anglaise (image omise) : P5 : commande Join du menu Object

*1 : ouvrir Object après avoir sélectionné uniquement les pièces d’un groupe. 2 : choisir Join (Ctrl+J). Ce détail du menu identifie la commande ; utiliser la sélection des deux pièces montrée plus haut.*

### P6 - Centrer les origines {#p6---centre-the-origins}

1. Passez en mode Objet.

2. Sélectionnez les 15 maillages.

3. Sélectionnez **Object > Set Origin > Origin to Geometry**.

4. Réglez l’option Center de l’opération sur `Bounds Center`.

5. Vérifiez que la rotation est nulle et l’échelle à 1.

Les objets n’ont toujours aucun parent. Il n’y a pas d’armature. Ces origines servent à la préparation. L’étape 6 place les pivots des mécanismes sur les articulations réelles.

Description de l’image source anglaise (image omise) : P6 : Object > Set Origin > Origin to Geometry

*1 : ouvrir Object. 2 : survoler Set Origin. 3 : choisir Origin to Geometry ; régler Bounds Center dans les options de l’opération.*

Description de l’image source anglaise (image omise) : P6 : origine centrée de Blade1 avec transformations appliquées

*1 : l’origine orange est maintenant centrée sur le maillage. 2 : confirmer Rotation 0. 3 : confirmer Scale 1. Les pivots des mécanismes seront déplacés plus tard.*

### P7 - Redimensionner et empaqueter les textures {#p7---resize-and-pack-the-textures}

Il y a **12 textures utilisées**, quatre par matériau. N’écrasez pas les JPEG sources. Pour chaque texture utilisée :

1. Sélectionnez-la dans l’éditeur d’images.

2. Sélectionnez **Image > Resize**.

3. Réglez la largeur sur **1024**.

4. Réglez la hauteur sur **1024**.

5. Confirmez le redimensionnement.

6. Sélectionnez **Image > Pack**.

L’empaquetage conserve les pixels redimensionnés dans le fichier blend. Après avoir traité chaque texture, vérifiez Material Preview.

Description de l’image source anglaise (image omise) : P7 : menu Image empaquetant une texture redimensionnée en 1024 par 1024

*1 : choisir Image > Resize et saisir 1024 pour largeur et hauteur. 2 : vérifier les dimensions obtenues, 1024 x 1024. 3 : choisir Pack. Répéter pour les 12 textures utilisées.*

### P8 - Enregistrer et rouvrir le fichier préparé {#p8---save-and-reopen-the-prepared-file}

1. Enregistrez la copie de travail sous `CrescentRose_parts.blend`.

2. Rouvrez ce fichier.

3. Vérifiez les 15 maillages nommés, leurs transformations et les matériaux rouges et noirs.

4. Sélectionnez de nouveau la vue droite.

5. Appuyez sur Home.

6. Passez à l’étape 1.

Les 12 textures doivent rester disponibles sans le répertoire de textures d’origine.

Description de l’image source anglaise (image omise) : P8 : fichier préparé rouvert avec l’arme texturée intacte

*1 : ouvrir File pour Save As, puis Open pour recharger votre copie de travail. 2 : vérifier que les 15 maillages nommés sont conservés. 3 : vérifier les matériaux ; la barre de titre identifie le fichier rouvert.*

## A. Ouvrir le fichier {#a-open-the-file}

### Étape 1 — Ouvrir le fichier des pièces {#step-1--open-the-parts-file}

1. Ouvrez `examples/crescent-rose/CrescentRose_parts.blend`.

2. Sélectionnez l’affichage Material Preview dans la vue.

3. Appuyez sur Numpad 3 pour la vue droite.

4. Appuyez sur Home pour cadrer l’arme.

La lame pointe vers la gauche et la pointe du manche vers le bas.

Description de l’image source anglaise (image omise) : étape 1 : fichier des pièces en vue droite

*1 : cliquer sur Material Preview. 2 : appuyer sur Numpad 3 jusqu’à voir Right Orthographic ; appuyer sur Home pour cadrer l’arme.*

**Ce que vous devez voir :** la faux rouge et noire, haute d’environ 2 m, sans sélection.

### Étape 2 — Identifier les pièces {#step-2--meet-the-parts}

L’Outliner contient les 15 objets. Chacun constitue une pièce qui se déplace d’un bloc :

| Objet | Description | Porté par |
|---|---|---|
| `Receiver` | Corps du fusil avec lunette, détente et viseur | le rig |
| `Grip` | Poignée sous le boîtier | `Receiver` |
| `Magazine` | Chargeur cylindrique | `Receiver` |
| `Bolt` | Culasse | `Receiver` |
| `Pole` | Manche inférieur et collier | `Receiver` |
| `ButtSpike` | Pointe en bas | `Pole` |
| `HeadMount` | Bloc de tête auquel la lame est suspendue | `Receiver` |
| `Blade1` | Premier segment de lame, au plus près de la tête | `HeadMount` |
| `Blade2` | Deuxième segment | `Blade1` |
| `BladeTip` | Pointe | `Blade2` |
| `RearSpike` | Pointe à l’arrière de la tête | `HeadMount` |
| `PlateL`, `PlateR` | Plaques latérales extérieures de la tête | `HeadMount` |
| `StrutBase` | Fine tige entre le boîtier et la tête | `Receiver` |
| `StrutRod` | Manchon cranté autour de cette tige | `HeadMount` |

Description de l’image source anglaise (image omise) : étape 2 : les 15 objets de pièces dans l’Outliner

*1 : identifier les trois segments de lame. 2 : faire correspondre les noms du corps, de la tête et du manche au tableau. 3 : garder StrutBase et StrutRod comme objets distincts.*

Pour le FBX d’origine, suivez P1-P8 ci-dessus. Ces actions d’interface ont produit le fichier préparé fourni. Le script de préparation du dépôt fournit un tableau de regroupement de référence.

### Étape 3 — Trouver Mechanisms {#step-3--find-mechanisms}

Si l’étagère d’outils gauche est masquée :

1. Avec le pointeur au-dessus de la vue, appuyez sur T.

2. Sélectionnez Tools dans le menu Region Toggle.

Ensuite :

1. Ouvrez l’onglet BoneCraft de l’étagère d’outils gauche.

2. Dépliez **Mechanisms**.

3. Faites glisser le bord droit de l’étagère pour rendre le texte du panneau lisible.

La même section apparaît dans **Properties > Scene** si Scene Properties est réglé sur Show dans les préférences de BoneCraft. Les captures du texte source anglais, omises ici, utilisent l’étagère d’outils.

Avec un maillage actif et sans rig, **Add Parts from Selection** apparaît en haut. Avant de l’utiliser, sélectionnez toutes les pièces comme indiqué à l’étape 4. Les sous-sections numérotées deviennent utilisables après l’ajout des pièces.

Description de l’image source anglaise (image omise) : étape 3 : section Mechanisms de l’onglet BoneCraft

*1 : cliquer sur l’onglet BoneCraft. 2 : déplier Mechanisms. 3 : repérer Add Parts from Selection ; sélectionner les maillages avant utilisation.*

## B. Pièces {#b-parts}

### Étape 4 — Ajouter les pièces sélectionnées {#step-4--add-parts-from-selection}

1. Avec le pointeur au-dessus de la vue, appuyez sur A pour sélectionner les 15 objets.

2. Sélectionnez **Add Parts from Selection**.

Description de l’image source anglaise (image omise) : étape 4 : toutes les pièces sélectionnées, Add Parts from Selection

*1 : survoler la vue et appuyer sur A pour sélectionner les 15 maillages. 2 : cliquer sur Add Parts from Selection.*

**Ce que vous devez voir :** une nouvelle armature, « Mechanism Rig », apparaît dans l’Outliner avec les pièces dessous. Les objets de maillage restent sélectionnés. **1. Parts** énumère les 15 pièces. L’onglet BoneCraft commence maintenant par l’Overview repliable du rig.

### Étape 5 — Rides on {#step-5--rides-on}

Une pièce est portée par la pièce à laquelle elle est attachée.

1. Sélectionnez `Blade1` dans **1. Parts**.

2. Ouvrez le menu « Rides on » sous la liste.

3. Sélectionnez `HeadMount`.

4. Répétez pour chaque pièce avec le tableau de l’étape 2.

`Receiver` conserve « the rig ».

Description de l’image source anglaise (image omise) : étape 5 : Blade1 est porté par HeadMount

*1 : sélectionner Blade1 dans la liste Parts. 2 : ouvrir Rides on et choisir HeadMount. Répéter avec le tableau des parents.*

### Étape 6 — Pivots {#step-6--pivots}

Une charnière tourne autour du pivot de sa pièce. Les segments de lame, la tête et la poignée doivent tourner à leurs articulations plutôt qu’autour de leur centre. Travaillez dans la vue orthographique de profil pour conserver la position latérale du pivot.

1. Sélectionnez `Blade1` dans la liste.

2. Sélectionnez **Edit Pivot**.

3. Sélectionnez le repère.

4. Appuyez sur Ctrl+W pour Move dans Bforartists.

5. Cliquez à la jonction du segment et de la tête.

6. Sélectionnez **Apply Pivot**.

7. Répétez cette procédure de pivot pour les pièces ci-dessous.

| Pièce | Position du pivot |
|---|---|
| `Blade2` | À sa jonction avec `Blade1` |
| `BladeTip` | À sa jonction avec `Blade2` |
| `HeadMount` | Son point le plus bas, à la jonction avec la biellette |
| `Grip` | Son bord supérieur |
| `RearSpike` | À sa jonction avec la tête |
| `PlateL` et `PlateR` | Au centre du boulon rond, là où Blade1 rejoint la tête |
| `StrutBase` | En bas |
| `StrutRod` | En haut |

La position du repère dans la capture source anglaise, omise ici, sert de guide. Quelques millimètres ne font aucune différence visible.

Description de l’image source anglaise (image omise) : étape 6 : sélectionner la pièce et cliquer sur Edit Pivot

*1 : sélectionner Blade1 dans Parts. 2 : cliquer sur Edit Pivot, puis déplacer et appliquer le repère comme indiqué ensuite.*

Description de l’image source anglaise (image omise) : étape 6 : repère de pivot de Blade1 sur l’articulation, Apply Pivot

*1 : déplacer le repère de pivot sur l’articulation de lame avec Ctrl+W. 2 : cliquer sur Apply Pivot pour garder cet emplacement.*

## C. La tête {#c-the-head}

### Étape 7 — Add Joint → Hinge {#step-7--add-joint--hinge}

Si une pièce doit être masquée pour dégager la vue, masquez-la avant de lancer l’assistant.

Ouvrez **Add Joint → Hinge**. L’en-tête et la barre d’état de la construction guidée expliquent chaque étape.

Description de l’image source anglaise (image omise) : étape 7 : menu Add Joint, Hinge

*1 : ouvrir Add Joint. 2 : cliquer sur Hinge. La construction guidée attend maintenant une pièce.*

### Étape 8 — Cliquer sur la tête {#step-8--click-the-head}

L’en-tête indique « click the part that turns » : cliquez sur la pièce qui tourne. En vue droite, la plaque extérieure cache la tête. Cliquez sur le bloc arrière de la tête, derrière les plaques, à l’emplacement du cercle.

Si l’en-tête nomme `PlateR` :

1. Appuyez sur Esc.

2. Relancez **Add Joint > Hinge**.

3. Cliquez plus en arrière sur la tête.

Lorsqu’il est actif, l’assistant intercepte les raccourcis clavier ordinaires.

Description de l’image source anglaise (image omise) : étape 8 : cliquer sur le bloc arrière de la tête

*1 : cliquer sur le bloc noir arrière de HeadMount, derrière la plaque extérieure rouge. Vérifier que l’assistant nomme HeadMount.*

### Étape 9 — Appuyer sur X, puis Enter {#step-9--press-x-then-enter}

L’en-tête demande l’axe.

1. Appuyez sur X.

2. Examinez l’aperçu en boucle.

3. Appuyez sur Enter pour conserver la charnière.

La tête tourne autour de l’axe latéral.

Description de l’image source anglaise (image omise) : étape 9 : choix de l’axe

*1 : suivre l’invite d’axe : appuyer sur X, puis Enter. 2 : observer la tête tourner autour de son pivot avant de confirmer.*

**Ce que vous devez voir :** `HeadMount Hinge` dans **2. Joints & Links**, avec son curseur dans **4. Controls**. Utilisez ces curseurs en mode Objet.

Pour utiliser les poignées d’os dans la vue :

1. Sélectionnez l’armature.

2. Passez en mode Pose.

### Étape 10 — Limites {#step-10--limits}

1. Sélectionnez `HeadMount Hinge` dans la liste.

2. Réglez **Min** sur 0.

3. Réglez **Max** sur 120.

Les valeurs positives tournent la tête vers le bas et l’arrière. Gardez la limite de course de 120 degrés. La séquence Rifle utilise une cible de 90 degrés avec les charnières de lame.

Description de l’image source anglaise (image omise) : étape 10 : Min 0, Max 120

*1 : sélectionner HeadMount Hinge. 2 : régler Min sur 0. 3 : régler Max sur 120 ; double-cliquer sur le nombre, saisir la valeur et appuyer sur Enter.*

### Étape 11 — Tester {#step-11--test}

Cliquez sur le bouton de lecture de la ligne. La tête va jusqu’à 120° et revient, puis la pose est restaurée.

Description de l’image source anglaise (image omise) : étape 11 : Test sur la ligne de la charnière

*1 : cliquer sur le petit triangle de lecture de la ligne HeadMount Hinge. Observer le balayage et le retour.*

## D. La chaîne de lame {#d-the-blade-chain}

### Étape 12 — Trois charnières supplémentaires {#step-12--three-more-hinges}

Pour `Blade1`, `Blade2` et `BladeTip`, répétez les étapes 7 à 10 :

1. Ouvrez **Add Joint → Hinge**.

2. Cliquez sur le segment.

3. Appuyez sur X.

4. Appuyez sur Enter.

5. Réglez **Max** sur 120.

Chaque segment est porté par le précédent. Les trois charnières forment une chaîne.

Description de l’image source anglaise (image omise) : étape 12 : les trois charnières des segments de lame et la charnière distincte de tête dans la liste

*1 : créer et sélectionner chaque charnière : Blade1, Blade2, BladeTip. 2 : régler Max sur 120 pour chacune ; utiliser X comme axe.*

### Étape 13 — Essayer la chaîne {#step-13--try-the-chain}

1. Repliez **2. Joints & Links** pour dégager de la place.

2. Dépliez **4. Controls**.

3. En mode Objet, réglez `Blade1 Hinge`, `Blade2 Hinge` et `BladeTip Hinge` sur 60 degrés chacun.

Pour saisir chaque valeur :

1. Double-cliquez dans son champ numérique.

2. Appuyez sur Ctrl+A.

3. Saisissez la valeur.

4. Appuyez sur Enter.

Les segments suivants se déplacent avec les précédents et recourbent la chaîne. Avant de continuer, remettez les trois valeurs à 0.

Description de l’image source anglaise (image omise) : étape 13 : les trois charnières de lame à 60 degrés dans Controls

*1 : saisir 60 dans chacun des trois curseurs de lame. 2 : vérifier que la chaîne se recourbe ensemble. Remettre les trois curseurs à 0.*

## E. Plaques et biellette {#e-plates-and-strut}

### Étape 14 — Charnières sur les plaques {#step-14--hinges-on-the-plates}

`PlateL` est masqué derrière la tête en vue droite.

1. Ajoutez une Hinge sur `PlateR` avec la même procédure.

2. Réglez son **Max** sur 30.

3. Appuyez sur Ctrl+Numpad 3 pour la vue gauche.

4. Ajoutez une Hinge sur `PlateL`.

5. Réglez son **Max** sur 30.

6. Appuyez sur Numpad 3 pour revenir en vue droite.

Description de l’image source anglaise (image omise) : étape 14 : PlateL Hinge et PlateR Hinge

*1 : créer les deux charnières de PlateR et PlateL ; utiliser la vue du côté opposé pour atteindre PlateL. 2 : régler chaque Max sur 30.*

### Étape 15 — Add Link → Follow {#step-15--add-link--follow}

Une poignée doit déplacer les deux plaques. Réglez la vue avant de lancer l’assistant :

1. Appuyez sur Numpad 1 pour la vue de face.

2. Sélectionnez `Blade2`.

3. Utilisez F3 > Frame Selected pour rapprocher la tête.

Les deux plaques extérieures apparaissent aux bords gauche et droit.

1. Ouvrez **Add Link > Follow**.

2. Cliquez sur `PlateL` au bord gauche comme pièce menante.

3. Cliquez sur `PlateR` au bord droit comme pièce suiveuse.

4. Appuyez sur Enter.

Description de l’image source anglaise (image omise) : étape 15 : la vue de face expose les deux plaques extérieures pour choisir les pièces de Follow

*1 : cliquer d’abord sur PlateL, la pièce menante. 2 : cliquer ensuite sur PlateR, la pièce suiveuse. Appuyer sur Enter.*

### Étape 16 — Plages {#step-16--ranges}

1. Sélectionnez le nouveau Follow.

2. Vérifiez **Source Range** 0…30 et **Target Range** 0…30, remplis automatiquement.

3. Dans **Name**, renommez le lien `PlateR Follow`.

Description de l’image source anglaise (image omise) : étape 16 : Source Range et Target Range

*1 : nommer le lien PlateR Follow. 2 : vérifier Source Range de 0 à 30. 3 : vérifier Target Range de 0 à 30.*

### Étape 17 — Add Link → Piston {#step-17--add-link--piston}

La biellette doit pointer entre le boîtier et la tête pendant le repli de la tête. L’assistant intercepte les raccourcis de navigation lorsqu’il est actif. Avant de le lancer :

1. Appuyez sur Numpad 3 pour la vue droite.

2. Sélectionnez `StrutRod` dans l’Outliner.

3. Utilisez F3 > Frame Selected pour une vue rapprochée.

4. Ouvrez **Add Link > Piston**.

Description de l’image source anglaise (image omise) : étape 17 : menu Add Link, Piston

*1 : ouvrir Add Link après avoir cadré StrutRod. 2 : choisir Piston ; l’assistant demande d’abord le cylindre.*

### Étape 18 — Le cylindre et la tige {#step-18--the-cylinder-and-the-rod}

Les rôles cylindre et tige de l’assistant désignent les extrémités du lien. Les noms d’objets du modèle décrivent les pièces sources. `StrutBase` est la fine tige rouge exposée dans les crans du manchon. `StrutRod` est le manchon noir.

1. Dans la vue rapprochée, cliquez d’abord sur `StrutBase` comme pièce cylindre.

2. Cliquez ensuite sur `StrutRod` comme pièce tige.

3. Appuyez sur Enter pour accepter.

4. Renommez le lien `Head Strut`.

5. Gardez **Stretch** désactivé.

1. Modifiez `HeadMount Hinge` dans Controls.

2. Examinez la biellette.

3. Remettez la valeur à zéro.

**Ce que vous devez voir :** la biellette suit la tête. Chaque pièce vise l’autre.

Description de l’image source anglaise (image omise) : étape 18 : assistant Piston, cylindre rouge exposé puis manchon noir

*1 : cliquer d’abord sur le StrutBase rouge exposé. 2 : cliquer ensuite sur le manchon noir StrutRod. Appuyer sur Enter.*

Description de l’image source anglaise (image omise) : étape 18 : réglages de Head Strut avec Stretch désactivé

*1 : renommer le lien Head Strut. 2 : laisser Stretch décoché ; tester ensuite HeadMount Hinge et restaurer 0.*

## F. Le fusil {#f-the-rifle}

### Étape 19 — Charnières de poignée et de pointe arrière {#step-19--grip-and-rear-spike-hinges}

Pour `Grip` et `RearSpike` :

1. Ouvrez **Add Joint → Hinge**.

2. Cliquez sur la pièce.

3. Appuyez sur X.

4. Appuyez sur Enter.

5. Réglez **Min** sur 0.

6. Réglez **Max** sur 90.

Ensuite :

1. Sélectionnez `RearSpike Hinge` dans la liste.

2. Réglez son Axis X sur -1.

3. Gardez Y et Z à 0.

4. Gardez Grip sur X positif.

5. Confirmez que `Grip Hinge` et `RearSpike Hinge` apparaissent dans la liste des articulations.

Inverser l’axe X de RearSpike le replie vers la tête repliée dans Compact. Ces contrôles replient la poignée et la pointe arrière pour la forme compacte à l’étape 25.

Description de l’image source anglaise (image omise) : étape 19 : Grip Hinge, Max 90

*1 : sélectionner Grip Hinge. 2 : garder Axis X à 1, Y et Z à 0. 3 : régler Max sur 90 ; garder Min à 0.*

Description de l’image source anglaise (image omise) : étape 19 : RearSpike Hinge avec Axis X -1 et Max 90

*1 : sélectionner RearSpike Hinge. 2 : régler Axis X sur -1. 3 : régler Max sur 90 ; garder Min à 0.*

### Étape 20 — Glissières Magazine et Bolt {#step-20--magazine-and-bolt-slides}

Pour `Magazine`, puis `Bolt` :

1. Ouvrez **Add Joint → Slide**.

2. Cliquez sur la pièce.

3. Appuyez sur Z.

4. Appuyez sur Enter.

5. Réglez **Max** sur 0.04 pour Magazine ou 0.06 pour Bolt.

Les glissières utilisent les unités de la scène. Une valeur de 0.06 correspond à 6 cm.

Description de l’image source anglaise (image omise) : étape 20 : Magazine Slide, axe Z et Max 0.04

*1 : sélectionner Magazine Slide après Add Joint > Slide. 2 : utiliser l’axe Z (Z = 1, X = Y = 0). 3 : régler Max sur 0.04 ; garder Min à 0.*

Description de l’image source anglaise (image omise) : étape 20 : Bolt Slide, axe Z et Max 0.06

*1 : sélectionner Bolt Slide après Add Joint > Slide. 2 : utiliser l’axe Z (Z = 1, X = Y = 0). 3 : régler Max sur 0.06 ; garder Min à 0.*

### Étape 21 — Glissière du manche {#step-21--pole-slide}

1. Ouvrez **Add Joint → Slide**.

2. Cliquez sur `Pole`.

3. Appuyez sur Z.

4. Appuyez sur Enter.

5. Réglez **Max** sur 0.6.

6. Dans **4. Controls**, réglez `Pole Slide` sur 0.6.

7. Examinez le manche rétracté.

8. Remettez le contrôle à zéro.

Les valeurs positives font monter le manche dans le boîtier.

Description de l’image source anglaise (image omise) : étape 21 : réglages de Pole Slide, axe Z et Max 0.6

*1 : sélectionner Pole Slide après Add Joint > Slide. 2 : utiliser l’axe Z (Z = 1, X = Y = 0). 3 : régler Max sur 0.6 ; garder Min à 0.*

### Étape 22 — Télescope du manche {#step-22--pole-telescope}

1. Ouvrez **Add Joint → Telescope**.

2. Cliquez sur `Pole` comme base.

3. Cliquez sur `ButtSpike` comme segment.

4. Appuyez sur Enter.

5. Appuyez sur Z.

6. Appuyez sur Enter.

7. Réglez **Length** sur 0.2.

8. Testez le contrôle distinct.

9. Remettez le contrôle à zéro.

Ce contrôle déplace la pointe jusqu’à 20 cm selon Z positif, à l’intérieur du manche de ce modèle.

Description de l’image source anglaise (image omise) : étape 22 : choix guidés de Telescope, Pole comme base et ButtSpike comme segment

*1 : cliquer sur Pole comme base. 2 : cliquer sur ButtSpike comme segment. Appuyer sur Enter, puis Z, puis Enter.*

Description de l’image source anglaise (image omise) : étape 22 : réglages de Pole Telescope, axe Z et Length 0.2

*1 : sélectionner Pole Telescope. 2 : vérifier que Z est son axe. 3 : saisir Length 0.2 ; tester le contrôle et restaurer zéro.*

## G. Séquences {#g-sequences}

### Étape 23 — Ajouter une séquence {#step-23--add-sequence}

1. Dans **3. Sequences**, sélectionnez **Add Sequence**.

2. Double-cliquez sur le nom de la séquence dans la liste.

3. Saisissez `Scythe to Rifle`.

4. Appuyez sur Enter.

Description de l’image source anglaise (image omise) : étape 23 : Add Sequence

*1 : cliquer sur Add Sequence. 2 : double-cliquer sur le nouveau nom et saisir Scythe to Rifle. Appuyer sur Enter.*

### Étape 24 — Enregistrer un groupe de mouvements {#step-24--record-a-motion-group}

1. Sélectionnez **Move Slider to End**.

Le curseur de séquence passe à `100%`. Le bouton devient Record Step 1.

1. Dans **4. Controls**, réglez `BladeTip Hinge` sur 70.

2. Réglez `Blade2 Hinge` sur 120.

3. Sélectionnez Record Step 1.

Deux entrées cibles sont enregistrées, une par poignée déplacée. Les deux curseurs d’articulation reviennent à zéro.

Description de l’image source anglaise (image omise) : étape 24 : Move Slider to End avant de poser le premier groupe

*1 : cliquer une fois sur Move Slider to End. Le bouton devient Record Step 1.*

Description de l’image source anglaise (image omise) : étape 24 : Record Step 1 avec Blade2 à 120 et BladeTip à 70 degrés

*1 : saisir Blade2 = 120 et BladeTip = 70. 2 : cliquer sur Record Step 1 ; les deux cibles sont enregistrées et les curseurs d’articulation réinitialisés.*

*Groupes de mouvements restants.* L’enregistrement reste armé après chaque capture. Ne l’armez pas de nouveau. Pour chaque groupe restant ci-dessous :

1. Posez les poignées du groupe aux valeurs indiquées.

2. Sélectionnez le bouton Record Step affiché.

| Groupe de mouvements | Poignées à poser | Bouton d’enregistrement après les groupes précédents |
|---|---|---|
| 2 | `Blade1 Hinge` 10 et `PlateL Hinge` 30 | Record Step 3 |
| 3 | `HeadMount Hinge` 90 | Record Step 5 |
| 4 | `Pole Slide` 0.6 | Record Step 6 |

Le numéro du bouton correspond au nombre d’entrées cibles enregistrées plus un. Enregistrer deux poignées augmente le nombre de deux. Il ne compte pas les clics d’enregistrement. Les quatre groupes produisent six entrées cibles. Si vous changez les poignées déplacées, utilisez le numéro du bouton affiché.

### Étape 25 — Les étapes {#step-25--the-steps}

Chaque cible enregistrée possède une entrée sous la séquence. L’entrée montre **Target**, l’interpolation, **Start** et **End**. Les champs Start/End utilisent 0-1. Les curseurs de Controls affichent 0-100%.

| Mouvement | Start | End |
|---|---:|---:|
| La lame se replie d’abord | 0 | 0.25 |
| Les plaques et le premier segment suivent | 0.25 | 0.5 |
| La tête se replie en troisième | 0.5 | 0.8 |
| Le manche se déplace en dernier | 0.8 | 1 |

Les entrées du même groupe utilisent les mêmes valeurs Start et End. Pour chaque entrée de `Scythe to Rifle` :

1. Réglez **Start** sur la valeur Start de son groupe dans le tableau.

2. Réglez **End** sur la valeur End de son groupe dans le tableau.

3. Gardez l’entrée sur `Ease In Out`.

Avant l’intervalle d’une étape, sa valeur initiale est conservée. Après l’intervalle, sa valeur finale est conservée.

Une fois chaque séquence terminée, sélectionnez **Cancel** dans la bannière de capture. Cancel termine l’enregistrement, conserve les entrées enregistrées et ramène le curseur de cette séquence à zéro. Tant que l’enregistrement est armé, un avertissement de chevauchement décrit l’intervalle proposé pour le prochain enregistrement. N’ajoutez pas de groupe vide supplémentaire.

Pour la deuxième séquence, utilisez la procédure de l’étape 24 :

1. Ajoutez `Rifle to Compact`.

2. Sélectionnez une fois **Move Slider to End** pour armer l’enregistrement.

3. Réglez `Grip Hinge` sur 90 pour le premier groupe.

4. Réglez `RearSpike Hinge` sur 90.

5. Sélectionnez Record Step 1.

6. Pour chaque entrée du premier groupe :

    1. Réglez **Start** sur 0.

    2. Réglez **End** sur 0.5.

7. Réglez `Magazine Slide` sur 0.04 pour le deuxième groupe.

8. Réglez `Bolt Slide` sur 0.06.

9. Sélectionnez Record Step 3.

10. Pour chaque entrée du deuxième groupe :

    1. Réglez **Start** sur 0.5.

    2. Réglez **End** sur 1.

11. Gardez chaque entrée sur `Ease In Out`.

12. Sélectionnez **Cancel** dans la bannière de capture pour terminer l’enregistrement.

Chaque groupe crée deux entrées. Pour le deuxième groupe, le bouton passe de Record Step 1 à Record Step 3.

Description de l’image source anglaise (image omise) : étape 25 : les six cibles et leurs intervalles dans Scythe to Rifle

*1 : Target est la valeur d’articulation enregistrée. 2 : choisir Ease In Out. 3 : saisir Start. 4 : saisir End. Répéter ces champs pour les six entrées avec les valeurs montrées.*

Description de l’image source anglaise (image omise) : étape 25 : les quatre cibles et leurs intervalles dans Rifle to Compact

*1 : Grip et RearSpike utilisent Target 90, Start 0, End 0.5. 2 : Magazine et Bolt utilisent 0.04 / 0.06, Start 0.5, End 1. Garder Ease In Out.*

Description de l’image source anglaise (image omise) : étape 25 : terminer l’enregistrement avec Cancel dans la bannière de capture

*1 : après avoir terminé une séquence, cliquer sur Cancel dans cette bannière pour terminer l’enregistrement. Les entrées sont conservées et la séquence revient à zéro.*

### Étape 26 — Tester la séquence {#step-26--test-the-sequence}

**Test**, à côté du bouton d’enregistrement d’étape, fait aller le curseur de 0% à 100% puis à 0%. Il restaure ensuite la valeur que le curseur avait avant le test.

1. Depuis Scythe, sélectionnez **Test** pour `Scythe to Rifle`.

2. La première séquence étant à 100%, sélectionnez **Test** pour `Rifle to Compact`.

3. Après le test, remettez les deux séquences à 0%.

Description de l’image source anglaise (image omise) : étape 26 : bouton Test de la séquence pendant le repli

*1 : cliquer sur Test à côté du bouton d’enregistrement. 2 : observer le repli et le retour. Tester Compact avec Scythe to Rifle à 100%.*

**Ce que vous devez voir :** la lame se recourbe, les plaques se ferment, la tête se replie le long du boîtier et le manche remonte. Puis tout revient.

## H. Formes {#h-forms}

### Étape 27 — Enregistrer une forme {#step-27--save-form}

Gardez tous les curseurs d’articulation individuels à zéro. Les séquences fournissent leur mouvement. Placer la séquence sélectionnée à sa fin peut réarmer l’enregistrement. Enregistrer une Form n’enregistre pas une nouvelle étape. Sauf si vous voulez ajouter une cible, ne sélectionnez pas Record Step.

Dans **4. Controls** :

1. Tous les curseurs à 0, sélectionnez **Save Form**.

2. Double-cliquez sur la nouvelle entrée de la liste.

3. Nommez-la `Scythe`.

4. Réglez `Scythe to Rifle` sur `100%`.

5. Sélectionnez **Save Form**.

6. Nommez la nouvelle entrée `Rifle` de la même manière.

7. Réglez aussi `Rifle to Compact` sur `100%`.

8. Sélectionnez **Save Form**.

9. Nommez la nouvelle entrée `Compact`.

Pour désarmer l’enregistrement :

1. Sélectionnez `Scythe` dans la liste des formes.

2. Sélectionnez **Go to Form**.

Les deux séquences reviennent à zéro. Passer à Rifle ou Compact peut réarmer l’enregistrement, car la séquence sélectionnée est à 100%.

Description de l’image source anglaise (image omise) : étape 27 : Save Form avec tous les curseurs à 0

*1 : commencer avec les deux séquences et toutes les articulations à 0. 2 : cliquer sur Save Form. 3 : double-cliquer sur la nouvelle entrée et la nommer Scythe ; répéter pour Rifle et Compact.*

### Étape 28 — Appliquer une forme {#step-28--go-to-form}

1. Sélectionnez une forme dans la liste.

2. Sélectionnez **Go to Form**.

**Go and Key** insère aussi des clés pour chaque contrôle à l’image courante. Ces clés animent la transformation.

Description de l’image source anglaise (image omise) : étape 28 : Rifle sélectionné, Go to Form

*1 : sélectionner la forme enregistrée. 2 : cliquer sur Go to Form. Go and Key insère aussi des clés d’animation.*

### Étape 29 — Le fusil {#step-29--the-rifle}

Description de l’image source anglaise (image omise) : étape 29 : forme Rifle

*1 : sélectionner Rifle. 2 : cliquer sur Go to Form. 3 : comparer les pourcentages des séquences à la pose illustrée.*

### Étape 30 — Compact {#step-30--compact}

Description de l’image source anglaise (image omise) : étape 30 : forme Compact

*1 : sélectionner Compact. 2 : cliquer sur Go to Form. 3 : comparer les pourcentages des séquences à la pose illustrée.*

1. Revenez à `Scythe`.

2. Enregistrez le fichier.

## Ce que vous avez construit {#what-you-built}

| Élément | Os | Fonction |
|---|---|---|
| 15 pièces | `MCH-<part>` et `DEF-<part>` | Le maillage de chaque pièce est parenté à son os `DEF-` |
| 8 Hinges, 3 Slides, 1 Telescope | `CTRL-<part>` | Les poignées ; leurs valeurs correspondent aux curseurs de **4. Controls** |
| 1 Piston | `MCH-<part>-aim` et `MCH-<part>-target` | Gardent les deux pièces de la biellette dirigées l’une vers l’autre |
| 1 Follow | aucun | `PlateR` tourne avec `PlateL` |
| 2 Sequences | `CTRL-SEQ-<name>` | Un curseur chacune |
| 3 Forms | aucun | Valeurs de curseurs enregistrées |

L’exemple actualisé a passé Rig Validator sans problème signalé. Il a aussi passé les vérifications de rechargement avec Auto Run Python Scripts désactivé, notamment chaque contrôle individuel et les trois Forms.

## Pour aller plus loin {#try-next}

Pour modifier le mappage de Follow :

1. Activez **Curve** sur `PlateR Follow`.

2. Remodelez le mappage dans l’éditeur de graphes.

Pour une autre pose, enregistrez une quatrième forme, `Carry`, avec la lame repliée et la tête relevée.

Pour animer et exporter :

1. Insérez les formes dans le temps avec **Go and Key**.

2. Exportez les os `DEF-` (voir [Outils VRChat](08-vrchat.md)).

## Gear Link {#gear-link}

Crescent Rose n’a pas de paire d’engrenages ; ce rig n’a donc pas de Gear Link. Un Gear Link fait tourner une Hinge lorsqu’une autre tourne, selon un rapport de dents. Il peut servir pour une manivelle et une roue ou pour une crémaillère convertissant une rotation en glissement. Consultez [Gear Link](07-mechanisms.md#gear-link).

## Crédits {#credits}

Modèle Crescent Rose par amandangm, https://sketchfab.com/3d-models/crescent-rose-dcb6bfbb3b824c01a182fa131fe35824, CC BY 4.0. Ce tutoriel utilise une version divisée, redimensionnée et riggée. Crescent Rose est une création de Rooster Teeth Productions. Cette ressource de tutoriel a été réalisée par un fan.

[← Sommaire](index.md)
