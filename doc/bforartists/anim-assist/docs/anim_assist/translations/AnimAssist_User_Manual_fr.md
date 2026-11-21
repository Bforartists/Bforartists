<a id="anim-assist-12112-candidate-user-guide"></a>

# Guide d'utilisation de la version candidate d'Anim Assist 12.11.2

Ce guide décrit la version candidate locale et non publiée d'Anim Assist 12.11.2. Elle corrige la configuration des bandes sonores à la révision `7ec664d`. Les téléchargements publiés restent à la version 12.11.1. La révision du 20 novembre 2026 a porté sur le code source et la documentation.

Consultez le [journal des modifications actuel](../../../../../../scripts/addons_core/B4_anim_assist/CHANGELOG.md) et l'[index de la documentation](../README.md) pour connaître les informations de version.

Chaque capture d'écran accompagne ses instructions. Sa légende indique la version capturée ou la date de qualification consignée. Les captures anciennes permettent de repérer les commandes. Elles ne constituent pas de nouveaux tests de validation.

Le manuel source anglais utilise principalement des figures de panneaux de la version 12.11.1, capturées dans la compilation fournie de Bforartists 5.2.3, basée sur Blender 5.4 Alpha. Il comprend aussi une figure de synchronisation labiale de la version candidate 12.11.2, capturée sur Bforartists officiel 5.2.3, basé sur Blender 5.3 Alpha. Cette édition localisée utilise de nouvelles captures natives de la version candidate locale et non publiée 12.11.2 ; leurs légendes précisent le contexte de capture et les limites de qualification. Les panneaux contextuels natifs montrent clairement les commandes enregistrées. Pour utiliser un outil, ouvrez son emplacement dans l’éditeur indiqué ci-dessous.

Utilisez la Feuille d’exposition pour les poses et leur placement dans le temps. Utilisez l'Éditeur de graphes pour les courbes d'Action ou les pilotes. Utilisez l’éditeur Animation non-linéaire pour les clips et les corrections. Les commandes d'aide expliquent chaque outil. Les noms de commandes suivent les libellés français vérifiés. Les libellés que l’interface conserve en anglais restent en anglais dans ce guide.

<a id="install-and-find-the-tools"></a>

## Installer et trouver les outils

<a id="install-the-standalone-add-on"></a>

### Installer le complément autonome

