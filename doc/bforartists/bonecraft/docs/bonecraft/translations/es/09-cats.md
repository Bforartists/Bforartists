# Herramientas de CATS {#cats-tools}

[← Índice](index.md)

Las herramientas CATS están en **CATS → CATS**, en la barra lateral derecha. Pulsa **N** para mostrarla.

También aparecen en **Properties → Scene** si Preferences → Tabs → Scene Properties → Show está activado. Los interruptores de CATS en la vista y Scene Properties controlan sus copias por separado.

Siguen [El pipeline de CATS](04-cats-pipeline.md). Selecciona arriba el esqueleto que procesar.

En 9.1, varios paneles tienen ajustes opcionales en un desplegable bajo sus botones de acción. Las entradas necesarias permanecen encima: interruptores de limpieza Fix Model, idioma fuente de Translate Bone Names, formas de boca y huesos de ojos.

Las herramientas de huesos con Adjust Last Operation se ejecutan inmediatamente. Ajusta allí sus opciones después. Mantén el puntero sobre botones y opciones para leer sus descripciones.

---

## Fix Model {#fix-model}

**Fase del pipeline:** 1 (revisión de limpieza recomendada)

**Qué hace:** ejecuta las operaciones de limpieza activadas en la malla seleccionada. Un avatar limpio puede no necesitar esos cambios.

**Opciones (cada una puede desactivarse):**

- Aplicar modificadores
- Remove doubles — unir vértices duplicados en la misma posición
- Recalcular normales — corregir superficies del revés
- Eliminar geometría suelta — caras no conectadas al cuerpo
- Eliminar grupos de vértices vacíos
- Eliminar huesos de peso cero — huesos que no mueven ningún vértice
- Eliminar restricciones y cuerpos rígidos que VRChat no puede usar

1. Revisa las opciones de limpieza.

2. Activa solo las operaciones que necesita tu avatar.

3. Guarda un punto de control del archivo.

4. Selecciona **Fix Model** para ejecutar las operaciones activadas en la malla seleccionada en una pasada.

5. Examina el resultado antes de continuar.

Descripción de imagen del original en inglés (imagen omitida): opciones y acción Fix Model. Revísalas antes de la primera fase del pipeline.

*Panel emergente nativo, BoneCraft 9.2.18. Opciones y acción Fix Model. Revísalas antes de la primera fase del pipeline.*

---

## Translate Bone Names {#translate-bone-names}

**Qué hace:** traduce nombres de huesos del esqueleto a nombres ingleses VRChat. Funciona sin conexión mediante un diccionario integrado de nombres conocidos.

**Idiomas admitidos:** japonés (日本語, el más común, de MMD y muchos modelos comunitarios), chino (中文), coreano (한국어), portugués (Português), español (Español) y francés (Français).

**Controles principales:**

1. Selecciona **Language** de los nombres fuente.

2. Selecciona **Translate Bone Names**.

Language identifica el idioma de los nombres de huesos del modelo, no el de la interfaz. Para un modelo MMD japonés, selecciona japonés independientemente del idioma de Bforartists.

Descripción de imagen del original en inglés (imagen omitida): elige el idioma fuente de nombres antes de Translate Bone Names. El ejemplo no ha detectado nombres coincidentes.

*Panel emergente nativo, BoneCraft 9.2.18. Elige el idioma fuente de nombres antes de Translate Bone Names. El ejemplo no ha detectado nombres coincidentes.*

---

## Join Meshes {#join-meshes}

**Qué hace:** combina objetos de malla del avatar en una malla. VRChat funciona mejor con una malla por avatar. Si las fuentes tienen claves de forma distintas, CATS rellena las ausentes con formas neutras. La malla unida tiene un conjunto coherente.

**Controles principales:** lista de mallas, botón de actualización y **Join Meshes**.

**Cuándo usarla:** después de adjuntar ropa y accesorios y asignarles pesos.

1. Examina las mallas fuente.

2. Selecciona la limpieza que necesiten antes de unirlas.

3. Guarda un punto de control del archivo.

4. Si hay que actualizar la lista, pulsa el botón a su lado.

