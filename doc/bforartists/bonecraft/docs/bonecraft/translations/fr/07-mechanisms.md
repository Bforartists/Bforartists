# Mechanisms {#mechanisms}

[← Sommaire](index.md)

## Fonctionnement de Mechanisms {#what-mechanisms-does}

Mechanisms construit des rigs mécaniques à partir de pièces rigides. Il gère charnières, glissières, télescopes, pistons, engrenages, suiveurs et transformations complètes commandées par un curseur. Il construit des os et contraintes Blender ordinaires. Vous pouvez tout inspecter et modifier. Le rig fonctionne dans Blender sans scripts. Les moteurs reçoivent les os `DEF-`. L’exportation des mouvements précalculés de mécanismes vers les moteurs viendra plus tard (voir les limites de cette version).

BoneCraft fournit les outils. Vous fournissez les pièces de l’arme.

Un exemple complet, avec étapes écrites et descriptions d’images sources anglaises conservées, est proposé dans [Tutoriel : Crescent Rose avec Mechanisms](12-crescent-rose.md).

Vocabulaire utilisé dans les panneaux et sur cette page :

| Terme | Signification |
|---|---|
| *Part* | Pièce se déplaçant d’un bloc : objet ou partie disjointe d’un maillage. Une pièce peut être portée par une autre. |
| *Joint* | Mouvement autorisé d’une pièce : Hinge (rotation), Slide (translation), Telescope (extension de segments imbriqués). |
| *Link* | Ce qui déplace une pièce pour vous : Piston, Gear Link, Follow. |
| *Handle* | Os que vous faites glisser dans la vue. Chaque articulation en possède un. Sa valeur est aussi un curseur du panneau. |
| *Sequence* | Transformation commandée par un curseur et composée d’étapes. |
| *Form* | Ensemble enregistré de valeurs de poignées et de Sequences, par exemple « Stowed » ou « Rifle ». |

## Emplacement {#where-it-is}

- **Onglet BoneCraft → Mechanisms** dans la vue 3D. BoneCraft se trouve dans l’étagère d’outils gauche (**T**), sauf si vous l’avez déplacé dans la barre latérale droite (**N**) des préférences. Il se situe entre Skin et Review. Il s’affiche si un maillage est actif (pour commencer un rig) ou si une armature avec mécanismes est active. Sinon, il explique quoi sélectionner.
- **Éditeur Properties → onglet Scene → Mechanisms**, juste après Rig Builder. Il est affiché tant que Preferences → Tabs → Scene Properties → Show est activé. Sans sélection utilisable, une ligne indique « Select a mesh to start, or an armature with mechanisms. » : sélectionnez un maillage pour commencer ou une armature avec mécanismes. Désactiver l’onglet BoneCraft de la vue ne le retire pas. Le commutateur Scene Properties ne masque que la copie de Scene. Le commutateur d’outil `mechanisms` (**Preferences → Add-ons → BoneCraft → Tools**) retire l’outil de tous les emplacements. Les sections de Scene sont repliées au départ ; cliquez sur **Mechanisms** pour le déplier.
- **Menu Object → Mechanisms** fournit des raccourcis pour ajouter pièces, articulations et liens et tester le mouvement.
- **Barre d’outils de la vue → Build Mechanism** lance une articulation ou un lien guidé en cliquant sur une pièce, en mode Objet ou Pose.

Pour préparer Build Mechanism :

1. Ajoutez les pièces.
2. Sélectionnez le rig de mécanisme ou l’une de ses pièces.
3. Dans l’en-tête de l’outil, sélectionnez le type.

Mechanisms contient quatre sous-sections : **1. Parts**, **2. Joints & Links**, **3. Sequences** et **4. Controls**. Elles apparaissent quand le rig possède des pièces. Avant cela, seul **Add Parts from Selection** est visible.

Chaque bouton correspond à une étape d’annulation. Si une construction échoue, BoneCraft restaure tout ce qu’elle a modifié. Le panneau en indique la raison.

Description de l’image source anglaise (image omise) : Mechanisms dans l’onglet BoneCraft.

*Capture historique d’atelier. Mechanisms dans l’onglet BoneCraft.*

## Pièces {#parts}

