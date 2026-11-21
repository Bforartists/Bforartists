# Primeros pasos {#getting-started}

[← Índice](index.md)

## ¿Qué es BoneCraft? {#what-is-bonecraft}

BoneCraft es un complemento para Bforartists. Crea rigs de personajes y accesorios y prepara avatares 3D para VRChat, VRoid / VRM y MMD. Sus paneles automatizan la creación de rigs, la pintura de pesos, los nombres de huesos, la sincronización labial, el seguimiento ocular y la exportación.

**Lo que BoneCraft no puede hacer:**

- No puede modelar ni esculpir la forma del cuerpo de tu avatar
- No puede crear texturas ni materiales desde cero
- No puede subir directamente a VRChat (sigues necesitando VRChat Creator Companion / SDK)

---

## BoneCraft y BoneForge {#bonecraft-and-boneforge}

BoneCraft solo funciona en Bforartists, un fork de Blender. BoneForge es un complemento independiente para Blender estándar con menos herramientas. Instala solo uno de estos complementos. En Blender estándar, BoneCraft muestra un aviso y un botón para conseguir Bforartists. No carga sus herramientas.

BoneForge 9.0.0 y posteriores están dirigidos a Blender estándar. BoneCraft es el complemento independiente para Bforartists. Ambos tienen Auto-Rig Wizard, Quick Rig, Mannequin y las herramientas compartidas CATS/Material Atlas. BoneCraft también incluye Mechanisms, Control Picker y sus herramientas de rigs de control de producción, detección de articulaciones y exportación por perfiles. Una ubicación similar no añade esas herramientas a BoneForge.

## Inicio rápido de la compilación suministrada {#supplied-build-quick-start}

La compilación original suministrada de Bforartists incluye BoneCraft 9.2.18. La nueva versión preliminar local incluye la candidata 9.2.19. Ambas activan BoneCraft mediante los ajustes de fábrica. En estas compilaciones no instalas un ZIP ni activas BoneCraft manualmente.

1. Abre la compilación suministrada de Bforartists.
2. Pulsa **T** para mostrar la Tool Shelf izquierda.
3. Selecciona **BoneCraft** o **Rig Builder**.
4. Pulsa **N** para mostrar la barra lateral derecha.
5. Selecciona **CATS** para las herramientas de avatar e **Import / Export**.

Usa las mismas rutas de interfaz y ajustes del manual. Los paquetes de herramientas y dependencias opcionales conservan sus requisitos. Los rigs iniciales de Rigify y los puentes VRM/MMD siguen necesitando sus dependencias indicadas.