5. Selecciona **Join Meshes**.

6. Examina la malla unida, las claves de forma y los pesos.

Descripción de imagen del original en inglés (imagen omitida): después de Refresh Mesh List, la lista contiene una malla marcada con seis polígonos. Revísala antes de Join Meshes.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Después de Refresh Mesh List, la lista contiene una malla marcada con seis polígonos. Revísala antes de Join Meshes.*

---

## Material Atlas Combiner {#material-atlas-combiner}

**Fase del pipeline:** 2 (opcional)

**Qué hace:** hornea varios materiales en una hoja de texturas (atlas). Menos materiales mejoran la clasificación de rendimiento VRChat.

**Ubicación:** **CATS → CATS → Material Atlas**. Divide el trabajo en **1. Choose Target**, **2. Choose Materials and Textures** y **3. Bake and Review**.

### Analizar y elegir fuentes {#analyze-and-choose-sources}

Descripción de imagen del original en inglés (imagen omitida): Material Atlas antes del análisis. Elige el destino, conserva una copia de seguridad y después usa Analyze Materials.

*Panel emergente nativo, BoneCraft 9.2.18. Material Atlas antes del análisis. Elige el destino, conserva una copia de seguridad y después usa Analyze Materials.*

**Target** ofrece **Active Avatar**, **Selected Meshes** y **Visible Scene**. Active Avatar usa las mallas hijas del esqueleto activo. Si no hay esqueleto activo, usa la malla activa. Visible Scene usa las mallas visibles. Para un conjunto concreto, elige Selected Meshes.

1. Guarda una copia del archivo.

2. Selecciona el alcance en **Target**.

3. Mantén **Preserve Backup Duplicate** activado.

4. Selecciona **Analyze Materials**.

5. Selecciona un grupo de atlas.

6. Para hornearlo, activa su casilla.

7. En **Materials to combine**, activa los materiales que incluir.

8. En **Texture images**, activa las imágenes que incluir.

9. Repite la revisión de fuentes para cada grupo activado.

**Analyze Materials** crea las listas de fuentes. Su etiqueta pasa a **Refresh Analysis** cuando existen grupos. Refresh reconstruye las listas y sus selecciones. Revísalas de nuevo tras actualizar.

Cada lista tiene **Select All** y **Deselect All**. Cambian las casillas **Include** de esa lista del grupo activo. No cambian la fila resaltada. Las listas de materiales y texturas son independientes. Los demás grupos conservan sus selecciones. Las texturas ausentes quedan sin marcar. La selección masiva no activa un grupo desactivado.

Las mismas acciones masivas están en **Object → Atlas Source Selection**. Usa Accept o Revert sobre una previsualización de atlas pendiente antes de cambiar su selección de fuentes.

Un grupo activado necesita al menos dos materiales marcados. El horneado omite grupos desactivados y de un solo material. Las ranuras excluidas y las referencias compartidas de materiales permanecen separadas. Excluir una imagen la omite del horneado; no excluye todo su material.

Los materiales transparentes y emisivos empiezan en grupos separados. Los grupos Alpha Blend empiezan desactivados para conservar el orden de dibujo. Actívalos si aceptas posibles cambios de ese orden.

**Source Details** empieza desactivado. Actívalo para examinar diagnóstico de mallas, avisos de claves de forma y UV, tamaños de materiales, funciones de texturas y grupos de fuentes duplicadas. **Override Size** de un material muestra la selección de tamaño. El tamaño personalizado usa **Width** y **Height**. Los materiales solo de color usan tamaño **Fallback**.

La lista de grupos ofrece **Resolution** y controles de añadir/eliminar. **Add Group** y **Remove Group** administran grupos. No hornean por sí mismos.

Descripción de imagen del original en inglés (imagen omitida): fuentes analizadas de dos mallas de ejemplo. Revisa las casillas de grupos, materiales e imágenes, incluido el aviso UV.

*Candidata BoneCraft 9.2.19. Compilación nativa de prueba Bforartists 5.2.3, Blender 5.4 Alpha. Fuentes analizadas de dos mallas de ejemplo. Revisa las casillas de grupos, materiales e imágenes, incluido el aviso UV.*