1. Sélectionnez les objets de pièces (ou un maillage composé de parties disjointes) en mode Objet.
2. Cliquez sur **Add Parts from Selection**.
    - Plusieurs objets : une pièce par objet. Chaque objet est parenté à l’os de sa pièce et reste à sa place.
    - Un maillage avec des parties disjointes : une pièce par partie. Chacune reçoit un groupe de sommets pour son os et le maillage reçoit un modificateur Armature.
    - La première fois, BoneCraft crée le rig (une armature) pour vous.
3. Sélectionnez une pièce dans la liste pour la modifier.

Pour chaque pièce :

- **Rides on :** choisissez la pièce avec laquelle celle-ci se déplace. Une pièce enfant suit sa parente. « the rig » signifie qu’elle est portée par la racine du rig.
- **Size** règle la longueur d’os, donc la taille de la poignée.
- **Edit Pivot** place un repère sur la pièce. **Apply Pivot** déplace ses os sur le repère. L’objet reste en place.
- **Apply Transforms** apparaît si un objet de pièce possède une rotation ou une échelle non appliquée. Ces transformations inclinent les axes. Quand le bouton apparaît, cliquez sur **Apply Transforms**.
- Le bouton **X** retire la pièce. Il refuse tant qu’une articulation, un lien ou une autre pièce l’utilise, et nomme ces utilisateurs.
- **Merge for VRChat** nécessite au moins deux objets de pièces. Ne fusionnez que des pièces rattachées uniquement au rig de mécanisme. Faites-le en dernier. L’action joint les objets en un maillage avec un groupe de sommets par ancien objet et un modificateur Armature. Les pièces deviennent des parties disjointes de ce maillage. La fusion supprime les groupes portant les noms des os de cette armature, sauf le propre os `DEF-` de la pièce.

Pour changer le pivot d’une pièce :

1. Sélectionnez **Edit Pivot**.
2. Faites glisser le repère jusqu’au point de rotation ou de départ du glissement.
3. Cliquez sur **Apply Pivot**.

Vous pouvez renommer l’objet d’une pièce : les pièces sont identifiées sur leurs objets et retrouvent ainsi leur objet. Une copie (Shift+D) ne remplace pas la pièce. Si son objet est supprimé, la pièce affiche « Part '&lt;name&gt;' is missing » avec **Reassign** et **Delete**. Les autres mécanismes continuent de fonctionner.

- **Reassign** utilise le maillage sélectionné. Il refuse un objet non maillage ou déjà utilisé par une autre pièce de type objet. Les parties disjointes d’un maillage peuvent partager ce maillage.
- **Delete** retire la pièce (voir ci-dessous les cas de refus).

Description de l’image source anglaise (image omise) : pièces ajoutées et commandes de pivot de la pièce sélectionnée.

Description de l’image source anglaise (image omise) : pièces ajoutées et commandes de pivot de la pièce sélectionnée.

*Capture historique d’atelier. Pièces ajoutées et commandes de pivot de la pièce sélectionnée.*

## Articulations et liens : un exemple de chaque {#joints-and-links-one-example-each}

**Add Joint** lance une construction guidée d’articulation. **Add Link** lance une construction guidée de lien. Tous deux fonctionnent depuis l’onglet de la vue et l’onglet Scene de Properties. Depuis Scene, l’assistant utilise la plus grande vue 3D de l’écran.

Vous pouvez aussi utiliser la barre d’outils :

1. Activez Build Mechanism dans la barre d’outils de la vue.
2. Dans l’en-tête, sélectionnez le type d’articulation ou de lien.
3. Cliquez sur sa première pièce.

Ce clic lance le même assistant et fournit sa première sélection. Poursuivez avec les pièces et axes demandés dans la vue. Les menus Add Joint et Add Link restent disponibles.

**Align to Selection** permet des charnières inclinées. Il nécessite le maillage de la pièce en mode Édition avec une arête ou face sélectionnée quand vous appuyez sur **A**. L’assistant ignore **Tab**. Avant **Align to Selection**, préparez le maillage :

1. Sur le maillage de la pièce, entrez en mode Édition.
2. Sélectionnez une arête ou une face.
3. Toujours en mode Édition, lancez **Add Joint → Hinge**.
4. Cliquez sur la pièce.
5. Appuyez sur **A**.

Sans sélection utilisable, l’assistant affiche un message. Vous pouvez ensuite appuyer sur une autre touche.

Règles communes à chaque construction guidée :

