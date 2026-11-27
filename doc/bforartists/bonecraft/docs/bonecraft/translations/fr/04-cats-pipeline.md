# Le pipeline CATS {#the-cats-pipeline}

[← Sommaire](index.md)

**Lisez ceci avant votre première utilisation d’un outil CATS.**

Les outils CATS proposent une procédure de préparation recommandée. Examinez les phases dans cet ordre. Sautez celles dont votre avatar n’a pas besoin. Avant de modifier les données du maillage ou du rig, enregistrez un point de sauvegarde. Inspectez chaque résultat. Les outils restent disponibles même si une phase précédente est incomplète.

---

## Les six phases, dans l’ordre {#the-six-phases-in-order}

Pipeline Status, dans l’onglet CATS, répertorie les phases et coche chacune à sa fin :

1. **Fix Model** — Examinez les options de nettoyage, par exemple supprimer les doublons et corriger les normales. Inspectez le maillage après l’opération.

2. **Material Atlas** — Combinez les matériaux de l’avatar sur une seule planche de textures (facultatif, pour les performances).

    1. Gardez **Preserve Backup Duplicate** activé jusqu’à l’examen du résultat.

    2. Sélectionnez **Analyze Materials**.

    3. Sélectionnez les sources.

    4. Sélectionnez **Bake Checked Sources**.

    5. Examinez le résultat.

    6. Acceptez ou rétablissez avant un autre précalcul.

    Consultez [Material Atlas Combiner](09-cats.md#material-atlas-combiner).

3. **Visemes** — Générez les 15 formes de bouche de synchronisation labiale VRChat à partir des trois formes de base (A, O, CH).

4. **Eye Tracking** — Configurez le mouvement des yeux dans VRChat avec les os des yeux de l’avatar.

5. **Pose to Shape Key** — Capturez le mélange actuel de clés de forme du maillage dans une nouvelle clé. Ce bouton ne précalcule pas la déformation des os d’armature. Pour cela, consultez la [procédure native de pose d’os](09-cats.md#save-a-bone-deformed-pose).

6. **Apply All Transforms** — Appliquez position, rotation et échelle au maillage et à l’armature. Comparez le résultat avant l’exportation.

---

## Pipeline Status et Operation Ledger {#pipeline-status-and-the-operation-ledger}

Pipeline Status montre une ligne par phase. Quand une phase se termine, sa ligne affiche une coche. La scène stocke cet état dans votre fichier.

Operation Ledger énumère chaque opération CATS, la plus récente en dernier, avec son heure et son résultat. Changed indique que l’opération a modifié le modèle. Clean indique qu’aucun changement n’était nécessaire. Failed indique un échec. **Copy** copie le registre dans le presse-papiers pour une demande d’assistance. **Clear** le vide.

L’ordre est conseillé. Si une phase précédente est incomplète, les outils fonctionnent tout de même avec un avertissement comme « Run Fix Model first for best results » : exécutez d’abord Fix Model pour de meilleurs résultats. Examinez l’avertissement avant de continuer.

Description de l’image source anglaise (image omise) : Pipeline Status énumère les six phases dans l’ordre recommandé.

*Panneau contextuel natif, BoneCraft 9.2.18. Pipeline Status énumère les six phases dans l’ordre recommandé.*

Description de l’image source anglaise (image omise) : Operation Ledger avant toute entrée. Copy et Clear agissent sur les entrées enregistrées.

*Panneau contextuel natif, BoneCraft 9.2.18. Operation Ledger avant toute entrée. Copy et Clear agissent sur les entrées enregistrées.*

---

## Pourquoi cet ordre {#why-this-order}

Cet ordre facilite l’examen d’un type de changement à la fois :

- **Examinez d’abord le nettoyage.** Selon ses options, Fix Model peut modifier la géométrie ou supprimer des données. Vérifiez le maillage et ses clés de forme existantes avant de générer davantage de données.

- **Examinez les formes de bouche, puis les yeux.** Testez les visèmes générés ou associés. Eye Auto-Detect recherche les noms d’os. Vérifiez les affectations Left Eye et Right Eye séparément de l’orientation des os et des contraintes.

- **Examinez ensuite la capture d’expression.** Pose to Shape Key capture un mélange de clés de forme, pas la déformation des os.

    1. Remettez les valeurs des clés d’origine à 0.

    2. Testez la nouvelle clé à 1.

    Pour enregistrer une pose déformée par les os, utilisez la procédure native liée plus haut.

- **Examinez les transformations avant l’exportation.** Les appliquer modifie les données des objets et réinitialise les canaux de transformation. Les outils précédents restent disponibles. Comparez le résultat et les réglages d’exportation. Pour rétablir l’état antérieur, utilisez Undo ou un point de sauvegarde.

---

## Avant de sauter une phase {#before-skipping-a-phase}

**Sauter Fix Model :**
Inspectez la géométrie importée, les normales, les poids, les modificateurs et les clés de forme existantes. Sélectionnez les opérations de nettoyage nécessaires. Vérifiez séparément les problèmes de bouche et de mouvement des yeux. Une phase non cochée ne suffit pas à identifier leur cause.

**Sauter Visemes :**
Sans visèmes générés ou associés, l’avatar n’a pas de synchronisation labiale. Si les clés de forme de visèmes existent déjà, associez-les dans VRChat Viseme Mapping (guide 8). Ne générez pas inutilement des remplacements. Pipeline Status laisse alors Visemes non coché. C’est normal.

**Sauter Eye Tracking :**
L’avatar ne bouge pas les yeux dans VRChat et regarde droit devant lui. C’est acceptable s’il n’a pas d’os des yeux.

**Sauter Pose to Shape :**
Facultatif : sautez cette phase si vous n’avez pas besoin d’un instantané du mélange actuel de clés de forme. Les expressions existantes peuvent être examinées et utilisées sans créer une autre clé.

Suivant : [Outils de rig](05-rig-tools.md)