### Hornear y revisar {#bake-and-review}

1. Después de revisar las fuentes, selecciona **Bake Checked Sources**.

2. Lee el resumen previo.

3. Corrige los errores de fuentes o ajustes indicados.

4. Cuando los cambios previstos sean correctos, confirma el horneado.

5. Examina atlas, transparencia, claves de forma y canal UV exportado.

6. Si el resultado es correcto, selecciona **Accept — Delete Backup**.

Si necesitas el resultado original, selecciona **Revert — Restore Originals**. Accept elimina la copia de seguridad. Revert restaura objetos, materiales y visibilidad originales. También restablece los resultados de cantidad de materiales.

Descripción de imagen del original en inglés (imagen omitida): un grupo Opaque de 2048 píxeles horneado desde dos mallas de ejemplo. El panel sigue indicando de 2 a 2 materiales y clasificación Excellent. Examina el aviso UV antes de Accept o Revert.

*Candidata BoneCraft 9.2.19. Bforartists 5.2.3 oficial, Blender 5.3 Alpha. Un grupo Opaque de 2048 píxeles horneado desde dos mallas de ejemplo. El panel sigue indicando de 2 a 2 materiales y clasificación Excellent. Examina el aviso UV antes de Accept o Revert.*

**Preserve Backup Duplicate** empieza activado. Conserva un duplicado visible anterior al atlas para revisar y usar Revert. Desactivarlo elimina los originales después del atlas y no deja copia para Revert. Guarda un archivo separado antes de desactivarlo.

Usa Accept o Revert sobre la previsualización actual antes de otro análisis u horneado. Si cambia un objeto analizado, una ranura de material o una clasificación de render, la comprobación previa puede cancelar antes de crear una copia de seguridad.

Antes de volver a hornear:

1. Selecciona **Refresh Analysis**.

2. Revisa las selecciones reconstruidas.

**Smart Combine Materials** es el acceso automático inicial antes de que exista análisis. Con **Auto Analyze** activado, reconstruye el análisis antes de hornear. Usa **Bake Checked Sources** para hornear tus selecciones revisadas sin reanálisis automático. Las instrucciones antiguas llaman **Bake Atlas** a este operador.

**Si el horneado no puede empezar:** necesita Cycles. Si Bforartists indica que Cycles no está disponible, usa una compilación completa que lo incluya.

### Advanced Options {#advanced-options}

**Advanced Options** sustituye el nombre anterior Override Inherited Settings. Contiene controles opcionales de flujo, horneado, UV y salida.

| Ajuste | Uso |
| --- | --- |
| Auto Analyze | Reconstruye grupos para el acceso automático Smart Combine. |
| Debug Report / Copy Debug Report | Activa diagnóstico y copia el informe más reciente para resolver problemas. |
| Albedo (Color) | Paso obligatorio de horneado de color base. Déjalo activado. |
| Normal Map / Emission / Roughness | Pasos de salida separados opcionales. Examina los datos fuente admitidos y el resultado. |
| Metallic / Pack ORM Channels | La comprobación previa bloquea estas opciones en esta compilación. Déjalas desactivadas. |
| Packing Preset / Bake Padding / UV Margin | Determina relleno y separación de islas del atlas. |
| Pixel Art No-Bleed / Preserve Island Orientation | Controla el relleno y el tratamiento admitido de orientación de islas. |
| UV Method / UV Seed / Rotation Step | Elige empaquetado y variación. Semilla y rotación aparecen solo para métodos que las usan. |
| Keep Source UV Maps | Conserva las capas UV fuente en la malla de salida. Empieza desactivado. |
| Fallback Size | Tamaño asignado en el atlas a materiales de color sin imágenes. |
| Format Output | Elige PNG, TGA o EXR. EXR conserva emisión superior a 1.0. PNG y TGA la limitan. |
| Material Output Type / Surface Output | Elige tipo de render y sombreador de superficie del material generado. |
| Path Output | Carpeta de texturas de salida. |