- Cliquez sur les pièces dans la vue. Elles reçoivent un contour et un numéro.
- Si une étape demande un axe, appuyez sur **X**, **Y** ou **Z**.
- Après préparation d’**Align to Selection** comme ci-dessus, appuyez sur **A** pour aligner sur la sélection.
- La dernière étape montre le mécanisme en mouvement en boucle. **Enter** le conserve. **Esc** le retire.
- L’en-tête et la barre d’état affichent une phrase complète par étape. Avec Show Helpers désactivé, ils affichent un libellé court.

Chaque ligne de Joints & Links possède quatre icônes : **Test** (triangle de lecture), **Edit** (crayon, affiche les réglages), **Detach** (chaîne brisée) et **Delete** (X).

Après construction, l’élément sélectionné dans la liste montre uniquement les réglages utilisés par son type.

### Hinge {#hinge}

Blade Hinge, 0°…90° :

1. Utilisez Add Parts from Selection avec une pièce Blade.
2. Sélectionnez **Add Joint → Hinge**.
3. Cliquez sur Blade.
4. Appuyez sur **X**.
5. Appuyez sur **Enter**.

La construction crée une poignée en demi-cercle, `CTRL-Blade`, et une *Blade Hinge* dans la liste.

6. Réglez **Min** sur 0.
7. Réglez **Max** sur 90 (° pour une Hinge).
8. Pour tester la charnière, faites glisser la poignée en demi-cercle.

La poignée s’arrête à 90°. **Set Min** et **Set Max** copient sa pose actuelle dans les limites.

Une limite inférieure à un tour complet doit rester dans −180°…180°. Des limites comme 170°…190° sont refusées avec un message. Une plage d’au moins un tour, par exemple −180°…180°, tourne librement sans limite.

Description de l’image source anglaise (image omise) : limites de Hinge et commandes de poignée.

*Capture historique d’atelier. Limites de Hinge et commandes de poignée.*

### Slide {#slide}

Barrel Slide, 0…0.3 :

1. Sélectionnez **Add Joint → Slide**.
2. Cliquez sur la pièce Barrel.
3. Appuyez sur **Y**.
4. Appuyez sur **Enter**.

La construction crée une poignée en flèche.

5. Réglez **Min** sur 0.
6. Réglez **Max** sur 0.3 (unités de scène).
7. Pour tester la glissière, faites glisser la flèche.

Le canon glisse et s’arrête à 0.3.

Description de l’image source anglaise (image omise) : limites de course de Slide pour la pièce sélectionnée.

*Capture historique d’atelier. Limites de course de Slide pour la pièce sélectionnée.*

### Telescope {#telescope}

Mât à trois segments :

1. Créez la base et les trois pièces de segments.
2. Sélectionnez **Add Joint → Telescope**.
3. Cliquez sur la base.
4. Cliquez sur chaque segment dans l’ordre, de la base vers l’extérieur.
5. Appuyez sur **Enter**.
6. Appuyez sur la touche d’axe.
7. Pour conserver la construction, appuyez sur **Enter**.

La construction crée une poignée en flèche sur la base. **Length** définit la course totale. **Shares (empty = even)** répartit cette course entre les segments.

Pour tester une répartition personnalisée :

1. Réglez **Length** sur 1.
2. Saisissez `0.5, 0.25, 0.25` dans **Shares (empty = even)**.
3. Faites glisser la poignée en flèche.

Les trois segments s’allongent selon leur part. La somme doit être égale à Length pour que la pointe parcoure la longueur totale. Un texte invalide comme `0.5, abc` produit un message. Chaque segment doit avoir une part numérique et la somme doit être égale à Length. **Set Max** définit Length d’après la pose de la poignée.

Description de l’image source anglaise (image omise) : longueur de Telescope et répartition par segment.

*Capture historique d’atelier. Longueur de Telescope et répartition par segment.*

### Piston {#piston}

Élévateur : cylindre sur le cadre, tige sur le bras.

1. Donnez une Hinge au bras.
2. Définissez le cadre comme porteur du bras.
3. Sélectionnez **Add Link → Piston**.
4. Cliquez sur la pièce cylindre sur le cadre.
5. Cliquez sur la pièce tige sur le bras.

La construction crée un Piston sans poignée. Chaque pièce vise le point d’attache de l’autre. L’option **Stretch** étire la tige pour les ressorts et câbles.

6. Pour tester le Piston, déplacez la poignée du bras.

Le piston suit. Si rien ne déplace encore le Piston, la construction fonctionne mais n’a pas d’aperçu. **Test** signale cette situation.