Estas instrucciones describen la versión preliminar de la contribución local. El paquete oficial Bforartists 5.2.3 no incluye este conjunto. Consulta la [propuesta de contribución](https://github.com/Bforartists/Bforartists/pull/7067) para conocer el historial de revisión.

## Instalar BoneCraft {#installing-bonecraft}

Usa esta sección para el ZIP independiente del Toolkit. Si usas una compilación suministrada, puedes empezar con las pestañas existentes indicadas arriba.

El ZIP público enlazado es 9.2.18. Usa la versión preliminar local para las correcciones de la candidata 9.2.19 hasta su publicación.

**Lo que necesitas:**

- Bforartists (BoneCraft está probado en Bforartists 5.2)
- El archivo independiente [BoneCraft-BFA-9.2.18.zip](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/bonecraft-v9.2.18/BoneCraft-BFA-9.2.18.zip)

**Pasos:**

Para una actualización:

1. Guarda tu trabajo.

2. Desactiva el complemento independiente BoneCraft anterior.

3. Elimina el complemento independiente BoneCraft anterior.

4. Reinicia Bforartists antes de instalar el nuevo ZIP.

Para una primera instalación, empieza aquí:

1. Abre Bforartists.
2. Abre **Edit** → **Preferences** → **Add-ons**.
3. Selecciona **Install from Disk…**.

4. Selecciona el archivo `.zip` de BoneCraft.

5. Activa la casilla junto a BoneCraft.
6. Confirma que Preferences indica **9.2.18** para el ZIP publicado enlazado.

7. Despliega la entrada de BoneCraft para ver **Language**, **Tabs**, **Shelf Width**, **Show Helpers** y **Tools**.

Estos pasos instalan el ZIP independiente del Toolkit. Usa el inicio rápido de la compilación suministrada si tu compilación ya incluye BoneCraft. Evita activar copias independientes e integradas duplicadas.

**Deberías ver:** las pestañas BoneCraft y Rig Builder en la Tool Shelf izquierda (pulsa **T**) y CATS en la barra lateral derecha (pulsa **N**).

## Dónde está cada cosa {#where-things-are}

Cada pestaña contiene un grupo de trabajo. Setup Rigging, Skin, Review, Avatar Tools y Facial son secciones desplegables dentro de las pestañas. Las rutas siguientes usan las etiquetas inglesas de la interfaz. Las etiquetas traducidas dependen de la preferencia Language.

| Pestaña | Ubicación predeterminada | Secciones |
| --- | --- | --- |
| Rig Builder | Tool Shelf izquierda (T) | Auto-Rig Wizard, Quick Rig - premade armatures, Mannequin |
| BoneCraft | Tool Shelf izquierda (T) | Overview, Setup Rigging, Skin, Mechanisms, Review |
| CATS | Barra lateral derecha (N) | CATS, Avatar Tools, VRChat Tools, Import / Export |

Descripción de imagen del original en inglés (imagen omitida): BoneCraft está seleccionado en la Tool Shelf izquierda y CATS en la barra lateral derecha. Pulsa T o N para mostrar esos lados.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. BoneCraft está seleccionado en la Tool Shelf izquierda y CATS en la barra lateral derecha. Pulsa T o N para mostrar esos lados.*

| Herramienta | Abre esta ruta |
| --- | --- |
| Bone Merge | BoneCraft → Setup Rigging → Bone Merge |
| Delta Mush / Proximity Wrap | BoneCraft → Skin → Delta Mush / Proximity Wrap |
| Viseme Library / Lip Sync | CATS → Avatar Tools → Viseme Library → Lip Sync |
| VRChat Viseme Mapping / Face Tracking | CATS → VRChat Tools → Facial |
| Humanoid / Hair | CATS → Avatar Tools → Set Up Humanoid Bones / Add Hair Physics |
| VRChat export | CATS → Import / Export → Game Engine Export → Unity / VRChat |
| Unreal export and Bone Names | CATS → Import / Export → Game Engine Export → Unreal Engine 5 |
| Validated profile export | CATS → Import / Export → Game Export → Export (Profile) |
| Material Atlas | CATS → CATS → Material Atlas → Analyze Materials / Refresh Analysis → Bake Checked Sources |
| VRM / MMD / I/O Hub | CATS → Import / Export → VRM / VRoid, MMD / PMX, Game Engine Export |
| Performance / Clothing / Naming | CATS → VRChat Tools → Check Performance / Attach Clothing / VRChat Naming Extras |

Para los controles del rig y de la biblioteca de visemas, selecciona un esqueleto. Para Delta Mush y Proximity Wrap, selecciona una malla en Modo Objeto. Lip Sync requiere un esqueleto en Modo Pose. Despliega el triángulo de la sección para mostrar sus botones. Los desplegables Options contienen ajustes opcionales. Si una herramienta se ejecuta inmediatamente, ajústala en Adjust Last Operation antes de otra operación.

Los tres flujos faciales tienen funciones diferentes. La generación de visemas de CATS crea claves de forma de la boca. Viseme Library / Lip Sync guarda poses y genera claves de animación. Facial asigna claves de forma existentes para VRChat o configura seguimiento facial.

Los controles de empaquetado UV están en **CATS → CATS → Material Atlas → Advanced Options → UV Packing**. Las instrucciones anteriores llaman a este desplegable Override Inherited Settings. BoneCraft proporciona utilidades UV compartidas para atlas, no el complemento independiente UVToolkit completo.

**Starter Rigs:**

1. Activa **Starter Rigs** en el menú de catálogos de la estantería de recursos inferior.

2. Si hace falta, selecciona **All** las bibliotecas.

La versión 9.2.5 eliminó los antiguos controles superiores izquierdos de Starter Rigs. **Add → Armature → Starter Rig Catalog** permite ajustar y generar con comprobaciones de dependencias.

**Mover una pestaña:**

1. Abre **Edit** → **Preferences** → **Add-ons** → BoneCraft → **Tabs**.

2. Selecciona **Left** o **Right** para la pestaña.

Cada pestaña tiene también un interruptor de visibilidad. Los cambios se aplican inmediatamente. Cuando una pestaña está oculta, sus botones Left y Right se vuelven grises, pero siguen funcionando.

**Editor de propiedades:** **Scene Properties**, en Preferences → Tabs, empieza activado. Muestra Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools e Import / Export en la pestaña Scene del editor Properties.

Selecciona **Show** para ocultar o mostrar estas secciones. El azul indica que son visibles. Este interruptor no cambia las pestañas de la vista ni la pestaña de datos Armature.

Con un esqueleto seleccionado, sus herramientas de BoneCraft también aparecen en la pestaña de datos Armature. Estas herramientas no siguen los interruptores de visibilidad. Rig Builder, Mechanisms y las secciones CATS usan Scene.

Para quitar una herramienta de todas las ubicaciones, desactiva su paquete en **Tools**. También puedes desactivar el complemento.

**Shelf Width:** Widen Narrow Shelves empieza activado. Ensancha una vez las estanterías que contienen pestañas de BoneCraft si su anchura es inferior al mínimo Left o Right. Con una escala de interfaz 1×, los valores predeterminados son 240 píxeles para Left y 260 para Right. Si después arrastras una estantería para estrecharla, conserva la anchura elegida. Para controlar las anchuras manualmente, desactiva el interruptor. Sus campos de anchura quedan inactivos.

Descripción de imagen del original en inglés (imagen omitida): Tabs sitúa BoneCraft y Rig Builder a la izquierda y CATS a la derecha. Debajo están Shelf Width y Show Helpers.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Tabs sitúa BoneCraft y Rig Builder a la izquierda y CATS a la derecha. Debajo están Shelf Width y Show Helpers.*

**Menús y pestañas integradas de Tool Shelf:** también puedes acceder a las herramientas desde los menús de cabecera de la Vista 3D:

| Ubicación | Herramientas |
| --- | --- |
| Add → Armature | Quick Rig, Auto-Rig Wizard, Mannequin for Active Rig |
| Pose → BoneCraft (Pose Mode) | Herramientas de pose, selector, colecciones de huesos, configuración y comprobaciones del rig |
| Weights → BoneCraft (Weight Paint mode) | Rellenar, reflejar y normalizar pesos |
| Object → Mechanisms (Object Mode) | Añadir piezas, articulaciones y vínculos; probar movimiento |
| Tool Shelf → Pose or Weights → BoneCraft | Botones de operaciones habituales de pose o pesos |

Los botones de las estanterías Pose y Weights muestran texto cuando hay anchura suficiente. Una estantería estrecha muestra una cuadrícula de iconos. Mantén el puntero sobre un icono para leer su descripción. Estas ubicaciones usan las mismas herramientas que las pestañas de BoneCraft. Solo están disponibles los paquetes activados.

**Herramientas de la vista:** Place Rig Markers coloca el siguiente marcador de Auto-Rig Wizard al hacer clic en la malla. Build Mechanism inicia una articulación o vínculo guiado al hacer clic en una pieza. Consulta [Rig Builder](06-rig-builder.md#auto-rig-wizard) y [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each) para la configuración y los controles.

**Ejecutar primero, ajustar después:** Quick Rig, Fit Dropped Rig, Weight Mirror, Weight Transfer, Flood to Custom, Ribbon, Spline IK y Delta Mush se ejecutan inmediatamente.

1. Selecciona la herramienta.

2. Ajusta inmediatamente sus opciones en el panel Adjust Last Operation de la vista.

3. Termina los ajustes antes de otra operación.

Otros paneles contienen ajustes opcionales en un desplegable bajo los botones de acción. Para usarlos, despliega esa sección. Si un panel necesita otra selección, puede permanecer visible y explicar qué seleccionar.

**Show Helpers:** BoneCraft explica las secciones con líneas breves de «qué / cuándo» y notas «How this works». Para ocultarlas, desactiva **Show Helpers** en las preferencias del complemento. En Avatar Tools, **Compact Mode** controla el mismo interruptor.

**Language:** el ajuste **Language** de las preferencias del complemento cambia los paneles propios de BoneCraft a English, 日本語, 한국어, 中文, Français, Português o Español.

Descripción de imagen del original en inglés (imagen omitida): la versión preliminar local indica BoneCraft 9.2.19 y English como Language.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. La versión preliminar local indica BoneCraft 9.2.19 y English como Language.*

**Revisar primero la limpieza:**

1. Examina las opciones de Fix Model.

2. Selecciona las operaciones que necesita tu avatar.

3. Guarda un punto de control del archivo antes de los cambios.

4. Después de la operación, examina el resultado.

Pipeline Status y Operation Ledger registran el progreso. Consulta [El pipeline de CATS](04-cats-pipeline.md).

**Panel rápido:** pulsa **Ctrl+Shift+R** en la Vista 3D para abrir el panel de rig de BoneCraft bajo el cursor.

---

## ¿Por dónde empiezo? {#where-should-i-start}

Selecciona la guía adecuada a tu tarea:

> **Crear el rig de un modelo FBX, OBJ o Blender nuevo para VRChat.**
> → Ve a [Guía 1: llevar tu primer avatar a VRChat](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)

> **Preparar un avatar VRM exportado desde VRoid Studio.**
> → Ve a [Guía 2: llevar un avatar de VRoid a VRChat](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)

> **Preparar un modelo MMD (archivo PMX) para VRChat.**
> → Ve a [Guía 3: llevar un avatar MMD a VRChat](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)

> **Corregir nombres de huesos que impiden subir un avatar con rig.**
> → Ve a [Guía 4: corregir los nombres de huesos de tu avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

> **Preparar la sincronización labial, el seguimiento ocular y la malla de un avatar con rig para VRChat.**
> → Ve a [Guía 13: preparar tu avatar para VRChat con CATS](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)

> **Resolver un problema concreto.**
> → Ve al [Índice de soluciones rápidas](10-reference.md#quick-fix-index)

Siguiente: [Guías 1–7](02-guides-a.md)
