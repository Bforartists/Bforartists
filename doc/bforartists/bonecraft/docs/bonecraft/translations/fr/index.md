# Manuel de BoneCraft {#bonecraft-manual}

<!-- Print footer for exported PDFs. -->
<style>
@media print {
  p:has(> img):has(+ p > em:only-child) {
    break-after: avoid;
  }
  p:has(> img) + p:has(> em:only-child) {
    break-before: avoid;
    break-inside: avoid;
  }
  section.chapter > p:last-child {
    break-before: avoid;
  }
  @page {
    @bottom-center {
      content: "Page " counter(page) " sur " counter(pages);
      font-family: "Segoe UI", sans-serif;
      font-size: 9pt;
      color: #555;
    }
  }
}
</style>

**Version candidate locale de BoneCraft 9.2.19.** BoneCraft est une boîte à outils de rigging et de création d’avatars pour Bforartists.

Cette édition sans images couvre les commandes, la navigation et les corrections de panneaux de la version candidate de BoneCraft 9.2.19. Elle conserve les 12 chapitres et les instructions écrites des ateliers. Les fichiers de captures d’écran sont omis ; les descriptions d’images et les légendes du texte source anglais sont conservées sous forme de notes.

La compilation de Bforartists fournie à l’origine contient BoneCraft 9.2.18. Le nouvel aperçu local contient la version candidate 9.2.19. Dans les deux cas, BoneCraft est activé par les réglages d’usine. Ces compilations ne nécessitent aucune installation par fichier ZIP.

Pour **BoneCraft** et **Rig Builder**, ouvrez l’étagère d’outils de gauche (**T**). Pour **CATS**, ouvrez la barre latérale de droite (**N**). Consultez le [démarrage rapide de la compilation fournie](01-start.md#supplied-build-quick-start).

Les chemins de l’interface et les réglages restent les mêmes. Les outils facultatifs et leurs dépendances conservent leurs prérequis. Ces instructions concernent l’aperçu local de la contribution. Le paquet officiel de Bforartists 5.2.3 ne contient pas cet ensemble. Les utilisateurs de la version autonome doivent suivre la section [Installer BoneCraft](01-start.md#installing-bonecraft).

La revue du code source couvre l’installation de MMD, la préparation des atlas de matériaux, les noms à l’exportation, la restauration du mode, les formulaires de mécanismes enregistrés et les corrections actuelles des panneaux.

Pour l’installation et le repérage dans l’interface, lisez [Prise en main](01-start.md). Pour les changements jusqu’à la version candidate locale 9.2.19, lisez [Nouveautés](11-whats-new.md).

Les ateliers du texte source anglais conservent leurs vérifications historiques et les versions indiquées sur leurs captures. Cette édition sans images omet ces captures et conserve leurs descriptions et légendes écrites. Elle ne prétend pas que chaque tutoriel a été rejoué avec la version 9.2.19.

Cette édition suit les 12 chapitres anglais actuels, y compris l’atelier développé du chapitre 6 et le chapitre 12. Les anciens sommaires traduits et les chapitres incomplets sont des versions antérieures historiques ; ils ne définissent pas le contenu de cette édition.

La version autonome publiée reste la 9.2.18. La version candidate locale 9.2.19 n’a pas été publiée. Consultez les [notes de version 9.2.18](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md) pour cette publication.

Le tutoriel Crescent Rose du texte source anglais comprend huit étapes de préparation FBX, 30 étapes de Mechanisms et 52 captures annotées vérifiées sur l’interface 9.1.2. Cette édition sans images conserve les étapes écrites, les descriptions d’images et les légendes, tout en omettant les fichiers d’images.

## Chapitres {#chapters}

Complément vidéo : [découverte de l’IK/FK pour débutants et fichier d’exercice](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

Utilisez les liens des chapitres ci-dessous. La pagination du PDF change lors de la reconstruction du manuel.

1. [Prise en main](01-start.md) — présentation de BoneCraft, installation et emplacement des outils.
2. [Guides 1–7](02-guides-a.md) — premier avatar, VRoid, MMD, noms d’os, mappage humanoïde, cheveux et vêtements.
3. [Guides 8–13](03-guides-b.md) — synchronisation labiale, performances, poses, fusion de rigs, problèmes d’envoi et CATS.
4. [Le pipeline CATS](04-cats-pipeline.md) — les six phases, le registre et l’importance de leur ordre.
5. [Outils de rig](05-rig-tools.md) — interface du rig, animation, poids et commandes du rig.
6. [Rig Builder](06-rig-builder.md) — construction d’un rig, atelier écrit Simple Human → mannequin → Auto-Rig → IK/FK et fusion d’os.
7. [Mechanisms](07-mechanisms.md) — articulations et liens pour accessoires et machines : charnières, glissières, engrenages et séquences.
8. [Outils VRChat](08-vrchat.md) — outils VRChat, VRM et MMD, hub d’E/S et tableau des tâches.
9. [Outils CATS](09-cats.md) — chaque outil CATS, un par un.
10. [Solutions rapides et glossaire](10-reference.md) — problèmes courants et vocabulaire du manuel.
11. [Nouveautés](11-whats-new.md) — changements par version.
12. [Tutoriel : Crescent Rose avec Mechanisms](12-crescent-rose.md) — exemple guidé : créer pas à pas le rig d’une faux-fusil transformable, avec instructions écrites et descriptions d’images du texte source anglais conservées.