Description de l’image source anglaise (image omise) : réglages de Piston pour les pièces connectées.

*Capture historique d’atelier. Réglages de Piston pour les pièces connectées.*

### Gear Link {#gear-link}

Engrenage 20:40 :

Les deux pièces doivent d’abord posséder une articulation. La pièce menante doit avoir une Hinge. Pour Gear et Belt, la pièce menée doit avoir une Hinge. Pour Rack, elle doit avoir une Slide.

1. Sélectionnez **Add Link → Gear Link**.
2. Cliquez sur la pièce menante.
3. Cliquez sur la pièce menée.

Pour utiliser le nombre de dents :

1. Dans les réglages du lien, réglez **Source Teeth** sur 20.
2. Réglez **Target Teeth** sur 40.

Vous pouvez aussi saisir un **Ratio**. **Kind** vaut Gear, Belt ou Rack. **Reverse** inverse le sens. Pour tester le lien, tournez la source.

Avec **Kind** sur Gear, la cible tourne de −0.5× la rotation source (+0.5× avec Belt). Gear inverse le sens. Belt le conserve. Rack convertit la rotation en glissement. Sa distance par radian est égale à **Ratio** × **Pinion Radius**.

La construction par BoneCraft dépend de la plage de la Hinge source :

- Moins d’un tour complet : contrainte Transform. Elle suit tout ce qui déplace la source, y compris les Sequences.
- Au moins un tour complet : pilote ne nécessitant pas Python. La cible tourne indéfiniment avec la source. Il suit uniquement les poignées et les engrenages. Rig Validator avertit lorsqu’une Sequence ou un Follow serait perdu.

Description de l’image source anglaise (image omise) : commandes de Gear Link avant saisie de l’exemple 20:40. Le rapport illustré vaut 1.00 et les deux nombres de dents valent 0.

*Panneau contextuel natif de compilation de test, version candidate de BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Commandes de Gear Link avant saisie de l’exemple 20:40. Le rapport illustré vaut 1.00 et les deux nombres de dents valent 0.*

### Follow {#follow}

Blade 0–90° soulève Cover 0–40° :

Les deux pièces doivent posséder une Hinge ou Slide. Une Hinge source doit avoir des limites inférieures à un tour complet. BoneCraft refuse une source tournant librement.

1. Sélectionnez **Add Link → Follow**.
2. Cliquez sur la pièce menante (Blade).
3. Cliquez sur la pièce suiveuse (Cover).

Au départ, chaque plage de mappage couvre la plage complète de son articulation.

4. Réglez **Source Range** sur 0…90.
5. Réglez **Target Range** sur 0…40.
6. Pour tester Follow, déplacez la poignée Blade.

Cover suit. Au-delà de l’une des extrémités de plage, la cible conserve sa position. Pour remodeler le mappage dans l’éditeur de graphes, activez **Curve**. BoneCraft n’écrase jamais votre courbe (voir les modifications ci-dessous).

Description de l’image source anglaise (image omise) : plages source et cible de Follow.

*Capture historique d’atelier. Plages source et cible de Follow.*

### Sequence {#sequence}

Enregistrez des étapes pour replier une arme :

1. Dans **3. Sequences**, cliquez sur **Add Sequence**.

Une poignée de curseur nommée `CTRL-SEQ-<name>` est créée.

2. Cliquez sur **Move Slider to End**.

Le curseur passe à sa fin (1). Le bouton devient Record Step suivi du numéro de l’étape suivante.

3. Posez les poignées d’articulation pour la première étape.
4. Cliquez sur Record Step 1.

Chaque poignée déplacée devient une étape avec sa valeur cible. Les poignées reviennent à zéro.

Pour chaque enregistrement supplémentaire :

1. Cliquez sur **Move Slider to End**.
2. Posez les poignées d’articulation pour l’étape suivante.
3. Cliquez sur le bouton Record Step numéroté actuel.

Par défaut, chaque nouvelle étape occupe le quart suivant du curseur. Pour chaque étape enregistrée :

1. Réglez **Target**.
2. Sélectionnez l’interpolation : Linear, Ease In, Ease Out, Ease In Out ou Snap.
3. Réglez **Start**.
4. Réglez **End**.

En dehors de son intervalle, une étape conserve sa valeur finale. Plusieurs Sequences peuvent se cumuler. Pour tester la Sequence, cliquez sur **Test**. Le curseur parcourt 0 → 1 → 0.