Con **Keep Source UV Maps** desactivado, la malla final usa `atlas_uv` como UV0 para FBX, Unity y VRChat. Activarlo puede dejar `atlas_uv` en UV1. Comprueba el canal UV del motor si conservas mapas fuente. Las mallas de color sin UV creadas también reciben la capa UV generada del atlas.

### Conservación y límites {#preservation-and-limits}

El combinador conserva el tinte conectado de Principled, el mapeo de texturas y el alfa durante el horneado. Procesa fuentes ocultas en render mediante copias temporales de horneado. Las referencias de materiales excluidos siguen compartidas con otros objetos. Las posiciones geométricas, las claves de forma y el parentesco permanecen protegidos durante el montaje.

Los materiales VRM / MToon conservan su vía alternativa específica. La clasificación de transparencia considera el grafo alfa real y el alfa de textura. DITHERED por sí solo no clasifica un material como transparente. Pueden aparecer zonas magenta tras hornear. Revísalas antes de aceptar.

Las reparaciones documentadas tienen comprobaciones en el host con ejemplos generados. No certifican todos los avatares de producción ni grafos de sombreado. El explorador visible de archivos, la distribución de ventanas reales y deshacer/rehacer interactivos conservan sus límites de prueba registrados. Consulta el [registro histórico de reparación](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md) y la [revisión de interfaz 9.2.15](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md).

**Créditos de procedencia:** este flujo continúa la integración CATS y reconoce al Cats Blender Plugin original. La procedencia de Material Combiner reconoce Grim-es/material-combiner-addon. La inspiración UV viene de UV Toolkit de Alexander Belyakov y el repositorio archivado oRazeD/UVToolkit. BoneCraft implementa sus propias utilidades UV de atlas. No incluye código fuente UVToolkit.

---

## Visemes {#visemes}

**Fase del pipeline:** 3

**Qué hace:** crea los 15 visemas VRChat a partir de tres formas base de boca.

**Antes de generar:** **A Shape**, **O Shape** y **CH Shape** necesitan una fuente asignada. Cada campo debe nombrar una clave de forma de boca existente.

**Selección manual de fuentes:**

1. Selecciona la clave fuente en **A Shape**.

2. Selecciona la clave fuente en **O Shape**.

3. Selecciona la clave fuente en **CH Shape**.

**Alternativa automática:** selecciona **Auto-Detect**.

**Después de cualquiera de las dos rutas:**

1. Comprueba que los tres campos nombran claves existentes.

2. Si hace falta, despliega Options bajo los botones.

3. Si hace falta, cambia si se sobrescriben los visemas existentes.

4. Selecciona **Generate Visemes**.

