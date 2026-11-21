# Novedades {#whats-new}

[← Contenido](index.md)

Las versiones más recientes aparecen primero.

## 9.2.19 — Controles de paneles (candidato local) {#9219--panel-controls-local-candidate}

Este candidato local no se ha publicado. La versión independiente publicada sigue siendo 9.2.18.

- Collections y Visibility Bookmarks inicializan sus ajustes fuera del dibujado de paneles.
- Los paneles agrupados usan sus propios controles y comprueban la selección y el modo actuales.
- Hair Physics lee los huesos de pose seleccionados en las aplicaciones anfitrionas actuales.
- Bone Inspector muestra el giro del hueso en reposo y copia nombres mediante su botón del encabezado.
- Eye Tracking muestra valores en grados y conserva los ajustes guardados.

El manual inglés añade imágenes correspondientes a las herramientas y los ajustes. Las imágenes anteriores conservan sus etiquetas de versión originales.

## 9.2.18 — Formas guardadas de mecanismos {#9218--saved-mechanism-forms}

Las formas guardadas anteriormente siguen siendo legibles y utilizables en las compilaciones actuales de Bforartists. Abrir o aplicar una forma no vuelve a guardarla. **Save Form** captura los valores actuales con el formato actual. Los manejadores, deslizadores y ubicaciones de paneles existentes no cambian.

