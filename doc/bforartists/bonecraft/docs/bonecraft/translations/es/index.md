# Manual de BoneCraft {#bonecraft-manual}

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
      content: "Página " counter(page) " de " counter(pages);
      font-family: "Segoe UI", sans-serif;
      font-size: 9pt;
      color: #555;
    }
  }
}
</style>

**Versión candidata local de BoneCraft 9.2.19.** BoneCraft es un conjunto de herramientas de rigging y avatares para Bforartists.

Esta edición solo de texto abarca los controles, la navegación y las reparaciones de paneles de la versión candidata BoneCraft 9.2.19. Conserva los 12 capítulos y las instrucciones escritas de los talleres. Se omiten los archivos de capturas; sus descripciones de imágenes y pies escritos del original en inglés se conservan como notas.

La compilación original suministrada de Bforartists incluye BoneCraft 9.2.18. La nueva versión preliminar local incluye la candidata 9.2.19. Ambas activan BoneCraft mediante los ajustes de fábrica. Estas compilaciones no necesitan instalar un ZIP.

Para **BoneCraft** y **Rig Builder**, abre la Tool Shelf izquierda (**T**). Para **CATS**, abre la barra lateral derecha (**N**). Consulta [Inicio rápido de la compilación suministrada](01-start.md#supplied-build-quick-start).

Las rutas de interfaz y los ajustes son los mismos. Las herramientas y dependencias opcionales conservan sus requisitos. Estas instrucciones describen la versión preliminar de la contribución local. El paquete oficial Bforartists 5.2.3 no incluye este conjunto. Si usas la versión independiente, sigue [Instalar BoneCraft](01-start.md#installing-bonecraft).

La revisión del código fuente abarca la instalación de MMD, la preparación de atlas de materiales, los nombres de exportación, la restauración de modos, las formas guardadas de mecanismos y las reparaciones actuales de paneles.

Para instalar y conocer la distribución de la interfaz, lee [Primeros pasos](01-start.md). Para los cambios hasta la candidata local 9.2.19, lee [Novedades](11-whats-new.md).

Los talleres del original en inglés conservan sus comprobaciones históricas y las etiquetas de versión de las capturas. Esta edición solo de texto omite esas imágenes y conserva sus descripciones y pies escritos. No afirma que todos los tutoriales se hayan repetido con 9.2.19.

Esta edición sigue los 12 capítulos actuales en inglés, incluido el taller ampliado del capítulo 6 y el capítulo 12. Los índices traducidos anteriores y los capítulos incompletos son predecesores históricos, no el alcance de esta edición.

La versión independiente publicada sigue siendo 9.2.18. La candidata local 9.2.19 no se ha publicado. Lee las [notas de la versión 9.2.18](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md) para esa publicación.

El tutorial Crescent Rose del original en inglés incluye ocho pasos de preparación FBX, 30 pasos de Mechanisms y 52 capturas anotadas comprobadas con la interfaz 9.1.2. Esta edición solo de texto conserva los pasos escritos, las descripciones de imágenes y los pies, pero omite los archivos de imagen.

## Capítulos {#chapters}

Complemento en vídeo: [Guía de iniciación a IK/FK y archivo de práctica](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

Usa los enlaces de capítulos siguientes. La paginación del PDF cambia al reconstruir el manual.

1. [Primeros pasos](01-start.md) — qué es BoneCraft, cómo instalarlo y dónde está cada cosa.
2. [Guías 1–7](02-guides-a.md) — primer avatar, VRoid, MMD, nombres de huesos, mapeo humanoide, pelo y ropa.
3. [Guías 8–13](03-guides-b.md) — sincronización labial, rendimiento, poses, unión de rigs, problemas de subida y CATS.
4. [El pipeline de CATS](04-cats-pipeline.md) — las seis fases, el registro y por qué importa el orden.
5. [Herramientas de rig](05-rig-tools.md) — interfaz del rig, animación, pesos y controles del rig.
6. [Rig Builder](06-rig-builder.md) — crear un rig nuevo, un taller escrito Simple Human → maniquí → Auto-Rig → IK/FK y Bone Merge.
7. [Mechanisms](07-mechanisms.md) — articulaciones y vínculos para accesorios y máquinas: bisagras, deslizamientos, engranajes y secuencias.
8. [Herramientas de VRChat](08-vrchat.md) — herramientas de VRChat, VRM y MMD, I/O Hub y Task Board.
9. [Herramientas de CATS](09-cats.md) — cada herramienta de CATS, una por una.
10. [Soluciones rápidas y glosario](10-reference.md) — problemas habituales y los términos de este manual.
11. [Novedades](11-whats-new.md) — cambios por versión.
12. [Tutorial: Crescent Rose con Mechanisms](12-crescent-rose.md) — ejemplo práctico: crear paso a paso el rig de una guadaña-fusil transformable, con instrucciones escritas y descripciones de imágenes conservadas del original en inglés.