Consulta [Guía 13, fase 2](03-guides-b.md#phase-2--viseme-generation).

Descripción de imagen del original en inglés (imagen omitida): CATS Visemes: selecciona las formas fuente A, O y CH o usa Auto-Detect antes de Generate Visemes.

*Panel emergente nativo, BoneCraft 9.2.18. CATS Visemes: selecciona las formas fuente A, O y CH o usa Auto-Detect antes de Generate Visemes.*

---

## Eye Tracking {#eye-tracking}

**Fase del pipeline:** 4 (después de Fix Model)

Auto-Detect busca nombres comunes de huesos de ojos. No usa geometría de malla ni posiciones de huesos.

1. Comprueba **Left Eye** y **Right Eye**.

2. Si falta una asignación, selecciona manualmente ese hueso.

Si renombras los huesos:

1. Ejecuta de nuevo la detección.

2. Revisa ambas asignaciones.

Si el movimiento ocular es incorrecto, examina orientación de huesos, restricciones y avatar exportado.

**Qué hace:** encuentra los huesos de ojos y los nombra `LeftEye` y `RightEye`, como requiere VRChat. Crea restricciones de rotación para el movimiento ocular VRChat.

**Controles principales:**

- **Auto-Detect** — busca nombres comunes de huesos de ojo izquierdo y derecho
- **Left Eye** y **Right Eye** — huesos de ojos si los eliges manualmente
- **Up Limit**, **Down Limit** y **Side Limit** — cuánto pueden girar los ojos, en grados
- **Create Eye Tracking** — renombra huesos y crea restricciones

Descripción de imagen del original en inglés (imagen omitida): Eye Tracking antes de detectar huesos. Los límites del ejemplo son 30 grados arriba, 20 abajo y 30 a los lados.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Eye Tracking antes de detectar huesos. Los límites del ejemplo son 30 grados arriba, 20 abajo y 30 a los lados.*

---

## Pose & Shape Keys {#pose--shape-keys}

**Fase del pipeline:** 5 (opcional)

### Pose to Shape Key {#pose-to-shape-key}

El botón actual captura la **mezcla actual de claves de forma** de la malla seleccionada. No hornea deformación de huesos del esqueleto.

1. Cambia a Modo Objeto.

2. Selecciona la malla de destino.

3. Configura los valores de sus claves existentes para obtener la mezcla que capturar.

4. Selecciona **Pose to Shape Key**.

5. Introduce un nombre.

6. Confirma la operación.

7. Restablece los valores de las claves originales a 0.

8. Examina la nueva clave sola.

La herramienta asigna 1 a la nueva clave y deja las originales activadas. Conservar los valores originales activos vuelve a sumar su deformación.

### Guardar una pose deformada por huesos {#save-a-bone-deformed-pose}

Usa este flujo nativo para guardar deformación de huesos del esqueleto. El modificador debe conservar la topología de la malla.

**Save as Shape Key** conserva el modificador Armature. **Apply as Shape Key** lo elimina.

1. Coloca el esqueleto en una pose.

2. Guarda un punto de control del archivo.

3. Vuelve a Modo Objeto.

4. Selecciona la malla deformada.

5. Abre **Properties → Modifiers**.

6. Abre el menú desplegable del modificador Armature.

7. Selecciona **Save as Shape Key**.

8. Restablece la pose de huesos.

9. Restablece los valores de claves de forma originales.

10. Configura el valor de la nueva clave en 1.

11. Revisa la nueva clave sola.

Si la pose de huesos o la mezcla fuente siguen activas, suman deformación otra vez. Esta operación nativa no actualiza la marca Pose To Shape del pipeline BoneCraft.

Descripción de imagen del original en inglés (imagen omitida): el menú nativo del modificador Armature ofrece Save as Shape Key separado de Apply as Shape Key.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Menú nativo del modificador Armature antes de ejecutar. Save as Shape Key conserva el modificador; la imagen no muestra el resultado de una pose capturada.*

### Shape Key to Basis {#shape-key-to-basis}

Convierte la clave activa que no sea Basis en la nueva Basis. Ajusta las otras claves respecto a ella.

1. Guarda un punto de control del archivo antes de la operación.

2. Después, revisa las claves restantes.

Descripción de imagen del original en inglés (imagen omitida): Pose to Shape Key captura la mezcla actual. Shape Key to Basis convierte la clave activa en la nueva Basis.

*Panel emergente nativo, BoneCraft 9.2.18. Pose to Shape Key captura la mezcla actual. Shape Key to Basis convierte la clave activa en la nueva Basis.*

---

## Transforms & FBT {#transforms--fbt}

**Fase del pipeline:** 6 (última)

### Apply All Transforms {#apply-all-transforms}

Aplica posición, rotación y escala a malla y esqueleto, restableciendo los canales. Las herramientas anteriores siguen disponibles.

1. Guarda un punto de control antes de la operación.

2. Compara el avatar antes y después.

Si el tamaño cambia tras exportar, revisa transformaciones de malla y esqueleto y ajustes de escala de exportación e importación.

### Fix FBT {#fix-fbt}

Corrección de transformaciones para Full Body Tracking: mueve el hueso raíz al nivel del suelo.

### Remove FBT {#remove-fbt}

Elimina la corrección Fix FBT.

Descripción de imagen del original en inglés (imagen omitida): Apply All Transforms, Fix FBT y Remove FBT son las acciones finales del pipeline.

*Panel emergente nativo, BoneCraft 9.2.18. Apply All Transforms, Fix FBT y Remove FBT son las acciones finales del pipeline.*

---

## Bone Tools {#bone-tools}

- **Create Root Bone** — añade un hueso raíz (cuyo nombre se define en **Root Name**) al fondo de la jerarquía
- **Merge Bones** — combina con sus padres los huesos más cortos que **Merge Threshold**
- **Duplicate Bones** — duplica los huesos seleccionados

Descripción de imagen del original en inglés (imagen omitida): Create Root Bone, Merge Bones y Duplicate Bones. Ajusta nombres de raíz y umbrales después de la acción.

*Panel emergente nativo, BoneCraft 9.2.18. Create Root Bone, Merge Bones y Duplicate Bones. Ajusta nombres de raíz y umbrales después de la acción.*

---

## Armature Tools {#armature-tools}

**Qué hace:** combina un esqueleto con otro, por ejemplo el de una prenda con el del cuerpo.

**Controles principales:**

- **Base / Root** — esqueleto que se conserva (el resultado mantiene su nombre)
- **Incoming** — esqueleto que se integra en el base. Los huesos con el mismo nombre se combinan con el base.
- Naming Prep — empareja nombres de huesos de ambos rigs antes de combinar. Funciona en cualquier rig, incluidos los de fuentes distintas de Mixamo.
- Opciones de emparentado automático de huesos y unión posterior de mallas
- **Merge Incoming Into Base** — combina

Para Naming Prep:

1. Selecciona Mixamo Prefixed.

2. Selecciona **Normalize Merge Names**.

3. Selecciona Mixamo Stripped.

4. Selecciona **Normalize Merge Names** otra vez.

Ambos rigs terminan con los mismos nombres.

Para combinar por etapas y con previsualizaciones, usa Bone Merge (consulta [Rig Builder](06-rig-builder.md#bone-merge)).

Descripción de imagen del original en inglés (imagen omitida): elige esqueletos Base e Incoming, revisa Naming Prep y usa Merge Incoming Into Base.

*Panel emergente nativo, BoneCraft 9.2.18. Elige esqueletos Base e Incoming, revisa Naming Prep y usa Merge Incoming Into Base.*

---

## Mesh Tools {#mesh-tools}

- **Separate by Materials** — una malla por material
- **Separate by Loose Parts** — una malla por pieza conectada
- **Separate by Shape Keys** — separa las partes movidas por claves de forma

Descripción de imagen del original en inglés (imagen omitida): separar mallas por materiales, piezas sueltas o claves de forma.

*Panel emergente nativo, BoneCraft 9.2.18. Separar mallas por materiales, piezas sueltas o claves de forma.*

---

## Smart Automatic Weights {#smart-automatic-weights}

**Smart Automatic Weights** abre un diálogo con valores predeterminados inteligentes y una copia de seguridad oculta.

1. Comprueba la malla de destino y el esqueleto.

2. Para recalcular pesos desde el rig existente, selecciona Body.

3. Para transferirlos desde una malla fuente con pesos, selecciona Clothing.

**Advanced Recalculation** despliega una indicación de ubicación para **BoneCraft → Skin → Weight Tools**. No abre aquí los controles completos. Consulta [Herramientas de rig](05-rig-tools.md#automatic-bone-weight-recalculation).

Descripción de imagen del original en inglés (imagen omitida): Smart Automatic Weights abre su diálogo de configuración. Advanced Recalculation indica dónde están los controles completos de pesos.

*Panel emergente nativo, BoneCraft 9.2.18. Smart Automatic Weights abre su diálogo de configuración. Advanced Recalculation indica dónde están los controles completos de pesos.*

---

## Pipeline Status y Operation Ledger {#pipeline-status-and-operation-ledger}

Pipeline Status muestra cuáles de las seis fases están completas. Operation Ledger enumera cada operación CATS con hora y resultado: Changed, Clean o Failed. **Copy** copia el registro al portapapeles. **Clear** lo vacía. Consulta [El pipeline de CATS](04-cats-pipeline.md).

Siguiente: [Soluciones rápidas y glosario](10-reference.md)