La versión corrige los diagnósticos de compatibilidad en aplicaciones anfitrionas más recientes. El diagnóstico por sí solo no demostraba que las aplicaciones anteriores no pudieran usar formas guardadas. Consulte [Formas](07-mechanisms.md#forms) y las [notas de la versión](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md).

Esta es la versión independiente del Toolkit. No establece su aceptación en Bforartists oficial. Los límites históricos de las capturas y las pruebas de tutoriales se mantienen en sus capítulos.

## 9.2.17 — Nombres de exportación y restauración del modo {#9217--export-naming-and-mode-restoration}

**Unity / VRChat** y **Unreal Engine 5** ofrecen ahora **Bone Names**: **Keep Original Names**, **Unity-Preset** y **Unreal-Preset**. La vista previa muestra los huesos reconocidos y los nombres propuestos. Los nombres afectan a las copias de exportación, incluidos los grupos de vértices, los canales de animación y las referencias de los archivos auxiliares de Unity. El rig de trabajo conserva sus nombres.

Los dos botones principales de exportación a motores aceptan ahora Object Mode, Pose Mode y Edit Mode. Restauran el modo y la selección originales tras la exportación o la limpieza. El horneado FBX de la acción activa ya no necesita una tira NLA independiente.

Los huesos humanoides opcionales reconocidos y los dedos de manos y pies participan en el cambio de nombres. Los nombres en conflicto o las asignaciones ambiguas bloquean el cambio. Estos perfiles conservan la jerarquía, la orientación y la pose de reposo. No construyen un esqueleto Manny/Quinn.

La salida de **Export (Profile)** con nombres cambiados admite **Active Action** y **No Animation**. **All Actions** requiere **Keep Original Names**. Consulte [Exportación a motores de videojuegos](08-vrchat.md#game-engine-export) y las [notas de 9.2.17](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.17/RELEASE-NOTES.md).

## 9.2.15 — Flujo revisado del atlas de materiales {#9215--reviewed-material-atlas-workflow}

El panel presenta ahora tres etapas: selección del destino, selección de materiales y texturas, y horneado y revisión. **Smart Combine Materials** es el acceso directo automático inicial. Después del análisis, **Refresh Analysis** reconstruye las listas. **Bake Checked Sources** hornea las opciones revisadas.

Ambas listas de fuentes tienen **Select All** y **Deselect All**. Solo cambian las casillas Include dentro del grupo activo y de la lista de fuentes correspondiente. Las texturas ausentes siguen sin marcar. La selección en bloque no activa un grupo desactivado. **Object → Atlas Source Selection** ofrece las mismas acciones.

**Source Details** empieza plegado. **Copy Debug Report** está en **Advanced Options**. Backup, Accept y Revert siguen visibles. Estos cambios de interfaz conservan el flujo de horneado y las restricciones de preservación existentes.

## 9.2.14 — Mallas solo con color {#9214--color-only-meshes}

Las mallas que solo tienen color y carecen de UV creadas reciben la capa UV del atlas horneado durante el ensamblado final.

## 9.2.13 — Recuentos de materiales {#9213--material-counts}

Las estimaciones y los resultados de materiales cuentan las ranuras del atlas en todas las mallas de salida. Revert restablece esos resultados.

## 9.2.12 — Exportación UV0 {#9212--export-uv0}

La malla del atlas reconstruida exporta `atlas_uv` como UV0 mientras **Keep Source UV Maps** esté desactivado. Conservar los mapas de origen puede dejar el atlas en UV1.

## 9.2.11 — Comprobaciones de fuentes modificadas {#9211--changed-source-checks}

La comprobación previa rechaza las fuentes de materiales analizadas que falten o hayan cambiado antes de crear una copia de seguridad del atlas.

1. Actualice el análisis.

2. Revise las opciones de fuentes de nuevo.

## 9.2.10 — Materiales excluidos {#9210--excluded-materials}

El ensamblado del atlas conserva los materiales excluidos y las referencias compartidas a materiales.

## 9.2.9 — Fuentes ocultas en el renderizado {#929--render-hidden-sources}

El combinador hornea las fuentes ocultas en el renderizado mediante copias temporales. Revert restaura la visibilidad original.

## 9.2.8 — Entradas de sombreado conectadas {#928--connected-shader-inputs}

El combinador conserva durante el horneado los grafos conectados de tinte, mapeado y alfa de Principled. MToon conserva su ruta alternativa. **Metallic** y **Pack ORM Channels** siguen bloqueados por la comprobación previa.

## 9.2.7 — Clasificación de transparencias {#927--transparency-classification}

La clasificación de materiales contempla la opacidad DITHERED moderna y el alfa vinculado o constante. El ajuste de renderizado por sí solo ya no obliga a clasificar un material opaco en un grupo transparente.

## 9.2.6 — Instalación de MMD y PMX {#926--mmd-and-pmx-installation}

El instalador reconoce las extensiones MMD modernas y los complementos antiguos. La instalación de extensiones conserva sus dependencias e informa de los repositorios locales no disponibles. Se reconoce una extensión activada incluso sin los metadatos de los complementos antiguos. Las importaciones PMX canceladas siguen canceladas, en lugar de informar de un resultado satisfactorio.

El [registro de reparación fechado](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md) abarca 9.2.6–9.2.15 y sus comprobaciones con escenarios de prueba generados. La [revisión de interfaz de 9.2.15](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md) documenta las comprobaciones de operadores y los límites de las pruebas visuales. Estos registros históricos no afirman que se haya vuelto a ejecutar todo el manual en 9.2.18.

## 9.2.5 — Pestaña de catálogo Starter Rigs {#925--starter-rigs-catalog-tab}

Starter Rigs usa ahora una pestaña de catálogo en el estante de recursos nativo inferior. Sustituye los controles de la esquina superior izquierda de la vista. Para mostrar la pestaña junto a otros catálogos, active **Starter Rigs** una vez en el menú de catálogos del estante. La importación nativa de recursos y **Add → Armature → Starter Rig Catalog** siguen disponibles.

## 9.2.4 — Task Board y herramientas nativas {#924--task-board-and-native-tools}

**Open Health Check** ejecuta ahora la validación del rig y abre sus resultados. Antes de usarlo, seleccione un armature o su malla vinculada. **Quick Wins** muestra hasta tres recomendaciones. **Remaining Tasks** excluye esas tarjetas. **Refresh Task Board** vuelve a comprobar el estado.

Place Rig Markers y Build Mechanism siguen disponibles como herramientas de la vista. Su registro ya no interfiere con Grab/Move nativo ni con el cambio cíclico de herramientas en Object Mode y Pose Mode.

## 9.2.3 — Ubicación de la exportación a VRChat {#923--vrchat-export-location}

Elimina el panel duplicado Export to VRChat de Avatar Tools. La exportación sigue en CATS → Import / Export → Unity / VRChat.

## 9.2.2 — Interfaz actual {#922--current-interface}

Cada pestaña contiene un grupo de espacio de trabajo. Setup Rigging, Skin, Review, Avatar Tools y Facial son secciones desplegables dentro de las pestañas. Las rutas siguientes usan etiquetas de interfaz en inglés. Las etiquetas traducidas dependen de la preferencia Language.

- Bone Merge → BoneCraft → Setup Rigging
- Delta Mush / Proximity Wrap → BoneCraft → Skin
- Viseme Library / Lip Sync → CATS → Avatar Tools
- VRChat Viseme Mapping / Face Tracking → CATS → VRChat Tools → Facial

## 9.2.0 (octubre de 2026) {#920-october-2026}

- **Catálogo inicial completo:** los nueve esqueletos/metarigs incluidos tienen miniaturas desde el principio. Son Basic Humanoid, Simple Human, Full Human, Basic Quadruped, Cat, Horse, Wolf, Bird y Shark. El selector de catálogos los agrupa en Humans, Quadrupeds y Other Animals.
- **Rigify cuando hace falta:** Basic Humanoid funciona de forma independiente. Los rigs iniciales de Rigify siguen visibles cuando Rigify está desactivado. Seleccionar uno ofrece **Enable Rigify & Add Rig** o Cancel. La cancelación, un fallo de activación o la falta de un preajuste no añade ningún rig.
- **Estante opcional, ubicación histórica de 9.2.0:** el interruptor **Starter Rigs** del encabezado de la vista volvía al estante de recursos normal. La elección persistía en las preferencias. La versión 9.2.5 sustituye este interruptor por una pestaña de catálogo nativa. **Add → Armature → Starter Rig Catalog** sigue abriendo el selector como ventana emergente.
- **Clic o arrastre:** hacer clic en un rig inicial lo añade, igual que soltarlo dentro de la vista. El ajuste a la malla empieza activado. La asignación de pesos y la generación de controles empiezan desactivadas. Adjust Last Operation controla estas opciones. Las comprobaciones nativas de clic, arrastre y suelta, cancelación y deshacer/rehacer usaron Bforartists 5.2.0.

## 9.1.2 (octubre de 2026) {#912-october-2026}

- **Interruptor Scene Properties:** Preferences > Tabs tiene una nueva fila Scene Properties. Su botón Show controla todas las secciones de BoneCraft en la pestaña Properties > Scene. Son Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools e Import / Export. El interruptor empieza activado y se muestra azul mientras está activado. No desactiva el complemento ni cambia las pestañas de la vista o la pestaña Armature. Consulte [Dónde está cada cosa](01-start.md#where-things-are).

## 9.1.1 (octubre de 2026) {#911-october-2026}

- **Iconos más claros:** cada icono tiene ahora un único significado en toda la interfaz. Unos 60 botones recibieron iconos de Bforartists que se ajustan mejor a sus funciones. Algunos ejemplos son Apply All Transforms, Decimate, Normalize Names, Translate, Merge, Separate, Blend Pose y Lip Sync. Cada botón usa el mismo icono en todos los paneles.
- **Paneles más tranquilos:** los encabezados y el texto fijo ya no llevan iconos temáticos. Las indicaciones que informan de un estado muestran el icono de información, advertencia o verificación.
- **Cuadrícula de iconos legible:** cada botón de las pestañas Pose y Weights de Tool Shelf tiene su propio icono, para que un estante estrecho siga siendo legible.

## 9.1.0 (octubre de 2026) {#910-october-2026}

- **Herramientas donde Bforartists coloca las suyas:** BoneCraft añade entradas a Add → Armature y a los menús Pose, Weights y Object. También añade paneles de botones a las pestañas Pose y Weights de Tool Shelf de Bforartists.
- **Ejecutar primero, ajustar después:** Quick Rig, Fit Dropped Rig y las herramientas de pesos se ejecutan inmediatamente con los últimos valores usados. Ribbon, Spline IK, Delta Mush y las herramientas de huesos CATS también se ejecutan inmediatamente con los últimos valores usados. Adjust Last Operation controla sus opciones después. Las herramientas usan menos ventanas emergentes de confirmación.
- **Acciones primero, opciones plegadas:** varios paneles muestran botones encima de una sección plegada con ajustes opcionales. Las entradas obligatorias y los interruptores de limpieza de Fix Model siguen encima de la acción. Los ajustes usan casillas en vez de botones. Los encabezados de paneles no tienen iconos.
- **Herramientas gestuales:** Place Rig Markers y Build Mechanism están en la barra de herramientas de la vista. Place Rig Markers coloca el siguiente marcador de Auto-Rig Wizard al hacer clic en la malla. Build Mechanism inicia una articulación o un enlace al hacer clic en una pieza.
- **Secciones de avatar, ubicación histórica de 9.1.0:** Avatar Tools contenía la asignación humanoide, el pelo, los visemas y la exportación. La sección independiente VRChat Tools agrupa las utilidades Performance, Clothing y Naming. La exportación está ahora en **Import / Export → Game Engine Export → Unity / VRChat**.
- **Descripciones emergentes:** todos los operadores y todas las opciones explican su función.
- **Mostrar en vez de ocultar:** cuando no hay un rig disponible, las secciones siguen visibles y explican qué seleccionar. Auto-Rig Wizard aparece primero en Rig Builder. Los estantes empiezan con anchura suficiente para leerlos.
- **Correcciones:** Generate Spline IK vuelve a funcionar. Add Influence usa el hueso elegido. Las vistas previas de visemas usan su conjunto.

## 9.0.0 (octubre de 2026) {#900-october-2026}

- **Mechanisms:** una nueva sección en la pestaña BoneCraft y la pestaña Properties Scene crea rigs de accesorios y máquinas. Sus tipos son Hinge, Slide, Telescope, Piston, Gear Link, Follow y Sequence. Unos pasos guiados los construyen. Test comprueba su movimiento. BoneCraft nunca sobrescribe automáticamente una edición manual. **Keep mine** conserva la edición. **Restore** reconstruye el mecanismo. Consulte [Mechanisms](07-mechanisms.md).
- **Archivo de ejemplo:** `examples/crescent-rose/` contiene Crescent Rose con un rig de Mechanisms (formas de guadaña, rifle y compacta), y el [capítulo 12](12-crescent-rose.md) del manual lo construye paso a paso.
- **Lado de las pestañas:** cada pestaña de la vista puede estar en Tool Shelf a la izquierda o en la barra lateral derecha (Preferences → Tabs → Left / Right). BoneCraft y Rig Builder empiezan a la izquierda, y CATS a la derecha.
- **Rig Builder:** siempre aparece en la pestaña Properties Scene y también tiene su propia pestaña en la vista. Una disposición compacta cabe en un Tool Shelf estrecho. La biblioteca de recursos BoneCraft Rigs incluye Basic Humanoid. Fit Dropped Rig ajusta un rig soltado desde el estante de recursos.
- **Pestaña CATS:** Import / Export se trasladó a la pestaña CATS. CATS, VRChat e Import / Export también están siempre en la pestaña Scene.
- **Show Helpers:** una preferencia muestra u oculta el texto didáctico de BoneCraft. Compact Mode controla la misma preferencia.
- **Rig Validator:** los nombres de huesos con guiones pasan la validación. Los drivers solo generan advertencias para expresiones que necesitan Python. Las comprobaciones también abarcan rigs de Mechanisms. La tarea de validación de Task Board vuelve a informar de sus resultados.
- **Nombre:** el complemento se llama BoneCraft.

## 8.9.x (septiembre–octubre de 2026) {#89x-septemberoctober-2026}

- **8.9.6:** toda la pieza del vestido sigue los huesos de la falda sin atravesar la cadera. Las correctivas de las comisuras al abrir la mandíbula admiten labios adherentes.
- **8.9.5:** el cambio IK/FK del codo conserva la pose sin saltos. La detección de hombros es simétrica. Los marcadores oculares ya no saltan. Control Picker muestra la selección. Otros cambios incluyen comisuras más redondeadas, una corrección del vestido sobre el muslo, clavículas relajadas en la transferencia de animación y exportación en pose T.
- **8.9.4:** las correctivas sustituyen Preserve Volume para conseguir rodillas más redondeadas. Esta versión también añade claves de contacto para flexiones profundas y una mezcla en la unión del hombro.
- **8.9.3:** los huesos de falda de dos segmentos siguen las piernas. Las piernas también empujan estos huesos.
- **8.9.2:** las claves de forma crean parpadeos sin pliegues en los párpados. La abertura de la boca es ovalada.
- **8.9.1:** la vinculación de mallas densas es más rápida (678,000 vértices, seiscientos setenta y ocho mil: de 232 s a 57 s). Bone heat usa una malla de aproximación más ligera en lugar de fallar silenciosamente.
- **8.9.0:** esta versión añade claves de forma correctivas de articulaciones y controles faciales para apuntar los ojos, parpadear y seguir los labios. La ropa se dobla con las articulaciones.
- La versión 8.9 también añade recálculo automático de pesos de huesos y una selección de atlas más clara.

## 8.7–8.8 (septiembre de 2026) {#8788-september-2026}

- **8.8.0:** el panel de transferencia de animación funciona en aplicaciones anfitrionas Blender 5. La colocación de marcadores de dedos usa la forma de la mano. Otros cambios incluyen estiramiento IK hasta la piel, una opción Preserve Volume y una corrección de la vinculación de Delta Mush.
- **8.7.0:** esta versión añade un rig de control integrado, detección de articulaciones mediante el trazado de extremidades, transferencia de animación con coincidencia de dirección y huesos de torsión.

## 8.5–8.6 (julio de 2026) {#8586-july-2026}

- **8.6.1–8.6.3:** Material Atlas añade diagnósticos de teselas tras el horneado y una mejor partición de materiales mixtos. Comprueba la transparencia de MToon frente al alfa real de la textura y conserva esa transparencia al crear el atlas.
- **8.5.5–8.5.10:** los materiales VRM / MToon respetan el modo alfa. El alfa funciona en aplicaciones anfitrionas Blender 5. Otros cambios evitan una emisión excesiva y añaden diagnósticos magenta y nombres seguros para el atlas.
- **8.5.4:** las asignaciones humanoides se cargan correctamente. Esta versión también añade orientación de Naming Prep.
- **8.5.2–8.5.3:** estas versiones añaden importación de descargas de VRoid (.zip) y una tarjeta de transferencia de proyectos de VRoid.
- **8.5.1:** la exportación FBX conserva las blend shapes.

## Versiones anteriores {#earlier-versions}

**8.5.0:** después del horneado, Smart Combine convierte `atlas_uv` en UV0 de exportación de forma predeterminada. A menos que **Keep Source UV Maps** esté activado en los ajustes Advanced, elimina el mapa UV de origen anterior al atlas de la malla del atlas generada. La compilación abierta de Blender comparte ahora los controles derivados de CATS / Material Combiner / UVToolkit. Los sistemas de rigging de producción, control, transferencia de animación/exportación y versiones exclusivas de B4Artists siguen siendo exclusivos de B4Artists.

8.5.0 también actualiza la exportación y la validación. Las exportaciones de VRChat, VRM, MMD y Unreal tienen ahora controles de carpeta y nombre de archivo en los paneles de BoneCraft. Los ajustes de exportación ya no dependen solo de los valores predeterminados del explorador de archivos de Blender. Las exportaciones FBX de VRChat/Unity y Unreal activan **Embed Textures** de forma predeterminada para simplificar la importación de materiales. A menos que **Helper Meshes** esté activado, la exportación a VRChat excluye del FBX las mallas auxiliares y las formas de controles. El panel VRM añade **Lint Now** y **Fix Humanoid Map**. Fix Humanoid Map repara las asignaciones desactualizadas de alias humanoides antes de exportar, sin cambiar los nombres de los huesos.

**8.4.5:** durante el horneado, Smart Combine hace que las texturas de origen muestreen las UV conservadas anteriores al atlas. Valida la malla del atlas generada antes de ocultar los originales. Restablece todas las caras del atlas a la ranura final de material del atlas. Esto evita secciones grises o desordenadas en túnicas y ropa.

**8.4.4:** Material Atlas Combiner añade controles de inspección previos al horneado para lograr paridad de calidad. Incluyen diagnósticos de sombreadores/materiales, etiquetas de función de las texturas, marcadores de fuentes duplicadas/compartidas, ajustes de tamaño por material y preajustes de empaquetado. Los horneados de salida opcionales abarcan Normal/Emission/Roughness. La comprobación previa bloquea el empaquetado de canales Metallic/ORM hasta que se verifique esa ruta.

**8.4.3:** Material Atlas Combiner añade métodos seleccionables de empaquetado UV al flujo existente. Las opciones incluyen Smart Pack, Grid Pack, Seeded Variation, Oriented Pack, Fit 0-1 Bounds, Advanced Variation y Rotation Step. El informe de depuración y el registro de horneado documentan los detalles del método UV.

**8.4.2:** durante el horneado, Material Atlas Combiner usa como destino las UV del atlas generado. Los nodos de textura de origen copiados leen explícitamente las UV anteriores al atlas. Esto corrige los errores del atlas de túnicas y ropa causados por el muestreo de distintos mapas UV por las texturas de origen y el atlas horneado. Las filas seleccionables de materiales y texturas de 8.4.1 siguen disponibles.

**7.1.3 (limpieza de etiquetas de preferencias):** dos interruptores de preferencias del complemento tienen nuevas etiquetas que coinciden con sus pestañas de la barra lateral. «VRChat Avatar Tools» pasa a ser **CATS**, como la pestaña CATS de la barra lateral. «Task Board & Sidebar» pasa a ser **Rig Builder**, como la pestaña Rig Builder de la barra lateral. Solo cambiaron las etiquetas de los interruptores en Edit > Preferences > Add-ons > BoneCraft. No se eliminó ninguna herramienta.

**7.1.1:** BoneCraft añade la suite CATS completa para limpiar, optimizar y configurar avatares de VRChat. CATS tiene su propia pestaña en la barra lateral. Su flujo guía el orden de las operaciones.

Siguiente: [Tutorial: Crescent Rose con Mechanisms](12-crescent-rose.md)