1. Téléchargez le [ZIP publié du complément 12.11.1](https://raw.githubusercontent.com/Axleonex/B4Artists_Toolkit/main/releases/b4_anim_assist_v12.11.1.zip).

2. Dans Bforartists, ouvrez **Édition > Préférences > Add-ons > Installer depuis le disque**.

3. Sélectionnez le ZIP.

4. Activez **Anim Assist**.

5. Après une mise à jour, redémarrez Bforartists.

Le paquet autonome s'appelle `B4_anim_assist`. Pendant l'installation, conservez le ZIP intact.

La figure suivante montre le complément intégré à la compilation fournie. Pour une copie autonome, suivez les étapes d'installation du ZIP ci-dessus.

![Préférences d’Anim Assist : le complément activé et ses options générales d’aide au survol sont visibles. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 0e52fe6ce3f5.](images/fr/12.11.1-preferences.png)

<a id="use-a-proposed-built-in-integration"></a>

### Utiliser l'intégration native proposée

La compilation de test personnalisée/native fournie inclut Anim Assist. Ses préférences d'usine activent le complément. Cette intégration proposée ne nécessite aucun ZIP séparé. Cela ne signifie pas que les versions officielles de Bforartists incluent Anim Assist.

1. Démarrez la compilation personnalisée fournie.

2. Ouvrez les emplacements d'éditeurs indiqués ci-dessous.

3. Ouvrez **Édition > Préférences > Add-ons > Anim Assist** pour accéder à ses préférences.

N'installez pas une seconde copie autonome sur l'intégration fournie.

La figure des préférences ci-dessus montre le complément intégré. Les figures **Emplacement dans Scène** et **Configuration initiale** ci-dessous situent ses commandes de configuration.

<a id="find-the-editor-homes"></a>

### Trouver les emplacements dans les éditeurs

La qualification d'exécution antérieure utilisait Bforartists standard 5.2.0, basé sur Blender 5.3.0 Alpha, compilation `0a1ca45552db`, avec OpenGL. Ces preuves historiques concernent cet hôte. Blender standard n'est pas pris en charge. Ces résultats ne valident pas toutes les autres compilations hôtes.

- **Timeline :** la rangée d'outils Anim Assist apparaît en bas de la zone de dessin. Voir **Timeline : la rangée d'outils inférieure** ci-dessous. Les commandes de lecture et de création de clés restent dans l'en-tête natif.
- **Feuille d’exposition, Éditeur de graphes et Animation non-linéaire :** la barre latérale contient un onglet **Anim Assist**. Sa position par rapport aux onglets natifs peut varier. Le menu **Anim Assist** de l'en-tête donne aussi accès aux outils.
- **Contrôleurs :** l'onglet latéral et le menu d'en-tête **Anim Assist** s'adaptent au mode **Contrôleurs** de l'Éditeur de graphes.
- **Propriétés de la scène > Anim Assist :** cet emplacement contient la configuration des personnages, les outils d'animation généraux, les macros, les réglages et l'aide. La barre latérale de la Vue 3D ne contient aucun onglet Anim Assist.

Pour ouvrir les outils de la barre latérale :

1. Placez le pointeur dans la Feuille d’exposition, l'Éditeur de graphes ou l’éditeur Animation non-linéaire.

2. Appuyez sur N.

3. Sélectionnez l'onglet **Anim Assist**.

Pour travailler avec des pilotes, passez l'Éditeur de graphes en mode **Contrôleurs**.

**Propriétés de la scène > Anim Assist > Configuration (une fois par rig) > Lancer la configuration initiale** crée l'étagère rapide générale. La configuration propose aussi un espace de travail. Le menu circulaire facultatif **Maj Alt D** est désactivé au départ. Utilisez **Réglages** pour l'activer ou modifier son raccourci.

![Emplacement dans les propriétés de la scène et groupes d’outils d’Anim Assist. L’étagère rapide et les groupes partagent le même emplacement. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 58734afad3df.](images/fr/12.11.1-scene-home.png)

![Fenêtre de configuration initiale : commandes de première configuration et d’ajout de l’espace de travail Anim Assist, puis contrôles du rig et du visage. Les contrôles désactivés restent visibles. Cette vue identifie les commandes ; aucune configuration n’a été exécutée pour la capture. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 97be05df4471.](images/fr/12.11.1-scene-setup.png)

<a id="timeline-the-bottom-tool-row"></a>

## Timeline : la rangée d'outils inférieure

La rangée d'outils apparaît en bas de la Timeline, au-dessus de la barre de défilement horizontale native. Elle n'ajoute aucun en-tête, région ni découpage d'espace de travail. Les commandes de lecture et de création de clés restent dans l'en-tête natif. Pour afficher ou masquer la rangée, utilisez **Timeline > Vue > Afficher la rangée d’outils Anim Assist**.

Les boutons conservent leur hauteur complète et des zones de clic correspondantes. Le redimensionnement réserve de la place au-dessus de la barre de défilement. Si vous relâchez la séparation sous la hauteur minimale, la Timeline rétablit assez de hauteur pour la rangée. La barre traite ses clics avant les commandes natives de tête de lecture et de sélection des clés. Conservez assez de hauteur au-dessus pour examiner les clés.

De gauche à droite, la rangée contient :

| Commande | Fonction |
|---|---|
| **Bouton d'étape** (par exemple **Tout**, avec une petite flèche) | Affiche l'étape actuelle et ouvre la liste des étapes. |
| **Boutons de famille** (Pose intermédiaire, Rythme, Courbes, Clés, Pose, Précalculer, Mouvement) | Les noms colorés ouvrent la liste complète de leur famille. Les outils de la rangée suivent chaque nom de famille. |
| **Outils** | Les boutons, icônes et curseurs exécutent les outils. Le texte de survol explique chaque outil. |
| **+N** | Ouvre la liste des N outils qui ne tiennent pas dans la rangée. |
| **Trouver un outil** (loupe) | Recherche ou affiche les 96 outils. Chaque résultat permet d'exécuter ou d'épingler l'outil. |
| **Réglages** | Ouvre les Réglages de la barre d’outils pour configurer chaque rangée. |

1. Cliquez sur un bouton d'étape, de famille ou sur **+N** pour ouvrir sa liste.

2. Cliquez sur un élément pour l'utiliser.

La liste reste ouverte pendant le déplacement du pointeur, même sur un autre éditeur. Cliquer sur un autre bouton de famille affiche cette famille.

Pour fermer la liste, cliquez de nouveau sur le même bouton, cliquez ailleurs ou appuyez sur **Échap**.

![Rangée inférieure de la Timeline. Le sélecteur d’étape, les familles, les outils, Trouver un outil et Réglages occupent une même rangée. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : b6bf04a3afa9.](images/fr/stage-all.png)

<a id="tool-families"></a>

### Familles d'outils

Chaque famille regroupe les commandes selon leur fonction. Le texte de survol de chaque outil indique sa portée et ses conditions d'utilisation.

| Famille | Travail disponible |
|---|---|
| **Pose intermédiaire** | Pourcentages et glissement de poses intermédiaires, création d'intermédiaires, répartition, rapprochement ou éloignement des poses voisines. |
| **Rythme** | Décalages par images, préréglages d'espacement, curseurs temporels, décalage en cascade, insertion/suppression de temps, répartition, inversion et arrondi. |
| **Courbes** | Interpolation par spline ou par paliers, mélange vers les voisins/la référence, assouplissement, amplification, lissage, poignées et signets de référence. |
| **Clés** | Sélection des clés visibles, d'un intervalle et des extrémités, extension de sélection, types de clés, sélection des intermédiaires, Copier et Coller. |
| **Pose** | Miroir, sélection du côté opposé, échange, alignement, correspondance au monde/parent/cible et changement de propriétés de rig configurées. |
| **Précalculer** | Précalcul d'objet ou de plage d'aperçu, précalcul intelligent, réduction, placement sur des images entières, création de proxies, précalcul de session et nettoyage. |
| **Mouvement** | Trajectoires dans l'espace monde, actualisation, diagnostic des arcs, décalage de l'Action active et masque d'intervalle. |

![Partie supérieure du menu vertical de la famille Pose : commandes de miroir et de sélection, puis premières commandes de correspondance. La figure 6 poursuit le même menu ; les premières commandes de correspondance sont communes aux deux vues. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 2eac4fa6c5e1.](images/fr/12.10.0-pose-family-left.png)

![Partie inférieure du menu vertical de la famille Pose : commandes de correspondance, changement de mode du rig, options de pose et ouverture du panneau Anim Assist. La figure 5 montre le haut du même menu. Les commandes indisponibles dans ce contexte restent visibles. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 9cee78965b15.](images/fr/12.10.0-pose-family-right.png)

<a id="choose-a-stage"></a>

### Choisir une étape

Une étape contient les outils d'une phase d'animation :

- **Tout :** vue d'ensemble avec des outils de chaque famille.
- **Ébauche :** outils des familles Pose intermédiaire et Clés pour établir les poses.

- **Courbes :** outils Courbes et Mouvement pour travailler les courbes et vérifier les arcs.

- **Finition :** outils Rythme et Pose pour l'espacement et la symétrie.

- **Livraison :** outils de la famille Précalculer pour terminer et exporter.

Pour changer d'étape :

1. Cliquez sur le bouton d'étape à gauche de la rangée.

2. Cliquez sur une étape dans la liste au-dessus.

La liste se ferme après la sélection. Si la Timeline est basse, les cinq choix occupent une rangée dans la zone de dessin utilisable.

Vous pouvez aussi sélectionner une étape dans **Timeline > Vue > Étape Anim Assist**.

Pour parcourir les étapes avec la molette :

1. Maintenez **Ctrl** au-dessus du bouton d'étape.

2. Tournez la molette.

Chaque espace de travail conserve sa propre étape dans le fichier enregistré.

![Liste des cinq étapes, ouverte au-dessus du sélecteur d’étape, avec la famille Pose intermédiaire et son curseur d’interpolation visibles dans la barre d’outils. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 71fd4ec44a54.](images/fr/12.10.0-stage-choices.png)

<a id="use-the-tools"></a>

### Utiliser les outils

Les boutons et les icônes exécutent un outil au clic. Les icônes de type de clé utilisent les couleurs du thème de la Feuille d’exposition. Les losanges d'intermédiaires sont plus petits. Les losanges d'extrêmes sont plus grands. Les icônes de poignées utilisent les couleurs de l'Éditeur de graphes.

1. Survolez une icône pour lire son nom.

2. Si un outil est grisé, survolez-le pour lire sa condition, par exemple la sélection de clés.

3. Cliquez sur un bouton ou une icône disponible pour exécuter l'outil.

Les **curseurs intégrés** restent dans la rangée. Un clic sans glissement ne change rien.

1. Faites glisser la piste pour prévisualiser le changement.

2. Relâchez le bouton du pointeur pour appliquer le changement.

Pendant le glissement, appuyez sur **Échap** ou faites un clic droit pour annuler. L'annulation rétablit les clés d'origine.

- Pour un mouvement plus fin, maintenez **Maj** pendant le glissement.
- Pour accrocher au pas de l'outil, maintenez **Ctrl** pendant le glissement.

Pour définir une valeur exacte pendant le glissement :

1. Saisissez le nombre.

2. Appuyez sur **Entrée** pour l'appliquer.

Les **graduations** sont des préréglages sur la piste d'un curseur. Le glissement s'accroche aux graduations proches. Cliquez sur une graduation pour appliquer sa valeur exacte.

Le nombre à droite d'un curseur intégré ouvre un champ de valeur exacte. Pour appliquer la valeur par défaut de l'outil, appuyez sur **R**.

Les **curseurs détachables** affichent leur nom dans la rangée. Le glissement et le clic ouvrent des modes différents.

Pour ouvrir un curseur temporaire :

1. Faites glisser le nom pour ouvrir le curseur.

2. Relâchez le bouton du pointeur pour appliquer le changement.

Pour garder le curseur ouvert :

1. Cliquez une fois sur le nom.

2. Faites glisser la piste pour prévisualiser le changement.

3. Double-cliquez ou cliquez ailleurs pour appliquer le changement.

Pour annuler un changement dans ce curseur, appuyez sur **Échap**.

Pour ouvrir les **Réglages des outils d’animation**, faites un clic droit sur l'outil.

Les dix curseurs numériques sont Pose intermédiaire, Lisser, Voisines, Vers la référence, Lissage, Amplifier, Échelle de rythme, Décalage du rythme, Propagation et Réduire.

- **Pose intermédiaire** mélange la pose précédente et la suivante. Les valeurs inférieures à 0 % ou supérieures à 100 % dépassent ces poses.
- **Échelle de rythme** change l'espacement des clés. Sous 100 %, les clés se rapprochent et la lecture accélère. Au-dessus de 100 %, les clés s'éloignent et la lecture ralentit. **Décalage du rythme** déplace l'Action de l'objet actif dans le temps.
- **Propagation** déplace les clés après la tête de lecture selon le nombre d'images choisi. Vers les images antérieures, le déplacement s'arrête une image après la tête de lecture.
- **Réduire** supprime des clés si le changement de courbe reste sous la tolérance choisie. Les clés disparaissent pendant l'aperçu. Appuyez sur **Échap** pour les rétablir.
- **Vers la référence** mélange vers l'image de référence. **Définir la référence** mémorise cette image. **Amplifier** met le mouvement à l'échelle autour de cette référence.

Les outils portant sur toute l'Action, comme Décalage du rythme, dépassent la sélection des clés. Avant de changer toute une Action, vérifiez le texte de survol et les options de scène.

![Curseur détachable Échelle de rythme, ouvert au-dessus de sa commande, avec son titre, sa piste et la valeur 100.0 %. L’instruction reste en anglais en raison d’une lacune du catalogue source. Elle signifie : faites glisser pour ajuster ; double-cliquez ou cliquez en dehors du contrôle pour appliquer ; Échap annule. Cette capture documente ce repli réel et ne prouve pas une interface intégralement traduite. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 7e86840d22ed.](images/fr/12.10.0-timing-popout.png)

<a id="default-rows"></a>

### Rangées par défaut

Chaque rangée possède un ensemble par défaut fixe. Les listes suivantes donnent les commandes de gauche à droite, dans l'ordre de travail.

- **Tout :** la rangée commence par le curseur Pose intermédiaire, gradué à 25, 50 et 75 %. Viennent ensuite les icônes -1f/+1f et le curseur détachable Échelle de rythme. Puis viennent le curseur Lisser et les icônes Copier, Coller, Symétriser la sélection, Précalculer l’objet et Traînées, dans cet ordre. L'œil Traînées affiche ou masque les trajectoires dans l'espace monde.

![Étape Tout, détail de gauche de la rangée d’outils. La figure 4 situe Trouver un outil et Réglages dans la rangée complète. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 5c56af3a3932.](images/fr/12.10.0-all-row-left.png)

![Étape Tout, détail de droite de la même rangée. Le chevauchement avec la figure 9 permet de raccorder les deux vues sans couper les groupes de commandes. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : b9f510d00f2c.](images/fr/12.10.0-all-row-right.png)

- **Ébauche :** le curseur Pose intermédiaire va de -25 % à 125 %. Ses graduations sont -25, 25, 50, 75 et 125. Celles de -25 et 125 dépassent les poses limites. Celles de 25 et 75 mélangent vers ces poses. Les icônes Pose intermédiaire et Répartir suivent le curseur. Viennent ensuite Sélectionner une plage d’images, Toutes les clés et Fins, puis Étendre à gauche et à droite. Les losanges Marquer comme image clé, Pose intermédiaire, Extrême et Maintien mobile suivent. Copier et Coller terminent la rangée.

![Étape Ébauche, détail de gauche de la rangée d’outils. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 0abe6e06cd35.](images/fr/12.10.0-block-row-left.png)

![Étape Ébauche, détail de droite de la même rangée, avec un chevauchement de la figure 11. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 469a71b65008.](images/fr/12.10.0-block-row-right.png)

- **Courbes :** l'icône de courbe Vers la spline vient en premier. Les curseurs Voisines, Lissage et Lisser suivent. Viennent ensuite la cible Définir la référence, puis Vers la référence et Amplifier. Les icônes de poignées Automatique limité, Vecteur et Libre suivent. Traînées termine la rangée.

![Étape Courbes, détail de gauche de la rangée d’outils. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 5987f0daa281.](images/fr/12.10.0-spline-row-left.png)

![Étape Courbes, détail de droite de la même rangée, avec un chevauchement de la figure 13. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : c9dcc89ebf37.](images/fr/12.10.0-spline-row-right.png)

- **Finition :** la rangée commence par -1f/+1f. Le curseur Échelle de rythme suit, gradué à 80, 90, 110 et 120 %. Viennent ensuite Décalage du rythme et Propagation. Ce dernier possède des graduations à -1 et 1. Accrocher suit et arrondit les temps des clés. Les icônes Sélectionner le côté opposé, Symétriser la sélection, Symétriser l’actif et Échanger terminent la rangée.

![Étape Finition, détail de gauche de la rangée d’outils. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : c78e21a68dcf.](images/fr/12.10.0-polish-row-left.png)

![Étape Finition, détail de droite de la même rangée, avec un chevauchement de la figure 15. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : c2c03daed0aa.](images/fr/12.10.0-polish-row-right.png)

- **Livraison :** l'icône Précalculer l’objet vient en premier, suivie de Précalculer la plage d’aperçu et Précalcul intelligent. Le curseur Réduire suit, gradué à 0.001, 0.01 et 0.05. Précalculer les clés sur des images entières vient ensuite et conserve un instantané Réinitialiser le rythme. Proxy et précalcul en un clic suit. Viennent ensuite les proxies Position, Rotation, Monde et Parent. Précalculer la session et supprimer les proxies suit ces icônes. Supprimer toutes les sessions de proxy termine la rangée.

![Étape Livraison, détail de gauche de la rangée d’outils. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 7713b395a2de.](images/fr/12.10.0-deliver-row-left.png)

![Étape Livraison, détail de droite de la même rangée, avec un chevauchement de la figure 17. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 83fa10e1f768.](images/fr/12.10.0-deliver-row-right.png)

**Trouver un outil** inclut les outils absents de la rangée. Par exemple, **Vers les paliers** et les boutons **Pose intermédiaire 25/50/75 %**.

**Copier** inclut les poignées. **Coller** d'Anim Assist utilise les temps copiés. Le collage natif peut plutôt s'aligner sur la tête de lecture. Avant de remplacer ces outils par un raccourci natif, consultez son infobulle.

La vue d'ensemble situe les commandes. Les détails de chaque rangée se chevauchent pour garder les libellés lisibles. Les figures des listes de familles montrent les commandes supplémentaires.

<a id="find-and-more"></a>

### Trouver un outil et Plus

**Trouver un outil**, représenté par une loupe, contient tous les outils.

1. Cliquez sur la loupe.

2. Saisissez une partie du nom d'un outil, d'une famille ou un terme, comme « espacement » ou « arc ».

3. Cliquez sur un outil pour l'exécuter.

Pour parcourir les outils sans recherche :

1. Laissez le champ de recherche vide.

2. Sélectionnez un onglet de famille.

Pour ajouter ou retirer un outil de la rangée actuelle, cliquez sur son épingle.

Une épingle allumée indique que l'outil figure dans la rangée actuelle.

L'épinglage concerne la rangée actuelle, quelle que soit la famille de l'outil. **Trouver un outil** et **Réglages de la barre d’outils** partagent une disposition. Tout changement apparaît dans les deux.

Si N outils dépassent la largeur de la Timeline, **Plus** apparaît sous la forme **+N**, avant Trouver un outil. Si tous les outils tiennent, Plus disparaît.

Pour exécuter un outil depuis Plus :

1. Cliquez sur **+N**.

2. Cliquez sur l'outil.

Pour gagner de la place, élargissez la Timeline ou raccourcissez les curseurs intégrés. Vous pouvez aussi afficher les outils moins utilisés comme curseurs détachables ou boutons.

![Fenêtre complète Trouver un outil : recherche vide, sept onglets de familles, instruction, dix outils de la famille Pose intermédiaire et icônes d’épingle allumées ou éteintes. Le premier onglet correspond à Pose intermédiaire et conserve son abréviation native « Pose intermé... » ; il est distinct de l’onglet Pose. Aucun outil n’a été exécuté et aucune épingle n’a été modifiée pour cette capture. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 796a06e791a4.](images/fr/12.10.0-find-tools.png)

![Partie supérieure du menu de débordement actuel, en une seule colonne : en-tête et trois premières commandes complètes. Cette vue et la figure 21 se chevauchent sur toute la ligne du précalcul des transformations d’objet. Elle remplace l’ancienne illustration en colonnes. Le menu rejoint le bord droit natif de la fenêtre de 710 pixels de large ; aucune marge extérieure n’a été ajoutée. Aucun outil ni aucune épingle n’a été actionné pour cette capture. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 8ce8394ee69e.](images/fr/12.10.0-more-left.png)

![Partie inférieure du même menu de débordement en une seule colonne : trois dernières commandes complètes. La ligne du précalcul des transformations d’objet figure aussi dans la vue supérieure de la figure 20. La dernière commande, Coller, est grisée. Le menu rejoint le bord droit natif de la fenêtre de 710 pixels de large ; aucune marge extérieure n’a été ajoutée. Aucun outil ni aucune épingle n’a été actionné pour cette capture. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 5c1f436ec535.](images/fr/12.10.0-more-middle.png)

![Menu de débordement actuel complet en une seule colonne, avec ses cinq commandes et l’ouvre-menu +5 visible. La commande Coller est grisée. Cette disposition actuelle remplace l’ancienne illustration répartie en trois colonnes. Le menu rejoint le bord droit natif de la fenêtre de 710 pixels de large ; aucune marge extérieure n’a été ajoutée. Aucun outil ni aucune épingle n’a été actionné pour cette capture. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : bdae27abd25c.](images/fr/12.10.0-more-right.png)

<a id="undo-from-find-menus-and-the-toolbar"></a>

### Annuler depuis Trouver un outil, les menus et la barre d'outils

Dans la version 12.11.1, les actions de **Trouver un outil** et des menus natifs utilisent l'entrée Annuler native de l'outil. Elles n'ajoutent pas une seconde entrée pour la même modification. Les actions directes dans la barre de la zone de dessin conservent leur point de restauration Annuler requis. La fin et l'annulation des glissements gardent un traitement distinct.

1. Terminez l'action ou le glissement du curseur.

2. Utilisez **Annuler** natif pour rétablir le résultat précédent.

3. Examinez les clés et le mouvement avant de continuer.

Certaines commandes de sélection, de navigation dans les réglages ou sans modification ne créent aucune entrée d'annulation d'animation. Les entrées d'historique varient selon les commandes.

![Partie supérieure du menu Édition natif : Annuler et Refaire sont actuellement désactivés, tandis que le sous-menu Historique d’annulation reste disponible. La capture s’arrête avant le groupe Répéter ; elle ne montre ni le menu complet ni l’exécution de ces commandes. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 9b601ca1ce95.](images/fr/5.2.3-native-undo-menu.png)

<a id="change-what-a-row-shows"></a>

### Changer le contenu d'une rangée

1. Cliquez sur **Réglages** à droite de la rangée.

2. Dans **Ligne**, sélectionnez **Tout**, **Ébauche**, **Courbes**, **Finition** ou **Livraison**.

3. Cliquez sur un en-tête de famille pour ouvrir ses outils.

4. Pour chaque outil, sélectionnez son mode d'**Affichage**.

5. Pour les outils avec une icône, sélectionnez **Libellé / Icône**.

6. Pour un curseur intégré, définissez plutôt sa **Largeur** dans le second champ.

7. Pour déplacer un outil dans sa famille, cliquez sur ses **flèches haut et bas**.

8. Pour ouvrir ses Réglages des outils d’animation, cliquez sur son **engrenage**.

9. Cliquez hors du panneau ou appuyez sur **Échap** pour le fermer.

Les outils ordinaires proposent les modes Masqué et Bouton. Masqué retire l'outil de la rangée. Les curseurs proposent aussi Curseur flottant et Curseur intégré.

Le panneau **Réglages de la barre d’outils** s'ouvre sur la rangée actuelle. Son sélecteur **Ligne** prévisualise une autre rangée pendant l'édition. Chaque en-tête de famille indique son nombre d'outils visibles. Une étape ouvre d'abord ses familles principales. Utilisez **Trouver un outil** au-dessus des familles pour filtrer les noms.

Les changements apparaissent immédiatement. Fermer le panneau par un clic extérieur ou avec Échap les conserve. Le panneau n'a aucun bouton OK. **Annuler les modifications** remet toutes les rangées dans leur état à l'ouverture du panneau. Chaque rangée peut contenir n'importe quel outil. Ajouter un outil d'une autre famille ajoute aussi son bouton de famille.

L'affichage par icônes prend en charge les types de clés et de poignées, l'extension de sélection, -1f/+1f, Pose intermédiaire et Répartir. Il prend aussi en charge Vers la spline, Vers les paliers, Définir la référence, Copier et Coller. Il inclut Symétriser la sélection, Symétriser l’actif, Sélectionner le côté opposé et Échanger. Précalculer l’objet, les quatre types de proxies et Traînées sont aussi disponibles. Les autres outils affichent leur nom.

L'engrenage ou un clic droit sur un outil de la rangée ouvre les **Réglages des outils d’animation**. Ce panneau configure l'affichage, l'intervalle, la valeur par défaut, la largeur, la précision et la sensibilité du glissement. Il configure aussi l'accrochage, les préréglages et **Préréglages en graduations**. **Plage personnalisée / dépassement** autorise un intervalle personnalisé dans les limites de l'outil.

Chaque étape conserve son propre affichage, ses libellés, ses préréglages et ses graduations. Les autres valeurs sont communes aux rangées. Les réglages de scène stockent les masques, les cibles et les ancrages des intermédiaires. **Options des outils de scène** ouvre ces réglages.

| Réglage | Limite |
|---|---|
| Largeur du curseur | 80–240 pixels logiques. Les rangées étroites peuvent raccourcir la piste affichée. |
| Précision | 0–4 décimales. |
| Sensibilité | 10–2 000 pixels sur l'intervalle d'un curseur détachable. |
| Préréglages | Au plus 12 valeurs finies dans l'intervalle autorisé. |
| Intervalle personnalisé du curseur Pose intermédiaire | -100 % à 200 %. |
| Intervalle personnalisé d'Échelle de rythme | Minimum 1 %. |
| Intervalle personnalisé de Propagation | -500 à 500 images. |
| Intervalle personnalisé de Réduire | 0 à 1 unité de tolérance. |

L'intervalle standard affiché peut être plus étroit que l'intervalle personnalisé autorisé. Ces limites de configuration ne recommandent aucune tolérance pour les rigs de production.

![Partie supérieure visible des Réglages de la barre d’outils : disposition, préréglages, sélecteur de rangée, recherche et dix lignes du groupe d’interpolation, avec leurs commandes d’affichage, de largeur, d’ordre et de réglages. Les points de suspension natifs de l’instruction et de deux libellés longs sont conservés. La capture ne montre pas toute la boîte de dialogue et ne garantit pas que tous les textes tiennent dans les contrôles. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : fa194243431c.](images/fr/12.10.0-toolbar-settings.png)

![Boîte de dialogue des réglages de l’outil, avec tous les contrôles affichés et les boutons OK et Annuler entièrement visibles. Les points de suspension natifs de l’instruction sont conservés ; l’indication inférieure relative aux options de scène déborde et se trouve tronquée près du bord droit de l’écran. La capture ne garantit pas que tous les textes tiennent dans la boîte. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 87afe7f2ec14.](images/fr/12.11.1-tool-settings.png)

<a id="save-load-and-reset-layouts"></a>

### Enregistrer, charger et réinitialiser les dispositions

Une disposition contient toutes les rangées : Tout et les quatre étapes.

| Commande | Résultat |
|---|---|
| **Enregistrer sous** | Nomme et enregistre la disposition actuelle. |
| **Charger** | Rétablit une disposition enregistrée. |
| **Mettre à jour l’enregistrement** | Remplace la disposition enregistrée par les rangées actuelles. |
| **Renommer** et **Supprimer** | Renomment ou suppriment les dispositions enregistrées. |
| **Recommandée** | Identifie la disposition intégrée fixe. |
| **Rétablir les valeurs par défaut de Ébauche** | Rétablit l'ensemble par défaut de cette étape. Le nom de la commande suit la rangée modifiée. |
| **Restaurer la disposition recommandée** | Rétablit Tout et chaque étape. Les dispositions enregistrées restent disponibles. |

Les préférences du complément stockent les dispositions. Elles s'appliquent à toutes les Lignes du temps.

Si les Préférences ne s'enregistrent pas automatiquement, cliquez sur **Enregistrer les préférences** dans les Réglages de la barre d’outils. Cela conserve les changements après un redémarrage.

Les noms des dispositions enregistrées contiennent 1–64 caractères. La bibliothèque accepte au plus 100 dispositions. Charger une disposition remplace l'agencement de travail. Avant de remplacer un agencement modifié, lisez la commande signalant les changements non enregistrés.

Les étapes commencent avec des valeurs par défaut fixes. Ajouter un outil à Tout ne l'ajoute pas à une étape. Ajoutez-le séparément à chaque étape nécessaire. Les Préférences du complément ne contiennent aucune commande d'étape. Chaque espace de travail utilise le bouton d'étape de la rangée.

La figure **Réglages de la barre d’outils** ci-dessus montre les commandes des dispositions enregistrées. Ce panneau sert à configurer les rangées et à gérer les dispositions.

<a id="hover-explanations-and-shortcuts"></a>

### Explications de survol et raccourcis

Pour lire l'explication d'une commande, maintenez le pointeur dessus pendant environ une demi-seconde. Le réglage **Explications au survol** détermine la quantité d'aide. Ce réglage se trouve dans Édition > Préférences > Add-ons > Anim Assist > Général.

L'aide de survol, les choix d'étape et les curseurs détachables restent au-dessus des boutons. La Timeline affiche une seule infobulle Anim Assist sous le pointeur. L'aide de la barre prime sur l’outil Scene Strip Gizmo situé dessous.

- **Complet :** le texte explique la fonction, la portée, les conditions et l'utilisation de l'outil.
- **Court :** le texte donne le nom et une ligne d'explication. Pour un outil grisé, il indique aussi la raison.
- **Désactivé :** la rangée n'affiche aucune aide de survol Anim Assist. Les boutons natifs des panneaux et menus Anim Assist affichent encore le nom de l'outil. Bforartists y affiche toujours une ligne de description. Les champs de réglage conservent leur infobulle d'une ligne.

Pour désactiver toutes les infobulles, utilisez **Édition > Préférences > Interface > Infobulles**.

Le texte de survol ne cite un raccourci que si une affectation existe :

- **Raccourci :** cette touche correspond à cet outil Anim Assist précis. Les outils de la rangée n'ont aucun raccourci par défaut. Pour en afficher un ici, affectez-le dans **Édition > Préférences > Ensemble de raccourcis**.
- **Bforartists key :** cette touche exécute une commande native de même fonction. La Feuille d’exposition utilise notamment **Ctrl C** pour Copier et **Ctrl V** pour Coller. **A** sélectionne toutes les clés. **Ctrl Pavé numérique +** étend la sélection des deux côtés. **R** redimensionne le placement temporel des clés. **W** déplace les clés dans le temps. Les commandes natives peuvent différer des outils Anim Assist. Coller natif utilise la tête de lecture au lieu des temps copiés.

![Explication de survol complète de Lisser les clés (glisser), avec la commande Lisser mise en évidence. L’outil rapproche les clés sélectionnées de la moyenne de leurs voisines immédiates et indique la portée modifiable. Faites glisser pour prévisualiser ; relâchez pour appliquer ; Échap annule. Un clic droit ouvre les réglages de l’outil. Cette capture ne présente aucune ligne de raccourci. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : bae080f9780f.](images/fr/12.10.0-hover-explanation.png)

La figure **Préférences d'Anim Assist intégré**, près de l'installation, montre **Complet**, **Court** et **Désactivé**. La figure **Réglages**, plus loin, montre les options de raccourcis et de menus.

<a id="dope-sheet-poses-and-key-timing"></a>

## Feuille d’exposition : poses et placement des clés dans le temps

Le résumé compte les propriétaires visibles, les courbes modifiables et les clés sélectionnées. Il contient les commandes de sélection Tout/Aucun. Le groupe **Ébauche et interpolation** est ouvert au départ. Les autres groupes sont **Rythme, Clés et canaux, Pose et correspondance, Précalculer et terminer et Étagère rapide**.

1. Sélectionnez un objet animé ou des os de pose.

2. Affichez les canaux de l'Action.

3. Sélectionnez les clés à modifier.

4. Utilisez **Ébauche et interpolation** pour les pourcentages d'intermédiaires, leur création et les outils de glissement.

5. Développez les options du groupe **Ébauche et interpolation** pour les masques, les préréglages et les choix d'échantillonnage.

6. Utilisez **Rythme** pour l'espacement, les décalages et le décalage en cascade.

7. Utilisez **Clés et canaux** pour la sélection, la gestion des clés et leurs métadonnées.

8. Utilisez **Pose et correspondance** pour les correspondances et les miroirs.

9. Utilisez **Précalculer et terminer** pour les outils de précalcul et de diagnostic.

Pour sélectionner les côtés des poignées, utilisez l'Éditeur de graphes. La Feuille d’exposition conserve les types de poignées avancés. Les Propriétés de la scène contiennent la création de macros et la configuration.

![Vue supérieure de la Feuille d’exposition avec la barre latérale Anim Assist, la famille Ébauche et interpolation déployée et les autres en-têtes de familles visibles. Le contexte affiché compte deux propriétaires d’animation, 15 clés sélectionnées et six courbes modifiables. Les identifiants longs gardent leur troncature native. Cette vue ne démontre pas l’exécution des outils. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 90c5d5b34e43.](images/fr/12.8.0-dopesheet-tools.png)

<a id="breakdown-anchors"></a>

### Ancrages des intermédiaires

Sur une image vide, les clés environnantes servent d'ancrages au mélange. Par exemple, les valeurs 0 et 10 donnent 5 à 50 %.

Si la tête de lecture possède déjà une clé, celle-ci devient l'ancrage précédent. Une valeur actuelle de 5 et une valeur suivante de 10 donnent 7.5 à 50 %. Répéter l'opération peut encore modifier la clé existante.

Avant d'appliquer un intermédiaire, vérifiez la tête de lecture, les clés et les masques.

La figure de la Feuille d’exposition ci-dessus montre les actions d'intermédiaires et leurs options. Chaque exemple numérique décrit une autre disposition de clés et de tête de lecture.

<a id="graph-editor-curve-shaping"></a>

## Éditeur de graphes : modeler les courbes

**Modeler les courbes** s'ouvre avec les actions directes de modelage, d'interpolation et de poignées. Les groupes sont **Sélection et canaux, Modeler les courbes, Modifier le rythme, Nettoyer, Pose et précalcul et Étagère rapide**. **Sélection et canaux** inclut la sélection des poignées. **Nettoyer** contient la gestion des clés et les diagnostics. **Pose et précalcul** inclut les correspondances, les miroirs, les intermédiaires et le précalcul. Ses **Options des poses intermédiaires**, repliées, configurent l'échantillonnage des intermédiaires. Elles ne configurent pas l'interpolation générale des courbes.

1. Sélectionnez les clés d'Action visibles et modifiables.

2. Appliquez l'action de modelage ou d'interpolation.

3. Examinez la courbe obtenue et la vue.

L'interpolation des clés sélectionnées ne touche que les clés sélectionnées, modifiables et visibles. Les commandes temporelles du Gestionnaire de clés respectent la visibilité de l'éditeur et les verrouillages des canaux. **Déplacer les clés** et **Insérer des images** s'exécutent immédiatement. Pour ajuster leurs valeurs, utilisez **Ajuster la dernière opération** natif.

Les aides de sélection d'Action prennent en charge les **Actions d'objet**. Si la portée est vide, elles ne sélectionnent pas toute l'Action active. Elles excluent les Actions épinglées détachées et les sources qui ne sont pas des objets. La barre latérale explique ces exclusions. Avant d'utiliser un outil sur toute une Action, consultez sa description.

![Vue de l’Éditeur de graphes en mode F-Curves, avec six clés sélectionnées, trois courbes modifiables et la famille Modeler les courbes déployée dans la barre latérale Anim Assist. Les courbes affichées sont presque plates ; cette vue ne constitue ni un exemple de courbes modelées ni une preuve d’exécution des outils. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 9ede4f7c0f7c.](images/fr/12.8.0-graph-tools.png)

<a id="drivers-inspect-and-shape-driver-responses"></a>

## Contrôleurs : examiner et modeler leurs réponses

Pour utiliser les outils de pilotes, passez l'Éditeur de graphes en mode **Contrôleurs**. La barre latérale et le menu d'en-tête **Anim Assist** affichent quatre sections propres aux pilotes. Revenir aux courbes d'Action rétablit les groupes d'Action décrits ci-dessus. Le mode Contrôleurs utilise les canaux de pilotes au lieu des outils de clés d'Action.

<a id="driver-target"></a>

### Pilote et cible

Cette section compte les pilotes visibles sélectionnés. Pour le pilote actif, elle affiche aussi **Propriétaire**, **Propriété** et **Valeur actuelle**. Elle affiche un **Indice de tableau** si nécessaire. Une propriété non résolue produit un avertissement.

1. Sélectionnez un canal de pilote visible dans la liste des canaux.

2. Examinez son propriétaire et sa propriété pilotée dans **Pilote et cible**.

3. Cliquez sur **Cadrer la sélection** pour cadrer les courbes sélectionnées.

4. Pour voir l'ensemble des pilotes, cliquez sur **Tout cadrer**.

**Tous les canaux** et **Aucun** changent la sélection des canaux. **Sélectionner le propriétaire** rend actif l'objet qui possède le pilote. Les autres objets sélectionnés le restent. Le propriétaire doit appartenir au calque de vue actuel, rester visible et autoriser la sélection. Les pilotes d'autres blocs de données ne peuvent pas utiliser cette sélection d'objet.

Si le propriétaire est modifiable, **Désactivé** et **Verrouillé** changent les réglages natifs du canal du pilote actif. Un seul pilote visible sélectionné reste accessible pour l'inspection après verrouillage. Pour le déverrouiller, désactivez **Verrouillé**. Si plusieurs canaux sélectionnés rendent le pilote actif ambigu, sélectionnez explicitement le canal voulu.

Sans sélection, les quatre sections restent visibles et donnent des indications. Elles ne créent aucun pilote.

Avant d'utiliser ces sections :

1. Créez des pilotes avec la procédure native de Bforartists.

2. Reliez ces pilotes.

![Barre latérale des pilotes d’Anim Assist avec un pilote sélectionné de Empty sur scale&#91;0&#93;, déverrouillé et non mis en sourdine. Une variable alimente l’expression var + 1.0, dont la sortie actuelle vaut 1. Les points de réponse ne sont pas sélectionnés : Interpolation et Poignées sont donc grisés. Le libellé Ajouter un modificateur (actif) est entièrement visible à cette largeur. Aucune réponse n’a été modifiée. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-21 (UTC). SHA-256 de l’image (préfixe) : bce8e89881d6.](images/fr/12.11.0-selected-driver.png)

<a id="variables-expression"></a>

### Variables et expression

Cette section compte les variables. Les pilotes scriptés affichent **Expression**. Les autres types affichent **Type**. L'onglet natif **Contrôleurs** contient les réglages complets et modifiables des variables et de l'expression.

1. Déverrouillez le canal de pilote voulu.

2. Cliquez dessus pour en faire le pilote actif et modifiable natif.

3. Ouvrez **Variables et expression**.

4. Cliquez sur **Ouvrir les réglages du pilote**.

5. Modifiez les variables, les cibles, le type de pilote ou l'expression dans l'onglet natif **Contrôleurs**.

6. Revenez à **Anim Assist** pour les actions de réponse et les diagnostics.

Le bouton ouvre la catégorie native de la barre latérale. Il n'ouvre pas une copie séparée de la boîte de dialogue des réglages. Un pilote verrouillé peut rester accessible à l'inspection sans rendre ses réglages natifs modifiables. L'ordre des onglets natifs peut varier. Repérez **Contrôleurs**, **Modificateurs** et **Anim Assist** par leur nom.

![Réglages natifs du pilote de l’échelle X de Empty, soit scale&#91;0&#93; : expression scriptée var + 1.0, variable var ciblant la position X de Empty en espace monde, entrée de 0,000 et sortie de 1,000. Le libellé de la valeur pilotée conserve ses points de suspension natifs ; il désigne la valeur actuelle du pilote. Les identifiants de données et l’expression sont inchangés. Aucun réglage n’a été modifié. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-21 (UTC). SHA-256 de l’image (préfixe) : 0ee91da67e51.](images/fr/12.11.0-native-driver-settings.png)

<a id="response-curve"></a>

### Courbe de réponse

L'axe horizontal représente l'entrée du pilote. L'axe vertical représente la sortie pilotée. Les points de réponse associent l'entrée à la sortie. Ils diffèrent des clés d'Action, qui utilisent le temps d'animation.

1. Sélectionnez les canaux de pilotes visibles à modifier.

2. Déverrouillez ces canaux.

3. Vérifiez que leurs propriétaires sont modifiables.

4. Pour modifier des points, sélectionnez les points de réponse ou les côtés des poignées.

5. Sélectionnez **Interpolation** ou **Poignées** dans **Courbe de réponse**.

6. Examinez la réponse obtenue et la propriété pilotée.

| Commande | Portée et résultat |
|---|---|
| **Interpolation** | Modifie les points de réponse sélectionnés des canaux de pilotes sélectionnés, visibles et modifiables. Les choix sont Constant, Linéaire et Bézier. |
| **Poignées** | Modifie les côtés de poignées sélectionnés de ces canaux. Si un point de contrôle est sélectionné, l'action modifie ses deux poignées. |
| **Extrapolation** | Modifie les canaux de pilotes sélectionnés, visibles et modifiables hors de leur intervalle d'extrémités. Constant maintient la sortie. Linéaire prolonge la pente de l'extrémité. |
| **Ajouter un modificateur (actif)** | Ajoute le modificateur de réponse choisi au seul pilote actif et modifiable. Ne touche pas tous les canaux sélectionnés. |
| **Ouvrir les réglages des modificateurs** | Ouvre l'onglet natif **Modificateurs** du pilote actif. |

Les actions de points exigent des points ou des poignées sélectionnés. L'extrapolation exige des canaux sélectionnés et modifiables. Les modificateurs exigent un pilote actif déverrouillé, dont le propriétaire est modifiable. Ouvrir les réglages natifs exige aussi un pilote modifiable et actif nativement. Si une commande est désactivée, survolez-la pour lire sa condition.

L'interpolation, les poignées, l'extrapolation et la création de modificateurs prennent en charge **Annuler** et **Ajuster la dernière opération** natifs. Ces actions touchent uniquement les pilotes indiqués. Elles excluent les clés d'Action et les pilotes sans rapport. La qualification d'exécution ne couvre pas séparément chaque type de modificateur natif.

La figure du pilote sélectionné ci-dessus situe **Interpolation**, **Poignées**, **Extrapolation** et **Ajouter un modificateur (actif)**. La destination native des modificateurs apparaît ci-dessous.

![Onglet natif Modificateurs dans l’éditeur Contrôleurs, avec le canal d’échelle X de Empty sélectionné et le graphe de réponse visible. La pile est vide : seule la commande d’ajout de modificateur apparaît. Aucun modificateur n’a été ajouté. La fenêtre actuelle mesure 710 pixels de large. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-21 (UTC). SHA-256 de l’image (préfixe) : eb2138c45bad.](images/fr/12.11.0-native-modifier-settings.png)

<a id="diagnostics"></a>

### Diagnostic

1. Sélectionnez les canaux de pilotes visibles à examiner.

2. Ouvrez **Diagnostic**.

3. Cliquez sur **Vérifier les pilotes sélectionnés**.

4. Lisez la fenêtre de résultats.

5. Corrigez les cibles, les chemins, les os ou l'expression signalés dans les réglages natifs appropriés.

6. Après avoir corrigé une dépendance, cliquez sur **Mettre à jour les dépendances**.

**Vérifier les pilotes sélectionnés** vérifie la validité de l'évaluation, les cibles manquantes, les chemins de propriété non résolus et les os manquants. Il signale aussi les propriétaires liés/en lecture seule, les canaux verrouillés et les pilotes muets. Si une cible de propriété possède une valeur de repli activée, la vérification ne signale pas de chemin non résolu pour cette cible.

Les vérifications n'examinent que les pilotes visibles sélectionnés. Elles ne parcourent pas tout le fichier. Elles ne prouvent pas que chaque expression produit le mouvement voulu. **Mettre à jour les dépendances** actualise les propriétaires des pilotes sélectionnés et réévalue le calque de vue. Il ne répare pas les expressions ni les connexions de cibles. Il ne change pas les points de réponse et ne supprime pas les pilotes.

![Fenêtre complète du résultat du diagnostic du pilote sélectionné : « Aucun problème trouvé ». Ce résultat concerne uniquement le pilote Empty sur scale&#91;0&#93; sélectionné dans cette scène de démonstration ; il ne certifie pas tous les pilotes. La fenêtre de résultat recouvre une partie de la barre latérale en arrière-plan, qui n’est donc pas présentée entièrement dégagée. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-21 (UTC). SHA-256 de l’image (préfixe) : 22bebd3cbce0.](images/fr/12.11.0-driver-diagnostics.png)

<a id="nla-arrange-clips-and-blend-corrections"></a>

## NLA : agencer les clips et mélanger les corrections

**Disposition et rythme** et **Mélange et corrections** sont ouverts au départ. **Actions et pistes, Précalculer et terminer et Étagère rapide** sont repliés. Le résumé montre le propriétaire, le clip actif, l'Action source, le nombre de clips sélectionnés et les intervalles de scène et source. Les images de scène donnent la position du clip. Les images source donnent l'intervalle d'Action utilisé dans le clip.

<a id="arrange-clips"></a>

### Agencer les clips

1. Sélectionnez les clips d'Action à modifier.

2. Cliquez sur le corps du clip de référence pour le rendre actif.

3. Vérifiez que le clip de référence reste sélectionné.

4. Cliquez sur **-1f/+1f** pour décaler, ou sur **Déplacer les clips sélectionnés** pour un déplacement natif.

5. Utilisez **Align Starts to Active Clip / Align Ends to Active Clip** pour aligner les clips sur le clip actif sélectionné.

6. Utilisez **Mettre les clips en séquence** pour les placer successivement depuis le début du clip de référence.

7. Modifiez le pas ou l'écart entre clips dans **Ajuster la dernière opération**.

8. Développez **Options de rythme** pour l'échelle, la répétition, l'inversion et les limites de scène du clip actif.

Le placement temporel utilise les images de scène. Les outils refusent les lots contenant des clips verrouillés ou qui se chevauchent, sans changement partiel. L'agencement est suspendu pendant l'édition de la source. Ces outils ne modifient pas les bandes de transition, les bandes méta ni les bandes sonores.

![Fenêtre de correction du mélange NLA pour Cube Correction : mode de combinaison, influence animée activée et influence de 0,500 avec clé à l’image 12. La source d’origine est conservée. Le titre anglais Blend Options, resté dans l’interface faute de traduction source, signifie « options de mélange ». Cette vue montre la fenêtre de correction, pas l’ensemble de l’éditeur NLA. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 11e33c78ffbb.](images/fr/12.8.0-nla-arrange.png)

Avant d'utiliser une action sur le clip actif, vérifiez que le résumé montre son propriétaire, son clip et son Action.

<a id="edit-sources-and-manage-sharing"></a>

### Modifier les sources et gérer leur partage

**Modifier l’action** active le mode natif NLA Tweak Mode. **Ouvrir le Dope Sheet / Ouvrir l’éditeur de graphes** réutilise un éditeur non épinglé adapté ou change la zone actuelle. Le mode natif Tweak Mode fait correspondre le temps source aux clips déplacés, redimensionnés, répétés ou inversés.

Pour revenir à l'agencement après l'édition :

1. Utilisez le sélecteur d'éditeur pour revenir à NLA.

2. Cliquez sur **Terminer l’édition**.

Modifier une Action partagée peut toucher d'autres clips. Le résumé avertit du partage et indique les sources exclues. Muet et Solo influencent l'évaluation.

| Commande | Résultat |
|---|---|
| **Rendre les clips sélectionnés uniques** | Sépare les Actions sources des clips sélectionnés. |
| **Dupliquer indépendamment** | Copie l'Action. |
| **Dupliquer en liant** | Partage l'Action. |
| **Monter les pistes sélectionnées / Descendre les pistes sélectionnées** | Réordonne les pistes. Ne déplace pas les clips entre les pistes. |

**Push Down Active Action / Stash Active Action** agit sur l'Action affectée au propriétaire actif. Pousser vers le bas exige une évaluation NLA activée. Sans clip sélectionné, le résumé propose **Ajouter un clip d’action existant** pour un objet actif modifiable.

![Fenêtre Actions et pistes : duplication indépendante ou liée, clip et action, piste Manual Source, contrôles de sourdine, de solo et de réorganisation. Les commandes désactivées Push Down Active Action et Stash Active Action restent en anglais ; elles signifient respectivement transférer l’action active vers une bande NLA et mettre l’action active de côté. Aucune de ces commandes n’a été exécutée pour cette capture. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 9eba29d477c5.](images/fr/12.11.1-nla-actions.png)

<a id="add-a-transform-correction"></a>

### Ajouter une correction de transformation

1. Sélectionnez un clip d'Action source pris en charge.

2. Cliquez sur **Nouvelle correction de transformation**.

3. Sélectionnez le nouveau clip de correction.

4. Cliquez sur **Modifier la correction**.

5. Modifiez ses clés de transformation dans le mode Ajustement natif.

6. Après l'édition, cliquez sur **Terminer l’édition**.

7. Gardez les canaux non modifiés neutres : position nulle, rotation nulle/identité, échelle égale à un.

8. À la tête de lecture, cliquez sur **0 %, 50 % ou 100 %** pour créer une clé d'influence du clip actif.

Le mélange natif **Combiner** applique la correction au mouvement source. Pour une autre influence, saisissez sa valeur dans **Ajuster la dernière opération**. À une influence nulle, la correction n'ajoute aucun mouvement.

La création ajoute une Action de correction indépendante et une piste au-dessus de la source. Les corrections prennent en charge les transformations d'objets et d'os de pose. La création refuse les rigs contraints/pilotés, les os non résolus et les canaux source sans transformation. Elle explique la raison. Ces corrections sont distinctes des outils généraux de Calques d’animation dans les Propriétés de la scène.

Mélange et Influence animée sont des réglages natifs de bande. Si Influence animée est désactivée, la barre latérale indique l'enveloppe de mélange automatique. **Blend Options** montre Mélange automatique, les transitions d'entrée/sortie et l'extrapolation. Les boutons d'influence créent des clés d'influence natives. Ils ne créent aucune clé de pose dans l'Action source.

La figure **Commandes d'agencement et de correction NLA** ci-dessus montre la piste de correction. Elle montre aussi **Modifier la correction**, le mélange **Combiner** et les boutons d'influence.

<a id="bake-while-retaining-the-source-stack"></a>

### Précalculer en conservant la pile source

1. Sélectionnez un clip du propriétaire à précalculer.

2. Ouvrez **Précalculer et terminer**.

3. Vérifiez le propriétaire et l'intervalle de scène affichés.

4. Cliquez sur **Précalculer dans une nouvelle action**.

5. Si nécessaire, ajustez l'intervalle et le pas dans **Ajuster la dernière opération**.

6. Vérifiez le nom et l'intervalle du résultat.

7. Avant d'activer le précalcul, rendez muettes ou supprimez les contraintes actives qui s'appliqueraient de nouveau.

8. Sélectionnez **Utiliser le dernier précalcul (NLA désactivé)**.

Le précalcul écrit les transformations évaluées d'objet/de pose dans une nouvelle Action et la conserve. Cette Action reste d'abord **non affectée**. Les Actions, clips, parents et contraintes d'origine sont conservés. Activer le précalcul constitue une opération séparée. **Utiliser le dernier précalcul (NLA désactivé)** affecte le résultat et désactive l'évaluation de la pile source.

Enregistrez la scène source pour comparer. Renommer un objet ne change pas le propriétaire du résultat. Un autre objet reprenant l'ancien nom ne peut pas recevoir ce résultat. **Supprimer les pistes vides** retire les pistes vides séparément.

Les raccourcis de l'étagère rapide NLA rendent les sources uniques, modifient la source active et précalculent le propriétaire. Ils n'exécutent pas les macros générales d'édition de clés sur les bandes.

![Fenêtre de précalcul NLA pour Cube : plage de scène de 1 à 24, précalcul de 1 à 24 avec un pas de 1 et sortie Toolkit_Offer_Animated_Cube NLA Bake. Les originaux sont conservés et la sortie n’est pas affectée à l’objet au moment de cette capture. Le reçu lié indique la fin du précalcul ; la commande d’utilisation du dernier précalcul n’a pas encore été exécutée dans cet état. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : d1be1abd7d4e.](images/fr/12.11.1-nla-retained-bake.png)

<a id="scene-properties-and-broader-tools"></a>

## Propriétés de la scène et outils généraux

**Propriétés de la scène > Anim Assist** contient **Étagère rapide, Cette pose, Animation entière, Rig, Visage, Configuration (une fois par rig), Réglages et Aide et diagnostic**.

| Groupe | Travail |
|---|---|
| **Cette pose** | Décalages de transformation, correspondances, changement d'espace et miroir de pose. |
| **Animation entière** | Décalages d'Action active, trajectoires et Calques d’animation. |
| **Rig** | Repères, proxies, réglages de précalcul et nettoyage de session. |
| **Visage** | Configuration de la synchronisation labiale, connexions aux cibles, aperçu et précalcul. |
| **Configuration (une fois par rig)** | Configuration initiale et procédures d'espace de travail/système. |
| **Réglages** | Réglages partagés, raccourci circulaire facultatif et création de macros. |
| **Aide et diagnostic** | Aide des outils, rapports de diagnostic et conseils de récupération. |

**Rechercher** trouve les outils existants. La liste **Récents** affiche les outils terminés, du plus récent au plus ancien. **Répéter la dernière opération** utilise la première entrée. Les commandes annulées ou inachevées n'entrent pas dans Récents. Les anciens fichiers trient Récents par horodatage. **Basculer le mode de l’étagère** parcourt les modes de l'étagère.

Pour configurer les macros, ouvrez **Propriétés de la scène > Anim Assist > Réglages**.

Les figures **Emplacement dans Scène** et **Configuration initiale**, près de l'installation, montrent les accès partagés. Les figures suivantes montrent chaque panneau enregistré dans un panneau contextuel natif.

![Fenêtre des réglages : menu circulaire facultatif désactivé, champs Maj Alt D grisés, options d’en-tête des éditeurs, aide détaillée activée et mode compact désactivé. Ces réglages visibles ne démontrent pas l’exécution d’un raccourci. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 8cda3b33155a.](images/fr/12.11.1-settings.png)

![Fenêtre des macros avec préréglages, liste sans macro personnalisée, commande d’ajout et contrôles de traitement par lot. Aucune macro n’a été exécutée pour cette capture. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : b58079141672.](images/fr/12.11.1-macros.png)

<a id="offset-match-and-mirror"></a>

### Décaler, faire correspondre et appliquer un miroir

1. Sélectionnez le propriétaire animé et les clés ou os de pose voulus.

2. Ouvrez **Feuille d’exposition > Anim Assist > Ébauche et interpolation > Décalage de transformation** pour décaler des clés.

3. Sélectionnez le masque de canaux.

4. Sélectionnez la portée du décalage.

5. Définissez les valeurs de décalage.

6. Sélectionnez l'espace de transformation.

7. Utilisez **Ajuster l’image actuelle**, **Décaler les clés sélectionnées** ou **Glissement interactif** selon la portée voulue.

8. Avant **Réappliquer le dernier** ou **Inverser le dernier**, examinez le résultat.

![Fenêtre de décalage des transformations dans la Feuille d’exposition : valeurs nulles, image courante, translation en espace local, sans atténuation, avec filtres visibles. Cette vue appartient à l’état ultérieur à l’affectation de l’action précalculée signalée par l’opérateur ; la figure 35 conserve son état antérieur, où la sortie n’était pas affectée. Aucun décalage n’a été appliqué. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : b69af3487ae7.](images/fr/12.11.1-transform-offset.png)

**Propriétés de la scène > Anim Assist > Cette pose > Décalage de pose** décale les os de pose sélectionnés par petits pas ou par glissement interactif. Décalage de pose exige le **Mode pose**.

Image actuelle, Clés sélectionnées et Plage d’images sont des portées de décalage distinctes. L'atténuation d'intervalle répartit le décalage dans le temps. L'atténuation à entrée/sortie progressive ne modifie pas les tangentes des courbes. Ces outils utilisent le pivot **Origines individuelles**. Ils ne font pas tourner les éléments autour du point médian ou du curseur 3D.

Les correspondances proposent Monde, Parent, Cible, des canaux précis, les transformations visuelles/évaluées et la matrice locale. La correspondance à une cible exige généralement deux objets sélectionnés.

Pour une correspondance à une cible :

1. Sélectionnez d'abord la cible.

2. Sélectionnez l'objet à modifier.

**Aligner les objets sélectionnés sur l’actif** utilise l'objet actif comme référence. Ces commandes ne reconnaissent pas automatiquement tous les rigs.

Avant un changement d'espace compensé ou une procédure IK/FK :

1. Configurez les correspondances des propriétés de commutation.

2. Configurez les chaînes.

Les outils de miroir exigent une armature en **Mode pose**. **Sélectionner le côté opposé** change la sélection. Les miroirs d'image/d'intervalle peuvent aussi insérer des clés.

Avant **Symétriser la pose**, **Symétriser la sélection** ou **Échanger** :

1. Vérifiez la détection des paires et les exceptions de nommage.

2. Vérifiez l'espace et l'axe du miroir.

3. Vérifiez les filtres de canaux.

4. Lisez la description de l'outil.

![Fenêtre de correspondance rapide de la Vue 3D : réglages déployés, toutes les transformations TRS, axes X, Y et Z cochés, conservation du décalage désactivée et respect des transformations verrouillées activé. Les commandes de correspondance rapide et vers le côté opposé sont désactivées ; les contrôles Monde, Cible, Position, Rotation et Échelle restent disponibles, tandis que Parent est grisé. Aucune correspondance n’a été exécutée. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 44066c10bd95.](images/fr/12.11.1-transform-match.png)

Ouvrez **Feuille d’exposition > Anim Assist > Pose et correspondance** pour les réglages complets des correspondances et des miroirs.

![Fenêtre de décalage rapide de pose. Le contexte de capture signalé est HumanArmature en mode Pose avec des os sélectionnés. La vue présente les contrôles ; aucune modification de pose n’a été exécutée pour cette image. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : abb1138f681c.](images/fr/12.11.1-pose-offset.png)

![Fenêtre de miroir rapide avec aides de sélection, dans le contexte de pose de HumanArmature. Aucune opération de miroir, d’échange ou de sélection n’a été exécutée pour cette capture. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 1047474dae2c.](images/fr/12.11.1-pose-mirror.png)

<a id="action-offsets-and-motion-trails"></a>

### Décalages d'Action et trajectoires

**Animation entière** contient les décalages d'Action active et un masque d'intervalle facultatif. Ces décalages peuvent dépasser les clés sélectionnées.

Avant d'activer une modification sur toute l'Action :

1. Configurez le masque.

2. Configurez l'intervalle.

Pour utiliser les trajectoires :

1. Sélectionnez les objets ou os de pose ciblés par les réglages de trajectoire.

2. Ouvrez **Animation entière > Superposition des trajectoires**.

3. Sélectionnez le mode d'affichage.

4. Sélectionnez la portée d'échantillonnage.

5. Définissez le pas d'échantillonnage.

6. Cliquez sur **Activer la superposition**, ou utilisez l'œil **Traînées** de la Timeline.

7. Après des changements, actualisez les trajectoires si nécessaire.

8. Exécutez le diagnostic des arcs pour repérer les mouvements à examiner.

9. Examinez les mouvements signalés.

Les options de trajectoire incluent les graduations d'images/de clés, les numéros d'image, la vitesse, les tangentes, les fantômes et les couleurs. Les intervalles autour de l'image actuelle et personnalisés limitent l'échantillonnage. Le champ **Échantillons maximaux** limite leur nombre. Le diagnostic des arcs repère les mouvements à examiner. Il ne certifie pas la qualité de l'animation et ne corrige pas automatiquement un rig.

![Fenêtre du masque de décalage d’action : masque activé, plage de 1 à 250 et transitions d’entrée et de sortie de 5 images. Cette plage de masque est distincte de la plage de scène et de précalcul de 1 à 24. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 6582fed59c04.](images/fr/12.11.1-action-offset.png)

![Fenêtre de configuration de la superposition des trajectoires, actuellement désactivée : mode contrôle actif, voisinage de 25 images avant et après l’image courante, pas de 1, maximum de 160 points, points fantômes et repères de clés. Aucune trajectoire générée n’est présentée. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : cbca63e7cd19.](images/fr/12.11.1-motion-trails.png)

<a id="locators-proxies-and-bake-sessions"></a>

### Repères, proxies et sessions de précalcul

1. Ouvrez **Rig > Proxy et précalcul**.

2. Sélectionnez l'objet voulu.

3. Sélectionnez un repère ou un proxy de Translation, d'Orientation, d'Espace monde ou d'Espace du parent.

4. Définissez l'intervalle de la commande de précalcul choisie.

5. Définissez le pas de précalcul.

6. Sélectionnez les canaux à précalculer.

7. Exécutez la commande de précalcul.

8. Examinez le mouvement précalculé.

9. Utilisez le nettoyage de session seulement après avoir vérifié le résultat précalculé.

Les commandes créent des repères aux cibles, à la position moyenne de la sélection ou au curseur 3D. Elles définissent aussi le parentage, appliquent des contraintes, alignent et précalculent les repères et les cibles. Avant d'utiliser des commandes par paires, lisez le sens de leur flèche.

**Précalcul intelligent** combine le précalcul des transformations et la réduction des clés. **Réduire les clés** simplifie les clés existantes selon sa tolérance. Les intervalles disponibles sont scène, Action, personnalisé, clés sélectionnées et aperçu. Ces commandes générales diffèrent de la procédure NLA **Précalculer dans une nouvelle action**, qui conserve la pile source.

**Proxy et précalcul en un clic** enregistre le mouvement dans l'espace monde dans sa propre session de proxy, avant le précalcul. **Précalculer la session et supprimer les proxies** nettoie cette session. **Supprimer toutes les sessions de proxy** agit plus largement. La qualification existante ne certifie pas tous les cas avec parent, contraintes ou rigs de production. Avant de supprimer les aides, comparez le résultat.

![Fenêtre de proxy et de précalcul sans session active. Les réglages et options avancées sont repliés ; les états disponibles ou grisés des commandes sont conservés. Aucune session de proxy ni aucun précalcul de proxy n’a été exécuté pour cette image. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : e55ba0545ba4.](images/fr/12.11.1-proxy-bake.png)

La figure montre la configuration avant de créer une session. Une session active rend le nettoyage disponible.

<a id="animation-layers"></a>

### Calques d’animation

1. Ouvrez **Animation entière > Calques d’animation**.

2. Activez le système de calques.

3. Cliquez sur **Créer le calque de base** pour l'animation actuelle.

4. Ajoutez un calque de travail.

5. Sélectionnez le calque de travail.

6. Sélectionnez son mode de mélange.

7. Définissez son poids.

8. Configurez ses affectations d'os.

9. Avant d'insérer des clés, sélectionnez le calque de travail voulu.

10. Prévisualisez avec les commandes Solo, Muet et Verrouillé du calque.

Une liste d'affectations vide inclut tous les os. En Mode pose, le panneau visible propose **Affecter**, **Supprimer** et **Sélectionner** pour les affectations d'os. Chaque ligne de calque contient le poids, Solo, Désactiver, Verrouiller et le contrôle « Insertion automatique de clés ».

Ce panneau enregistré n'affiche pas **Modifier uniquement l’actif**, **Affecter automatiquement à l’insertion de clés**, ni toutes les commandes avancées. La recherche native d'opérateurs propose notamment **Affecter par motif**, **Fusionner vers le bas** et **Fusionner tous les calques**. Avant de fusionner ou d'aplatir, examinez la pile. Ces calques sont distincts des clips de correction de transformation NLA.

![Fenêtre des calques activée : Polish est sélectionné en mode additif au-dessus de Base Layer, avec un poids de 1,00 pour chaque calque. Ces deux noms de données restent inchangés. Le reçu lié confirme l’initialisation et l’ajout du calque sur HumanArmature en mode Pose ; aucun précalcul de calque n’a été effectué. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : a66a8e35266d.](images/fr/12.11.1-animation-layers.png)

<a id="lipsync"></a>

### Synchronisation labiale

1. Ouvrez **Visage > Synchronisation labiale**.

2. Activez la synchronisation labiale.

3. Ajoutez un calque de synchronisation labiale avec **+**.

4. Sélectionnez le calque.

5. Dans **Audio**, associez un fichier **WAV**.

6. Sélectionnez **Clés de forme**, **Os** ou **Les deux** comme cible.

7. Sélectionnez le maillage ou l'armature cible.

8. Configurez **Connexions des clés de forme** ou **Liaisons des os du rig** pour la bibliothèque de visèmes sélectionnée.

9. Vérifiez les noms de cibles des entrées de connexion.

10. Vérifiez l'anticipation, le décalage d'images et le moteur d'analyse.

11. Cliquez sur **Précalculer**.

12. Examinez le mouvement de la bouche.

Avant **Reprécalculer**, utilisez **Verrouiller les clés sélectionnées** pour conserver le travail manuel sélectionné.

**Aperçu en direct / Précalculé** montre l'état du calque. La sortie par clés de forme exige un maillage avec des clés de forme connectées. La sortie par os exige un calque d'animation, une armature et des connexions valides. **Remplir automatiquement** fournit les entrées de connexion. **Captures de visèmes > Capturer** mémorise une pose personnalisée.

Utilisez la commande d'état pour choisir la procédure d'aperçu ou de précalcul voulue.

L'analyse d'amplitude n'exige aucun exécutable externe de reconnaissance de phonèmes. L'analyse Rhubarb facultative exige un **Chemin de Rhubarb** configuré. Avant de vous fier au résultat, lisez les rapports de moteur de repli et de calque manquant. Si une bande de haut-parleur existe, sa superposition montre l'audio dans la Feuille d’exposition/la Timeline.

**Effacer**, dans la barre latérale, supprime la sortie automatique et conserve le travail manuel marqué. **Reprécalculer** conserve aussi les remplacements manuels. **Accentuer les clés manuelles** montre les modifications protégées. Changer l'audio signale que le calque doit être actualisé. Avant un nouveau précalcul, résolvez les problèmes de WAV, de cible et de calque signalés.

![Panneau complet de synchronisation labiale au stade de configuration : options de clés de forme, de mâchoire simple et d’amplitude, fichier manual-example.wav dont le chemin conserve ses points de suspension natifs, et zéro repère. Le maillage et les associations de clés de forme ou d’os ne sont pas affectés. Le reçu lié indique une bande sonore SOUND sur le canal 1 avec la bibliothèque BASIC_JAW. Aucune analyse ni aucun précalcul de bouche n’a été réalisé. Version candidate locale d’Anim Assist 12.11.2 dans Bforartists, distribution officielle 5.2.3 ; version indiquée par l’API : 5.3.0 Alpha. Capture du 2026-11-20 (UTC). SHA-256 de l’image (préfixe) : 1d9479550dc3.](images/fr/12.11.2-lipsync-setup.png)

<a id="troubleshooting-and-verification-limits"></a>

## Dépannage et limites de vérification

Si une opération sur les clés ne produit aucun effet :

1. Vérifiez l'éditeur actif.

2. Vérifiez les clés sélectionnées modifiables et les canaux visibles.

3. Vérifiez les verrouillages, le propriétaire et l'Action.

4. Examinez les données d'Action et les filtres de l'éditeur.

La visibilité de la barre seule ne prouve pas que l'opération a inséré des clés. La commande native Insérer une image clé reste la procédure normale pour les clés de maillage/d'objet.

Pour signaler un problème, indiquez la version du complément, la compilation Bforartists, la commande exacte et une petite scène reproductible.

Si une action NLA est indisponible :

1. Vérifiez les verrouillages de pistes et les exclusions Muet/Solo.

2. Vérifiez si une Action manque, si l'évaluation NLA est désactivée ou si le mode Ajustement est actif.

3. Avant d'agencer les clips, cliquez sur **Terminer l’édition**.

4. Pour créer une correction, lisez l'explication du rig/canal non pris en charge.

Après un changement temporel ou un précalcul :

1. Examinez le mouvement.

2. Si nécessaire, utilisez Annuler natif.

3. Enregistrez la scène.

4. Rouvrez-la avant de vous fier au résultat.

Si les réglages de pilote sont indisponibles, sélectionnez un canal déverrouillé pour le rendre actif nativement. Un pilote verrouillé peut rester visible pour l'inspection et le déverrouillage. Si plusieurs pilotes sélectionnés n'ont aucune cible active claire, les outils n'en choisissent pas. Les actions sur les points exigent des points de réponse sélectionnés.

Les [notes de version 12.11.1](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.11.1/RELEASE-NOTES.md) décrivent la correction du traitement d'annulation de la Timeline. La [qualification 12.11.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.11.0/qualification.md) consigne des tests ciblés des Contrôleurs et des observations du curseur natif sur Bforartists 5.2.0. Ils couvrent la portée des canaux, l'accès aux réglages natifs et l'annulation/le rétablissement des modificateurs. Les relevés couvrent aussi l'enregistrement des dispositions et 11 scénarios de non-régression des éditeurs d'animation. Ces résultats viennent de tests antérieurs. La mise à jour du guide n'a pas répété ces tests.

La [qualification 12.10.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.10.0/qualification.md) couvre les ensembles d'outils par étape. La [qualification 12.9.1](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.9.1/qualification.md) couvre les corrections des onglets d'étape. La [qualification 12.8.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.8.0/qualification.md) consigne 16 groupes d'interactions natives, l'annulation/le rétablissement et le rechargement d'espace de travail. Elle consigne aussi l'enregistrement de 98 panneaux et cinq tests de non-régression de disposition de la Timeline. Ses preuves comprennent l'insertion de clés de maillage et des captures de barre latérale à 220, 280 et 360 px.

Ces tests ne certifient pas chaque opérateur, modificateur, rig de production ou compilation hôte. Les anciennes preuves de curseurs et de synchronisation labiale restent historiques. La révision documentaire du guide anglais, le 20 novembre, vérifie le code source actuel, les liens et la présentation PDF. Elle ne fournit aucune certification formelle selon le dictionnaire STE.

La commande **Configurer la synchronisation labiale** de la version candidate 12.11.2 s'est terminée sur Bforartists officiel 5.2.3. Cet hôte repose sur Blender 5.3 Alpha. La commande a créé une bande sonore. La nouvelle figure montre le calque obtenu avant les connexions aux cibles et le précalcul. Elle ne démontre aucun mouvement de bouche précalculé.

Si la configuration indique **compiled without Audaspace support**, utilisez une compilation Bforartists avec prise en charge audio. La configuration peut se terminer sans créer de bande sonore. La compilation personnalisée fournie, basée sur Blender 5.4 Alpha, a produit ce résultat.

Utilisez les figures **Feuille d’exposition**, **Éditeur de graphes** et **Pilote sélectionné** pour repérer les résumés de portée et de sélection.

<a id="screenshot-sources-and-limits"></a>

## Sources et limites des captures d'écran

Le manuel source anglais conserve les captures historiques de la Timeline et des réglages de la barre d’outils, les captures de pilote sélectionné issues de la qualification 12.11.0, les vues d’ensemble des éditeurs issues de la qualification 12.8.0 et les captures de bandes séparées de la version 12.5.0. Cette édition localisée remplace ces figures par de nouvelles captures natives de la version candidate locale et non publiée 12.11.2. Chaque légende indique ce que sa capture démontre et ses limites de qualification ; une nouvelle capture ne répète ni n’étend les tests de version antérieurs.

Les captures natives 12.11.1 fournies par l'utilisateur montrent des portées vides. Elles documentent la disposition visible. Elles ne démontrent aucune modification terminée :

- [Barre latérale des Contrôleurs sans pilote sélectionné](../images/12.11.1-native-drivers-empty.png).
- [Barre latérale des courbes d'Action sans courbe modifiable dans la portée](../images/12.11.1-native-action-graph.png).