À côté du bouton d’enregistrement et de **Test**, la Sequence sélectionnée possède **Detach** (chaîne brisée) et **Delete** (X). Une Sequence mise en attente, par exemple parce que vous avez remodelé la courbe d’une étape, affiche son message et un bouton **Restore**. Restore régénère les étapes depuis l’enregistrement. Keep mine n’est pas proposé pour une Sequence.

Description de l’image source anglaise (image omise) : création d’une Sequence, étapes enregistrées et chronologie.

Description de l’image source anglaise (image omise) : création d’une Sequence, étapes enregistrées et chronologie.

*Capture historique d’atelier. Création d’une Sequence, étapes enregistrées et chronologie.*

## Test {#test}

**Test** (bouton de lecture dans la liste et dans 3. Sequences) fait parcourir toute sa plage à un mécanisme, puis revient. Il n’insère aucune clé et restaure la pose à la fin. Pour arrêter plus tôt, appuyez sur **Esc** : la pose est également restaurée. Pour Gear Link ou Follow, Test balaie la source. Pour Piston, il balaie l’articulation qui le déplace. BoneCraft ne détecte pas les collisions. Surveillez les pièces qui se heurtent.

Description de l’image source anglaise (image omise) : tester le mécanisme sélectionné sur sa plage de mouvement.

*Capture historique d’atelier. Tester le mécanisme sélectionné sur sa plage de mouvement.*

## Forms {#forms}

Dans **4. Controls** :

- Chaque articulation et Sequence possède un curseur. C’est le propre canal de la poignée : la faire glisser et utiliser le curseur sont équivalents.
- **Save Form** enregistre sous un nom toutes les valeurs de poignées et curseurs de Sequences. Renommez la forme dans la liste.
- **Go to Form** règle tous les contrôles sur les valeurs enregistrées.
- **Go and Key** fait de même et insère aussi des clés à l’image courante.
- Le **X** près de la liste retire une forme.

**Anciens fichiers enregistrés :** BoneCraft 9.2.18 lit et applique les formes capturées par les versions antérieures. Ouvrir ou appliquer une forme ne la réenregistre pas. **Save Form** capture les valeurs actuelles des contrôles au format actuel. Enregistrer avec un nom de forme existant remplace les valeurs capturées de cette forme.

Les contrôles restent dans **Mechanisms → 4. Controls**. La correction de compatibilité ne change ni les poignées, ni les curseurs de Sequences, ni les emplacements de panneaux du rig.

Description de l’image source anglaise (image omise) : les commandes Forms montrent les curseurs, Save Form, Go to Form et Go and Key.

*Capture historique d’atelier. Les commandes Forms montrent les curseurs, Save Form, Go to Form et Go and Key.*

## Ce que construit BoneCraft {#what-bonecraft-builds}

Pour chaque pièce :

| Os | Rôle | Visible |
|---|---|---|
| `CTRL-<part>` | Poignée. Sa valeur est le curseur du panneau. Seuls Hinge, Slide et Telescope en créent une. | Oui |
| `MCH-<part>` | Ajoute la poignée et chaque lien, puis applique les limites. | Masqué |
| `DEF-<part>` | Copie `MCH-<part>`. Le maillage lui est lié. Les moteurs reçoivent cet os. | Masqué |

Les os se trouvent dans les collections `Mechanism Controls`, `Mechanism MCH` et `Mechanism DEF`. Une pièce sans articulation n’a que les os `MCH-` et `DEF-`. La poignée d’un Telescope est `CTRL-<telescope name>`. Celle d’une Sequence est `CTRL-SEQ-<name>`. Un Piston ajoute les os `MCH-<part>-aim` et `MCH-<part>-target` pour chacune de ses deux pièces.

Les contraintes de `MCH-<part>` suivent toujours le même ordre : Copy Transforms depuis la poignée, puis la contribution de chaque lien, puis Limit Rotation ou Limit Location de l’articulation. `DEF-<part>` possède une Copy Transforms depuis `MCH-<part>`.

Tout ce que construit BoneCraft porte l’étiquette de son enregistrement : les noms de contraintes commencent par `BC·<id>·<role>` et les os portent les propriétés `bc_mech_id` et `bc_mech_role`. BoneCraft trouve ses os par étiquette, pas par nom ; vous pouvez donc renommer chaque os. Une reconstruction le retrouve sans créer de doublon.

