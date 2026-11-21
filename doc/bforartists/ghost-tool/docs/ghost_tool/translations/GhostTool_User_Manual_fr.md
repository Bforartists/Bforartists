<a id="ghost-tool-433-user-guide"></a>

# Guide de Ghost Tool 4.3.3

Ghost Tool affiche des maillages fantômes, des trajectoires et des marqueurs de mouvement modifiables dans Bforartists. Les maillages fantômes, aussi appelés pelures d’oignon, montrent une cible à d’autres moments de l’animation. Les trajectoires montrent son déplacement. Les marqueurs de mouvement sont des points modifiables sur ces trajectoires. Ce guide décrit la version 4.3.3.

Les captures montrent Ghost Tool 4.3.3 dans la version fournie de Bforartists 5.2.3. Les panneaux de paramètres natifs peuvent afficher Tear Off Panel dans leur barre de titre.

La version 4.3.2 a ajouté le repli de la barre Timeline et un espace entre les deux icônes de fantôme. La version 4.3.3 peut générer des aperçus lorsque le gestionnaire de pointeur Timeline d’Anim Assist est inactif. Les gestes de modification actifs suspendent toujours l’échantillonnage.

Le [ZIP d’installation de Ghost Tool 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/ghost-v4.3.3/b4_ghost_tool_v4.3.3.zip) installe l’add-on autonome. Les [notes de version 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/RELEASE-NOTES.md) et le [reçu du paquet](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/package-receipt.json) contiennent les preuves de publication et la somme de contrôle.

<a id="install-and-find-ghost-tool"></a>

## Installer et trouver Ghost Tool

La version de test personnalisée/native fournie inclut Ghost Tool 4.3.3. Ses préférences d’usine activent l’add-on. Aucune installation ZIP ni activation manuelle supplémentaire n’est nécessaire. Les emplacements de barre d’outils, étagère, panneau latéral et Préférences décrits ci-dessous s’appliquent aussi à cette version.

Pour une installation autonome :

1. Téléchargez `b4_ghost_tool_v4.3.3.zip`.

2. Ouvrez Édition > Préférences > Add-ons > Installer depuis le disque.

3. Sélectionnez le ZIP.

4. Activez Ghost Tool.

5. Après le remplacement d’une version installée, redémarrez Bforartists.

6. Vérifiez que les Préférences indiquent la version 4.3.3.

Les modifications du dépôt ne mettent pas automatiquement à jour un add-on installé. Un ancien ZIP installe sa version d’origine.

Ces instructions installent l’add-on autonome. La version intégrée proposée dépend de la demande de fusion Bforartists [7067](https://github.com/Bforartists/Bforartists/pull/7067). Au 2026-11-19, cette demande reste non fusionnée. Les versions officielles publiées de Bforartists n’incluent pas encore cette intégration proposée.

Par défaut, Ghost Tool utilise Barre d’outils supérieure dans la ligne native des paramètres d’outil de la Vue 3D. Lorsque les en-têtes natifs sont en haut, cette ligne se trouve sous l’en-tête principal de la Vue 3D. Elle suit l’alignement de l’en-tête natif.

Les Préférences proposent aussi Panneau latéral droit (N) et Étagère d’outils gauche (T). Ghost Tool remplace les anciens choix enregistrés Top Header par Barre d’outils supérieure.

![Préférences de Ghost Tool 4.3.3](images/fr/4.3.3-preferences.png)

*Figure 1. La version fournie active Ghost Tool 4.3.3. Emplacement d’affichage indique Barre d’outils supérieure.*

Les commandes natives d’outil et de mode restent disponibles. Dans les vues étroites ou divisées, les commandes Ghost Tool conservent le même ordre.

1. Faites glisser la ligne native horizontalement avec le bouton central pour atteindre les commandes hors de la largeur visible.

2. Si les commandes Ghost Tool sont masquées, sélectionnez Vue > Afficher la barre Ghost Tool.

3. Enregistrez les préférences pour conserver les choix d’affichage.

<a id="set-the-interface-language"></a>

## Régler la langue de l’interface

La version candidate multilingue de Ghost Tool prend en charge l’anglais, le japonais, le coréen, le chinois simplifié, le portugais, l’espagnol et le français. Ces instructions de langue concernent cette version candidate.
Les commandes de langue de Bforartists nécessitent une version qui prend en charge les traductions.

1. Ouvrez Édition > Préférences > Interface.

2. Dans Langue, sélectionnez la langue requise.

3. Pour une langue autre que l’anglais, activez Interface, Infobulles et Rapports sous Traduire.

4. Ouvrez les préférences de l’add-on Ghost Tool.

5. Réglez Langue sur Langue de l’interface.

Avec Langue de l’interface, les textes personnalisés de Ghost Tool utilisent la langue d’interface de l’application.
La désactivation d’Interface remet les textes personnalisés automatiques en anglais.
Un choix explicite de langue dans Ghost Tool change les textes personnalisés. Les commandes et infobulles natives utilisent toujours la langue de l’application.
Sélectionnez la même langue dans Bforartists et Ghost Tool pour traduire l’ensemble de l’interface.
Les noms d’objets, noms d’os et identifiants de données enregistrés conservent leur texte d’origine.

<a id="quick-start-inspect-an-animated-target"></a>

## Démarrage rapide : examiner une cible animée

1. Sélectionnez un objet animé ou un os en mode Pose.

2. Activez la première icône de fantôme.

3. Cliquez sur Fantômes pour afficher les aperçus de maillage.

4. Réglez Avant et Après séparément.

5. Sélectionnez Fil de fer ou Plein pour l’apparence du maillage.

6. Maintenez Fantômes pour régler l’échantillonnage et l’apparence.

7. Cliquez sur Trajectoires pour afficher une trajectoire.

8. Cliquez sur Ajouter la trajectoire sélectionnée pour conserver une autre cible sélectionnée.

9. Activez Affichage des marqueurs pour afficher les points modifiables d’une trajectoire ajoutée.

10. Cliquez sur Déplacer.

11. Sélectionnez un marqueur dans la Vue 3D.

12. Déplacez le marqueur.

13. Confirmez le déplacement.

14. Sélectionnez un autre marqueur pour poursuivre les modifications.

15. Pour quitter le mode Déplacer les marqueurs, cliquez à nouveau sur Déplacer ou appuyez sur Échap.

![Cube animé avec aperçus de maillages fantômes](images/fr/4.3.3-overview.png)

*Figure 2. Les maillages fantômes en cache entourent le cube animé. La première icône de fantôme active Ghost Tool.*

Lorsqu’aucune cible de trajectoire n’existe, Trajectoires peut ajouter la cible animée sélectionnée. Suivre la sélection affiche la sélection actuelle. Les cibles ajoutées avec Ajouter la trajectoire sélectionnée restent dans la liste.

<a id="read-the-top-toolbar-from-left-to-right"></a>

## Lire la barre supérieure de gauche à droite

![Barre d’outils supérieure complète de Ghost Tool](images/fr/4.3.3-toolbar-wide.png)

*Figure 3. La barre supérieure conserve l’ordre indiqué, de l’icône générale de fantôme à Paramètres.*

| Commande | Action |
| --- | --- |
| Ghost Tool | Activez ou désactivez l’outil complet. Maintenez pour les paramètres de mise à jour. |
| Fantômes | Affichez ou masquez les maillages fantômes. Maintenez pour l’échantillonnage et l’apparence. |
| Avant / Après à côté de Fantômes | Réglez séparément les nombres d’échantillons de maillage. Chaque nombre possède des boutons moins et plus. |
| Fil de fer / Plein | Sélectionnez le style d’affichage des maillages. |
| Trajectoires | Affichez ou masquez les trajectoires. Maintenez pour l’échantillonnage et les paramètres de ligne. |
| Avant / Après à côté de Trajectoires | Réglez séparément les nombres d’échantillons de trajectoire. Chaque nombre possède des boutons moins et plus. |
| Ajouter la trajectoire sélectionnée | Conservez la cible sélectionnée dans la liste des trajectoires. |
| Suivre la sélection | Affichez une trajectoire pour la sélection actuelle. Maintenez pour Mettre en évidence la trajectoire active. |
| Déplacer | Activez Déplacer les marqueurs pour répéter les modifications. Maintenez pour les paramètres de modification du mouvement. |
| Épingler | Sélectionnez un marqueur à épingler ou détacher. Maintenez pour Détacher tous les marqueurs. |
| Affichage des marqueurs | Affichez ou masquez les marqueurs de trajectoire modifiables. Maintenez pour l’échantillonnage et les étiquettes. |
| Style d’arc | Ouvrez les choix Plein, Couleur selon la vitesse et Fondu. |
| Graduations d’espacement | Affichez ou masquez les indicateurs d’espacement. Maintenez pour Indicateurs d’accélération. |
| Paramètres | Ouvrez les commandes avancées. |

La première icône de fantôme commande l’outil complet. Fantômes commande séparément la visibilité des maillages. La désactivation de l’outil complet désactive aussi la modification des marqueurs et des poignées.

Les maillages masqués conservent le style sélectionné. Fil de fer ou Plein sélectionne un style. Fantômes commande la visibilité des maillages.

Affichage des marqueurs est le losange immédiatement à droite d’Épingler. Les étiquettes apparaissent lorsque le pointeur survole une commande.

Style d’arc commande l’arc de mouvement fantôme. Fil de fer/Plein commande l’affichage des maillages. Le paramètre Style de ligne de Trajectoires commande l’affichage des trajectoires.

Paramètres contient la génération des marqueurs, les cibles, la plage, les modifications, Comparer, Physique et les options d’apparence. Générer et Effacer n’ont pas d’icônes supplémentaires sur la ligne supérieure.

<a id="set-before-and-ahead-counts"></a>

## Régler les nombres Avant et Après

Chaque affichage possède deux nombres indépendants. Avant demande des échantillons avant la tête de lecture. Après demande des échantillons après la tête de lecture.

1. Réglez un nombre dans son champ ou avec les boutons moins et plus de la barre supérieure.

2. Réglez un nombre sur zéro pour désactiver les échantillons de ce côté.

Options des pelures d’oignon utilise Après pour le nombre Ahead de la barre anglaise.

![Options des pelures d’oignon pour les nombres de maillages et l’échantillonnage](images/fr/4.3.3-skin-options.png)

*Figure 4. Options des pelures d’oignon affiche les nombres de maillages, l’échantillonnage, l’opacité et Mise à jour directe des pelures.*

Les nombres indiquent combien d’échantillons demander. L’échantillonnage indique leurs positions.

Pour cet exemple :

1. Placez la tête de lecture à l’image 20.

2. Réglez Avant à côté de Fantômes sur 3.

3. Réglez Après sur 2.

4. Réglez le pas d’image sur 2.

Les échantillons précédents demandent les images 18, 16 et 14. Les suivants demandent les images 22 et 24. L’animation disponible et les limites de plage peuvent restreindre ces demandes. La pose actuelle n’est pas un échantillon Avant ou Après.

Par clé utilise les clés d’animation au lieu d’images régulièrement espacées. Son intervalle peut sauter des clés. Modifier les nombres de Trajectoires sélectionne une fenêtre autour de la tête de lecture fondée sur ces nombres. Les modes de plage avancés suivent leurs propres règles.

<a id="hold-a-tool-for-its-settings"></a>

## Maintenir un outil pour ouvrir ses paramètres

Un bouton compatible possède deux actions :

1. Pour l’action principale, cliquez sur le bouton.

2. Pour son menu de paramètres, maintenez le bouton enfoncé.

Style d’arc et Paramètres s’ouvrent avec un clic normal.

| Maintenir cette commande | Paramètres disponibles |
| --- | --- |
| Ghost Tool | Actualiser les maillages pendant le parcours des images, Actualiser les marqueurs pendant le parcours des images, Suspendre les mises à jour |
| Fantômes | Échantillonnage, Toutes les (images), Intervalle entre les clés, Opacité, Devant, Fondu |
| Trajectoires | Échantillonnage et intervalle, Style de ligne, Numéros d’image, Poignées de Bézier |
| Affichage des marqueurs | Échantillonnage partagé avec Trajectoires, Points des clés, Numéros d’image des marqueurs |
| Déplacer | Au relâchement, Forme de courbe ou Lisser les voisins, Portée des images voisines, Atténuation |
| Épingler | Instructions d’épinglage et Détacher tous les marqueurs |
| Suivre la sélection | Mettre en évidence la trajectoire active |
| Graduations d’espacement | Indicateurs d’accélération |

L’échantillonnage par pas d’image utilise Toutes les (images). La valeur 1 échantillonne chaque image. L’échantillonnage par clé utilise les commandes d’intervalle entre les clés. Certaines commandes proposent des intervalles personnalisés.

Les marqueurs et Trajectoires partagent l’échantillonnage. Une modification dans Affichage des marqueurs change aussi l’échantillonnage de Trajectoires.

Paramètres > Options des pelures d’oignon ouvre les commandes de maillage de la figure 4. Paramètres > Trajectoires ouvre les commandes de cible et de poignées de la figure 7.

<a id="use-the-bottom-timeline-toolbar"></a>

## Utiliser la barre inférieure de la Timeline

La barre compacte se trouve à côté des boutons natifs de la Timeline, sur la même ligne. Elle n’ajoute pas de ligne sous la barre de la Timeline.

1. Activez l’icône de fantôme de gauche pour révéler les autres commandes.

2. Désactivez cette icône pour replier la barre.

Lorsque Ghost Tool est actif, un espace visible sépare l’icône générale d’activation de l’icône Fantômes des maillages. Ces comportements datent de la version 4.3.2.

![Barre Timeline de Ghost Tool dépliée](images/fr/4.3.3-timeline-enabled.png)

*Figure 5. La barre Timeline active affiche les nombres de maillages, les styles, la modification des marqueurs et les commandes de trajectoire.*

![Barre Timeline de Ghost Tool repliée](images/fr/4.3.3-timeline-collapsed.png)

*Figure 6. Lorsque Ghost Tool est désactivé, seule son icône générale reste à côté des commandes natives de la Timeline.*

La barre active présente cet ordre de gauche à droite :

1. Activation générale de Ghost Tool.

2. Affichage des maillages fantômes.

3. Nombres de maillages Avant et Après.

4. Styles de maillage Fil de fer et Plein.

5. Déplacer les marqueurs.

6. Losange des marqueurs modifiables.

7. Affichage des trajectoires.

8. Nombres de trajectoires Avant et Après.

Chaque paire conserve l’ordre avant/après de la barre supérieure. La Timeline utilise des champs numériques natifs compacts.

1. Pour les paramètres d’échantillonnage et d’affichage, maintenez Fantômes ou Trajectoires dans la Timeline.

Le menu contient Image par image, Par clé et les intervalles d’échantillonnage. Autres paramètres des fantômes ouvre les options complètes.

Le losange inférieur affiche ou masque les marqueurs modifiables. Son menu de maintien distinct se trouve sur Affichage des marqueurs dans la barre supérieure. Comparer contient les commandes d’instantané dans les paramètres avancés.

L’en-tête de l’Éditeur de graphes propose aussi l’activation générale et une section de trajectoire lorsque Ghost Tool est actif.

<a id="drag-markers-repeatedly"></a>

## Déplacer des marqueurs à répétition

1. Activez Ghost Tool.

2. Activez les marqueurs modifiables pour une cible animée.

3. Cliquez sur Déplacer.

4. Cliquez sur un marqueur visible dans la Vue 3D.

5. Déplacez le marqueur.

6. Confirmez le déplacement.

Si vous cliquez dans une zone vide, l’outil de sélection reste en attente. Après un déplacement confirmé, Déplacer reste actif pour une autre modification. Tous les boutons Déplacer les marqueurs partagent ce mode.

Pour arrêter :

1. Cliquez à nouveau sur Déplacer ou appuyez sur Échap.

Pendant un déplacement, Échap annule ce déplacement. Ghost Tool rétablit les courbes et positions de marqueur d’origine pour ce déplacement. Les déplacements confirmés précédents restent des modifications distinctes.

1. Pour annuler les déplacements confirmés précédents, utilisez Annuler.

La désactivation de Ghost Tool termine les modifications. La perte d’une cible, un changement de fichier ou d’historique et l’arrêt de l’add-on terminent ou annulent aussi les sessions concernées.

Le déplacement de poignées de trajectoire permet aussi des sélections répétées.

![Commandes de cible et de poignées de Trajectoires](images/fr/4.3.3-path-targets.png)

*Figure 7. Trajectoires conserve le cube animé comme cible. Cet exemple active Marqueurs et Poignées.*

1. Activez Poignées de Bézier dans les paramètres de Trajectoires.

2. Lancez le déplacement de poignées.

3. Sélectionnez une poignée visible.

4. Déplacez la poignée.

5. Confirmez le déplacement.

6. Sélectionnez une autre poignée pour continuer.

L’accès par Shift+G reste disponible. Pendant le déplacement d’une poignée, Alt active ou désactive l’alignement des poignées. Échap annule le déplacement de poignée actif et quitte le mode.

<a id="choose-smooth-or-sharp-motion-edits"></a>

## Choisir des modifications de mouvement lisses ou marquées

1. Maintenez Déplacer.

2. Examinez Au relâchement.

3. Sélectionnez Remodeler les poignées ou Insérer une clé.

Remodeler les poignées change les poignées de Bézier existantes pour faire passer la courbe par l’échantillon déplacé. Cette action n’ajoute aucune clé.

Forme de courbe propose trois choix :

| Choix | Effet |
| --- | --- |
| Libre | Les poignées se règlent sans restriction d’angle. |
| Verrouillé | Les angles des poignées restent fixes. Leur longueur peut changer. |
| Lisse | L’influence des poignées se redistribue sur le segment. |

Paramètres > Modifier le mouvement contient les mêmes choix de relâchement et de forme de courbe que le menu de maintien Déplacer.

![Paramètres de Remodeler les poignées dans Modifier le mouvement](images/fr/4.3.3-reshape-options.png)

*Figure 8. Modifier le mouvement affiche Remodeler les poignées avec le réglage Libre. Portée règle l’influence sur les images voisines.*

Insérer une clé écrit une clé à l’image du marqueur. Ensuite, Lisser les voisins peut lisser les poignées des clés adjacentes. Portée des images voisines et Atténuation règlent l’influence sur les images environnantes.

![Commandes de clés et d’épinglage de Modifier le mouvement](images/fr/4.3.3-edit-motion.png)

*Figure 9. Modifier le mouvement affiche Insérer une clé, Lisser les voisins, l’interpolation progressive et l’épinglage. Dessiner des clés nécessite un trait d’annotation.*

La distance entre les échantillons affecte aussi la ligne visible. Des échantillons très espacés produisent une ligne grossière même si la courbe d’animation est lisse.

1. Pour examiner le résultat, sélectionnez un pas d’image plus petit.

Les échantillons d’affichage supplémentaires ne changent ni l’interpolation de l’animation ni la forme des poignées.

<a id="pin-markers-and-manage-path-targets"></a>

## Épingler les marqueurs et gérer les cibles de trajectoire

1. Cliquez sur Épingler.

2. Cliquez sur un marqueur visible pour changer son état d’épinglage.

3. Pour sélectionner un autre marqueur, cliquez à nouveau sur Épingler.

Épingler sélectionne un marqueur à la fois. Ce mode ne reste pas actif comme Déplacer. Plusieurs marqueurs peuvent rester épinglés simultanément.

Les marqueurs épinglés restent fixes pendant le remodelage. Une actualisation conserve les enregistrements des marqueurs épinglés correspondants.

Pour détacher tous les marqueurs épinglés :

1. Maintenez Épingler.

2. Sélectionnez Détacher tous les marqueurs.

Une cible de trajectoire ajoutée conserve un objet ou un os dans la liste. Elle ne fige pas tous les échantillons d’animation. Suivre la sélection change l’aperçu de sélection. Les cibles ajoutées avec Ajouter la trajectoire sélectionnée restent dans la liste.

La liste des trajectoires de Paramètres contient les commandes de cible. Affichage des marqueurs montre les points modifiables des trajectoires ajoutées. Points des clés fournit une aide d’affichage distincte.

La figure 7 montre la liste des trajectoires. La figure 9 montre Épingler et Tout détacher dans Modifier le mouvement.

<a id="live-updates-and-native-animation-editing"></a>

## Mises à jour directes et modifications natives de l’animation

Mise à jour directe des marqueurs et Mise à jour directe des pelures sont désactivées par défaut. Les scènes existantes conservent leurs valeurs enregistrées. Avec ces options désactivées, le dernier aperçu actualisé reste affiché pendant le parcours des images.

1. Pour Actualiser les marqueurs pendant le parcours des images et Actualiser les maillages pendant le parcours des images, maintenez l’icône générale de fantôme.

Ces commandes utilisent les mêmes paramètres de mise à jour des marqueurs et maillages. Suspendre les mises à jour interrompt les mises à jour automatiques.

Paramètres > Options des marqueurs contient les mêmes commandes de mise à jour des marqueurs. La figure 4 montre Mise à jour directe des pelures dans Options des pelures d’oignon.

![Options des marqueurs et commandes de mise à jour directe](images/fr/4.3.3-marker-options.png)

*Figure 10. Options des marqueurs contient Mise à jour directe des marqueurs, Suspendre les mises à jour et le délai de mise à jour.*

Pendant les gestes natifs de déplacement, rotation, mise à l’échelle et manipulation de gizmo, Ghost Tool conserve le dernier aperçu. Il ne parcourt pas les images pendant ces gestes. Après confirmation ou annulation, il attend la fin des modifications. Ensuite, il actualise les fantômes existants.

L’insertion automatique de clés peut rester active. Sans cette option :

1. Confirmez la pose.

2. Insérez la clé voulue.

Générer, dans les commandes avancées des marqueurs, régénère les aperçus sur demande.

Dans la version 4.3.3, Ghost Tool peut générer des marqueurs et pelures lorsque le gestionnaire de pointeur Timeline d’Anim Assist est inactif. Cette exception concerne uniquement ce gestionnaire passif.

Les curseurs de réglage actifs d’Anim Assist, transformations, gizmos, déplacements de tête de lecture et opérations modales inconnues suspendent toujours l’échantillonnage.

1. Avant de générer à nouveau, terminez le geste actif.

La correction ne change ni les valeurs par défaut de mise à jour des aperçus ni le comportement de l’animation source.

Les commandes avancées contiennent toujours Cibles des marqueurs, les sources de pelures, la plage, la subdivision et l’apparence. La visibilité des marqueurs et pelures en cache masque ou affiche les aperçus existants sans les reconstruire.

Effacer tous les fantômes supprime les marqueurs et pelures.

1. Pour masquer les aperçus sans les supprimer, utilisez les commandes de visibilité.

Un clic ou une sélection par boîte ne peut pas sélectionner des marqueurs masqués.

<a id="save-compare-and-restore-snapshots"></a>

## Enregistrer, comparer et rétablir des instantanés

1. Ouvrez Paramètres.

2. Ouvrez Comparer.

3. Sélectionnez la Portée voulue.

4. Confirmez la cible de capture affichée.

5. Activez les marqueurs pour la cible sélectionnée.

6. Cliquez sur Enregistrer un instantané.

![Comparer avec un instantané de référence Motion enregistré](images/fr/4.3.3-compare.png)

*Figure 11. Comparer contient l’instantané de référence Motion enregistré, avec Masquer, Rétablir, Enregistrer une variante et Supprimer.*

Portée propose Objet actif / Os sélectionnés, Trajectoire sélectionnée, Canaux des marqueurs sélectionnés et Tous les marqueurs de scène.

Les instantanés conservent des échantillons figés et les clés et poignées capturées. Ils restent avec la scène après enregistrement et réouverture. Désactiver puis réactiver l’add-on les conserve aussi.

Masquer ou Afficher change la superposition de l’instantané sans modifier l’animation. Enregistrer une variante crée un instantané alternatif indépendant et enregistre son origine. Cette variante reste disponible si vous supprimez le parent.

La scène peut conserver dix instantanés.

1. À capacité maximale, supprimez les enregistrements inutiles avant d’enregistrer un autre instantané.

La capture, les variantes, la liaison, la visibilité, la suppression et le rétablissement prennent en charge les commandes natives Annuler et Refaire.

Avant d’écrire, Rétablir valide l’identité de la scène, de l’objet, de l’action, de l’emplacement, de l’os et du canal. Il rétablit les courbes capturées et les marqueurs de la portée de l’instantané. Il actualise aussi l’affichage lorsque les mises à jour directes sont désactivées ou suspendues.

Rétablir ne change pas les objets sans rapport ni les modificateurs d’action arbitraires. Les anciennes références contenant seulement des échantillons rétablissent des valeurs échantillonnées adaptées lorsque Ghost Tool peut remodeler les courbes.

Les cibles remplacées nécessitent une liaison explicite. La liaison associe une référence à sa cible. Les emplacements d’action partagés empêchent la liaison.

1. Avant la liaison, rendez l’animation mono-utilisateur.

Lier à la cible active prend en charge un objet d’origine et ses canaux d’os nommés par référence. Les références importées avec plusieurs objets restent visibles et non liées. Ghost Tool ne peut pas lier ces objets à une seule cible.

Les liaisons suivent les changements de nom d’os. Après enregistrement et réouverture, l’identité du canal identifie la courbe. Le retour arrière rétablit les valeurs d’origine après annulation. Pendant un geste, Ghost Tool n’applique pas aux courbes de remplacement les écritures de retour arrière destinées aux courbes d’origine.

<a id="transfer-snapshots-and-use-advanced-tools"></a>

## Transférer les instantanés et utiliser les outils avancés

1. Pour transférer les données de comparaison, exportez les instantanés en JSON.

Importer valide et fusionne les enregistrements. Si des identifiants correspondent à des enregistrements existants, Importer en attribue de nouveaux. Il rejette les versions non prises en charge et les enregistrements dépassant la capacité. Un import rejeté n’ajoute aucun enregistrement partiel.

Les références importées et anciennes restent visibles. Leur rétablissement nécessite une liaison explicite, car JSON ne peut pas prouver l’identité de l’objet d’origine. Un import échoué conserve les enregistrements de scène existants illisibles.

![Paramètres d’export et d’import JSON de Ghost Tool](images/fr/4.3.3-transfer-settings.png)

*Figure 12. Paramètres contient Exporter et Importer pour les données JSON de Ghost Tool.*

Modifier le mouvement contient les préréglages et commandes personnalisées d’interpolation progressive. Cette interpolation règle la variation de vitesse du mouvement. Dessiner des clés transforme le trait d’annotation le plus long en trajectoire de position. Les traits qui le croisent identifient les clés. La boîte Dessiner des clés conserve la cible sélectionnée.

Paramètres, le panneau latéral et l’étagère contiennent Ressenti physique, Apparence, Comparer et les autres outils avancés.

La figure 9 montre l’interpolation progressive et Dessiner des clés dans Modifier le mouvement.

![Commandes d’aperçu physique et d’application aux clés](images/fr/4.3.3-physics.png)

*Figure 13. Physique affiche les aperçus de trajectoire de lancer et Ressenti physique. Appliquer aux clés écrit l’aperçu dans les clés d’animation.*

![Commandes d’apparence des couleurs de marqueurs et trajectoires](images/fr/4.3.3-look.png)

*Figure 14. Apparence règle les couleurs de marqueurs, Lignes d’arc, Graduations d’espacement et les étiquettes d’image.*

<a id="troubleshooting-and-version-evidence"></a>

## Dépannage et preuves de version

| Problème | Vérification ou action |
| --- | --- |
| Aucun aperçu | Activez Ghost Tool. Vérifiez l’animation de la cible, la visibilité et des nombres non nuls. |
| Points modifiables absents | Ajoutez la cible à Trajectoires. Activez Affichage des marqueurs. |
| Échantillons trop espacés | Réduisez le pas d’image ou changez l’intervalle entre les clés. |
| Une seule icône de fantôme dans la Timeline | Activez cette icône pour déplier la barre. |
| Barre d’outils masquée | Sélectionnez Barre d’outils supérieure dans les préférences. Sélectionnez Vue > Afficher la barre Ghost Tool. |
| Commandes hors d’une vue divisée | Faites glisser la ligne native horizontalement avec le bouton central. |
| Échantillonnage en attente pendant une modification | Confirmez ou annulez le geste de modification actif. |
| Génération bloquée avec Anim Assist inactif | Installez Ghost Tool 4.3.3. Redémarrez Bforartists. |

La figure 1 montre les préférences de Ghost Tool. Les figures 5 et 6 montrent la barre Timeline dépliée et repliée.

L’échantillonnage des marqueurs suit celui de Trajectoires. Les préférences de largeur d’étagère gauche restent disponibles. La vérification complète des largeurs et échelles était inachevée en 4.2.11. Ce guide ne revendique aucune nouvelle correction de largeur d’étagère.

L’ancienne implémentation de barre directe a reçu 188 vérifications ciblées en arrière-plan. Ces résultats concernent cette implémentation. Ils ne proviennent pas d’une nouvelle exécution pour ce guide.

Les [notes de version 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/RELEASE-NOTES.md) décrivent les vérifications ciblées de régression et d’interface sur Bforartists officiel 5.2.3. La vérification d’interface utilisait Anim Assist 12.11.0 et des ressources utilisateur isolées. Elle a vérifié neuf marqueurs et trois aperçus de maillage. Les clés source et la tête de lecture sont restées inchangées.

Ces preuves de publication ne certifient pas chaque opération, personnage de production ou future version hôte. Le [reçu du paquet](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/package-receipt.json) indique l’intégrité du ZIP, la version et la correspondance avec la source.

1. Indiquez la cible, l’opération et l’étape échouée dans le [suivi des problèmes](https://github.com/Axleonex/B4Artists_Toolkit/issues).