Avec Show Helpers activé, chaque articulation et lien possède une note **How this works**. Elle énumère les contraintes par nom, explique chacune et propose **Select** (flèche) pour examiner l’os.

Vos propres contraintes, pilotes et os ne sont jamais touchés. Une contrainte ajoutée à un os MCH reste sous celles de BoneCraft après une reconstruction.

## Modifications et retouches manuelles {#editing-and-hand-edits}

- **Changements de valeurs** (limites, rapport, plages, chronologie, interpolation, apparence de poignée) : mettent à jour les contraintes existantes sur place, sans reconstruction.
- **Changements structurels** (**Kind** d’un Gear Link, **Curve** d’un Follow, **Stretch** d’un Piston) : remplacent les contraintes de ce mécanisme et reconstruisent uniquement celui-ci.
- **Changed by hand.** Après modification d’une contrainte BoneCraft, par exemple Limit, le message du mécanisme se termine par « (changed by hand) ». BoneCraft n’écrase jamais silencieusement la retouche. Sélectionnez une option :
    - **Keep mine** copie vos valeurs dans l’enregistrement. Il refuse ce qu’il ne peut pas relire. Son message invite à utiliser Restore ou Detach.
    - **Restore** abandonne votre retouche et reconstruit depuis l’enregistrement.
- Un mécanisme en attente bloque aussi les mécanismes utilisant ses os jusqu’à votre décision.
- La même protection s’applique à une courbe remodelée. Avec **Curve** activé, vous pouvez remodeler la courbe d’un Follow dans l’éditeur de graphes. Un changement ultérieur tel que Target Range remplacerait la courbe. Ce changement fait terminer le message du Follow par « (changed by hand) ». **Keep mine** conserve votre courbe. **Restore** la régénère.
- Une Sequence en attente affiche son message et **Restore** dans **3. Sequences**, avec **Detach** et **Delete** à côté. Keep mine n’est pas proposé pour les Sequences.
- **Detach** (chaîne brisée) supprime l’enregistrement et les étiquettes, mais conserve les os et contraintes comme votre rig manuel. Detach et Delete refusent tous deux un enregistrement utilisé par un autre et nomment ses utilisateurs.
- **Delete** (X) supprime l’enregistrement et tout ce que BoneCraft a construit pour lui.
- Une boucle de liens est refusée avant toute construction, et la boucle est nommée, par exemple « Blade Hinge → Cover Follow → Blade Hinge would loop. »

Rig Validator et Task Board signalent :

- Les boucles de liens.
- Les pièces manquantes.
- Les os DEF déplacés de l’extérieur de leur mécanisme.
- Les pilotes nécessitant Python.
- Les Gear Links qui perdent une Sequence ou un Follow.

La vérification des noms du validateur accepte les traits d’union (`CTRL-`, `MCH-`, `DEF-`). Sa vérification des pilotes avertit uniquement sur les expressions nécessitant Python. Un rig Mechanisms propre n’affiche pas d’erreur de validation. Il montre uniquement l’avertissement de l’os `root` décrit dans les limites de cette version.

## Show Helpers {#show-helpers}

**Show Helpers** est une préférence commune à BoneCraft : **Preferences → Add-ons → BoneCraft → Helpers**. La désactiver masque partout le texte pédagogique : lignes quoi / quand, notes **How this works** et phrases complètes des étapes guidées, remplacées par des libellés courts. Les étapes elles-mêmes, listes, Test, avertissements et infobulles de Blender restent toujours présents.

Le bouton **Compact Mode** de VRChat est son raccourci : Compact Mode activé signifie Show Helpers désactivé.

## Limites de cette version {#limits-of-this-version}

- Les mécanismes Click Turn, Track et Linkage viendront plus tard.
- L’exportation des mouvements précalculés vers les moteurs viendra plus tard, après la vérification manuelle sur ordinateur. En attendant, les os `DEF-` sont ceux à exporter.
- BoneCraft ne détecte pas les collisions. Pour les vérifier :
    1. Utilisez Test.
    2. Observez les pièces.
- Un Gear Link tournant librement suit uniquement les poignées et engrenages.
- L’os `root` du rig n’appartient à aucune collection d’os. La vérification des collections de Rig Validator l’indique donc et Task Board affiche « Rig validation warnings (1) ».

Suivant : [Outils VRChat](08-vrchat.md)
