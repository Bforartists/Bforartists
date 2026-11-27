# Herramientas de rig {#rig-tools}

[← Índice](index.md)

Este capítulo explica las herramientas de rigging, animación y pesos de BoneCraft. Úsalo para detalles de funciones o situaciones que no cubren las guías.

Cada entrada explica el propósito, los usos, los controles principales y la ubicación de la herramienta. La línea «Dónde encontrarla» indica el modo necesario. Los controles de rig necesitan Pose Mode. Weight Mirror y Weight Transfer necesitan el modo Weight Paint. Delta Mush necesita Object Mode. Si una herramienta no puede ejecutarse, algunas secciones permanecen visibles con un mensaje sobre la selección.

Desde 9.1, muchas herramientas se ejecutan inmediatamente y muestran sus opciones en Adjust Last Operation. Cámbialas justo después del clic, antes de ejecutar otra operación. Las operaciones habituales tienen accesos en Pose → BoneCraft y Weights → BoneCraft. Las pestañas Pose y Weights de Tool Shelf de Bforartists también tienen paneles de botones de BoneCraft. [Primeros pasos](01-start.md#where-things-are) enumera estos accesos.

Las imágenes muestran rigs y ajustes de ejemplo. Sigue la ruta de cada herramienta para abrir sus controles.

Para exportar a motores, usa [Herramientas VRChat: Game Engine Export](08-vrchat.md#game-engine-export). Los preajustes **Bone Names** cambian las copias de exportación. Tienen una función distinta de las herramientas que renombran el rig de trabajo.

---

## Herramientas de interfaz del rig {#rig-ui-tools}

Estas herramientas controlan la visibilidad y organización de huesos y el acceso rápido al trabajar con esqueletos.

---

### Bone Collections {#bone-collections}

**Qué hace:** muestra las colecciones de huesos del esqueleto como filas. Haz clic en el nombre de una colección para seleccionar sus huesos. El ojo muestra u oculta la colección.

> Una colección de huesos es un grupo con nombre, por ejemplo «IK Controls», «Face Bones» y «Deform Bones». Ocultarla oculta esos huesos en la vista para concentrarte en una parte del rig.

**Controles principales:**

- Cada fila: color de acento, **Toggle Collection Visibility** (ojo), nombre de la colección, **Solo Collection** y **Rename Collection Display**. El nombre selecciona sus huesos. **Rename Collection Display** asigna un nombre de visualización personalizado a la fila. Mantén el puntero sobre un botón sin texto para identificarlo por su descripción
- **Show All Collections** y **Hide All Collections** (ojos abierto y cerrado sobre la lista) — todas a la vez
- Sections — agrupa varias colecciones bajo una cabecera desplegable

**Dónde encontrarla:** pestaña BoneCraft → Review → Collections

Descripción de imagen del original en inglés (imagen omitida): colecciones de huesos y sus controles de visibilidad, selección, Solo y nombre de visualización.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Colecciones de huesos y sus controles de visibilidad, selección, Solo y nombre de visualización.*

---

### Visibility Bookmarks {#visibility-bookmarks}

**Qué hace:** guarda qué colecciones de huesos son visibles para cambiar de vista guardada de una vez.

**Ejemplo:** «Face Only» puede guardar solo los huesos faciales para trabajar expresiones. «Full Rig» puede guardar todos los huesos para pintar pesos. Un clic cambia entre vistas guardadas.

**Controles principales:** cada ranura es una fila.

- Nombre del marcador — haz clic para aplicar la vista guardada
- **Save Bookmark** — guarda la visibilidad actual en la ranura. Mantén el puntero sobre su icono para leer la descripción
- Muestra de color — identifica el marcador mediante color
- **Clear Bookmark** y **Remove Bookmark** (iconos de cierre) — vacía la ranura o elimina una añadida
- **Add Bookmark** — añade una ranura

**Marcadores predeterminados:** FK Arms, IK Body, Face Only, Full Rig

**Dónde encontrarla:** pestaña BoneCraft → Review → Collections → Visibility Bookmarks

Descripción de imagen del original en inglés (imagen omitida): Visibility Bookmarks con una vista Full Rig guardada y tres ranuras disponibles.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Visibility Bookmarks con una vista Full Rig guardada y tres ranuras disponibles.*

---

### Hotkey Quick Panel {#hotkey-quick-panel}

**Qué hace:** abre el panel de rig de BoneCraft (colecciones y marcadores) como un emergente donde esté el cursor.

**Uso:**

1. En la Vista 3D, pulsa **Ctrl+Shift+R**.
2. Para cerrar el emergente, haz clic fuera.

**Dónde encontrarla:** atajo **Ctrl+Shift+R** en la Vista 3D (no tiene panel propio)

El panel rápido usa los [controles de marcadores descritos arriba](#visibility-bookmarks).

---

## Herramientas de animación {#animation-tools}

---

### Pose Library {#pose-library}

**Qué hace:** guarda poses con nombre y miniaturas que puedes aplicar al rig con un clic.

**Controles principales:**

- **Save** — guarda las posiciones actuales de huesos como una pose con nombre y miniatura de la vista
- **Apply** — coloca los huesos en la pose guardada
- **Blend** — aplica la pose con intensidad parcial, mezclada con la posición actual
- **Mirror** — aplica la pose reflejada de izquierda a derecha
- **Delete**, **Rename** y **Category** — administran la lista. **Filter** muestra una categoría
- **Export** e **Import** — guardan o cargan un archivo `.bfpose`

Blend se aplica inmediatamente. Después de pulsarlo, configura la intensidad de mezcla en Adjust Last Operation.

**Dónde encontrarla:** pestaña BoneCraft → Review → Pose Library

Descripción de imagen del original en inglés (imagen omitida): una pose de ejemplo guardada muestra Apply, Mirror, Blend y los controles de biblioteca.

*Panel emergente nativo, BoneCraft 9.2.18. Una pose de ejemplo guardada muestra Apply, Mirror, Blend y los controles de biblioteca.*

---

### Control Picker {#control-picker}

**Qué hace:** un mapa interactivo de controles del rig. Haz clic en una forma para seleccionar su hueso. El selector resalta los controles seleccionados.

**Controles principales:**

- **Generate Picker** — crea la distribución a partir del rig
- **Edit Layout** — edita la distribución. Cada fila de control tiene iconos **Move Picker Control**, **Resize Picker Control** y **Relabel Picker Control**. **Snap** alinea los controles a una cuadrícula. **Rebuild Layout** vuelve a crear la distribución
- **Mirror Selection** — selecciona los controles reflejados
- **Pop-up Picker** — abre el selector en una ventana flotante, que también tiene **Add Selection Set**

**Dónde encontrarla:** pestaña BoneCraft → Review → Control Picker

Descripción de imagen del original en inglés (imagen omitida): Control Picker generado con controles de ejemplo, edición de distribución, selección reflejada y apertura del selector emergente.

*Panel emergente nativo, BoneCraft 9.2.18. Control Picker generado con controles de ejemplo, edición de distribución, selección reflejada y apertura del selector emergente.*

---

### Control Layer (IK/FK) {#control-layer-ikfk}

Para una comparación práctica escrita, sigue [Probar pesos y usar IK/FK](06-rig-builder.md#part-c-test-weights-and-use-ikfk).

**Qué hace:** controla las extremidades de un rig creado por **Build Control Rig**. Cambia una extremidad entre IK y FK sin saltos. También convierte animación IK a FK, o FK a IK, en un rango de fotogramas.

**Controles principales:**

- **IK** y **FK** — cambian el modo y ajustan los controles nuevos a la posición actual. El codo o la rodilla no salta
- **Bake IK** y **Bake FK** — convierten la animación del rango de fotogramas a IK o FK
- **Pole Follow**, **Pin** y **Lock-Free**, y **Global Rig Scale**, que mantiene los bloqueos protegidos

**Dónde encontrarla:** pestaña BoneCraft → Review → Control Layer (con un rig creado por **Build Control Rig** seleccionado; consulta [Rig Builder](06-rig-builder.md))

Descripción de imagen del original en inglés (imagen omitida): Control Layer muestra interruptores IK/FK de extremidades, acciones de horneado y ajustes del rig.

*Captura histórica del taller. Control Layer muestra interruptores IK/FK de extremidades, acciones de horneado y ajustes del rig.*

---

### Rigify Tools {#rigify-tools}

**Qué hace:** detecta un rig de control Rigify y conecta el panel de colecciones, los marcadores y los deslizadores de propiedades de BoneCraft con los controles estándar de Rigify.

> Rigify es el sistema integrado de Bforartists para generar rigs listos para animar. Si creaste tu rig con Rigify, conecta la interfaz de BoneCraft con sus controles IK/FK.

**Controles principales:**

- **Auto-Enhance** — configura los paneles de BoneCraft para el rig Rigify seleccionado
- **Re-run Enhancement** — los reconstruye desde cero
- **Enable Rigify** está en Quick Rig. Su desplegable Troubleshooting contiene **Generate Control Rig (active metarig)** (consulta [Rig Builder](06-rig-builder.md))
- Rigify Properties — deslizadores de IK/FK, estiramiento, espacio de padre y seguimiento de cabeza/cuello del rig

**Dónde encontrarla:** pestaña BoneCraft → Setup Rigging → Rigify Tools (y la sección Rigify Properties)

Descripción de imagen del original en inglés (imagen omitida): Rigify Tools muestra el acceso a la mejora. Selecciona un rig Rigify generado para usar los controles correspondientes.

*Panel emergente nativo, BoneCraft 9.2.18. Rigify Tools muestra el acceso a la mejora. Selecciona un rig Rigify generado para usar los controles correspondientes.*

---

### Retarget {#retarget}

**Qué hace:** transfiere animación entre esqueletos, por ejemplo un clip de captura de movimiento a tu avatar. Empareja huesos por nombre y dirección para conservar la orientación de extremidades. La coincidencia flexible de clavículas evita rotaciones excesivas de hombros.

**Controles principales:**

- **Import Clip** y **Browse Library** — cargan un clip o establecen una carpeta de biblioteca. Haz clic en el nombre de un clip para seleccionarlo
- **Auto-Match Bones** (marca de verificación en la fila del clip) — empareja huesos fuente y destino. Bone Mapping muestra las parejas
- **Preview** y **Stop Preview** — prueban el resultado
- **Apply** — hornea el clip en tu rig

**Dónde encontrarla:** pestaña BoneCraft → Setup Rigging → Retarget

Descripción de imagen del original en inglés (imagen omitida): Retarget empieza con Import Clip y Browse Library. El mapeo del clip y su previsualización aparecen al cargar un clip.

*Panel emergente nativo, BoneCraft 9.2.18. Retarget empieza con Import Clip y Browse Library. El mapeo del clip y su previsualización aparecen al cargar un clip.*

---

### Corrective Shape Keys {#corrective-shape-keys}

**Qué hace:** claves de forma que se activan cuando un hueso alcanza un ángulo, para corregir pinzamientos o colapsos en poses extremas.

**Ejemplo:** el codo del personaje colapsa al doblarse del todo. Una corrección esculpida del codo, vinculada al hueso del brazo, se aplica automáticamente al doblarlo.

**Controles principales:**

- New Corrective — ajustes de **Shape Key**, **Driver Bone**, eje de rotación, ángulo de intensidad máxima y aparición gradual
- Lista de correctivos — **Edit** y **Delete**, bajo la lista, actúan sobre el correctivo seleccionado

La malla hija del esqueleto debe tener una clave de forma Basis. Selecciona el esqueleto para mostrar New Corrective. Su malla hija proporciona las claves de forma.

Para crear un correctivo:

1. Selecciona **Shape Key**.
2. Selecciona **Driver Bone**.
3. Selecciona el eje de rotación.
4. Configura el ángulo de intensidad máxima de la forma.
5. Configura la gradualidad de su aparición.
6. Selecciona **Create Corrective**.

Para seleccionar un correctivo existente, haz clic en el nombre de su clave de forma en la lista.

Edit parte de los valores actuales del correctivo. Después de hacer clic en Edit:

1. En Adjust Last Operation, cambia el ángulo.
2. Cambia la atenuación.

**Dónde encontrarla:** pestaña BoneCraft → Skin → Correctives (la malla necesita una clave de forma Basis)

Descripción de imagen del original en inglés (imagen omitida): selecciona el esqueleto para mostrar New Corrective. Su malla hija proporciona las claves de forma.

*Panel emergente nativo, BoneCraft 9.2.18. Selecciona el esqueleto para mostrar New Corrective. Su malla hija proporciona las claves de forma.*

---

### Graph Tools {#graph-tools}

**Qué hace:** herramientas de ajuste de animación para claves y curvas.

- **Interactive Breakdown** (Breakdowner) — mezcla la pose actual entre los fotogramas clave más próximos al arrastrar a izquierda y derecha. Su atajo en la Vista 3D es **Ctrl+Shift+B**
- **Apply Delta** (Delta Mover) — desplaza huesos seleccionados una cantidad exacta en espacio de pantalla o global. Su atajo en la Vista 3D es **Ctrl+Shift+D**
- **Capture** y **Swap** (Buffer Curves) — conservan una copia de las curvas y alternan entre ella y tus ediciones
- **Smart Bake** — hornea en claves la animación dirigida por restricciones y elimina claves redundantes (**Tol** determina cuánto)
- **Euler Filter** — corrige inversiones de rotación causadas por bloqueo de cardán
- Tangent Handles — configura tipos de manejador de claves seleccionadas: **Auto**, **Vector**, **Aligned**, **Free** o **Auto Clamped**

**Dónde encontrarla:** pestaña BoneCraft → Review → Graph Tools

Descripción de imagen del original en inglés (imagen omitida): Interactive Breakdown inicia un arrastre en los huesos de pose seleccionados.

*Panel emergente nativo, BoneCraft 9.2.18. Interactive Breakdown inicia un arrastre en los huesos de pose seleccionados.*

Descripción de imagen del original en inglés (imagen omitida): Apply Delta y sus opciones de desplazamiento.

*Panel emergente nativo, BoneCraft 9.2.18. Apply Delta y sus opciones de desplazamiento.*

Descripción de imagen del original en inglés (imagen omitida): Buffer Curves, Euler Filter y Smart Bake. El desplegable Options está cerrado.

*Panel emergente nativo, BoneCraft 9.2.18. Buffer Curves, Euler Filter y Smart Bake. El desplegable Options está cerrado.*

Descripción de imagen del original en inglés (imagen omitida): Tangent Handles ofrece Auto, Vector, Aligned, Free y Auto Clamped.

*Panel emergente nativo, BoneCraft 9.2.18. Tangent Handles ofrece Auto, Vector, Aligned, Free y Auto Clamped.*

---

## Herramientas de pesos {#weight-tools}

Estas herramientas controlan cómo se deforma la malla al mover huesos. Los pesos indican qué huesos sigue cada parte y en qué proporción.

---

### Automatic Bone Weight Recalculation {#automatic-bone-weight-recalculation}

**Qué hace:** recalcula los pesos de una malla a partir del rig existente, sin cambiar la malla. En mallas densas trabaja mediante una malla proxy más ligera para no fallar silenciosamente.

**Controles principales:** Body calcula pesos a partir del rig existente. Clothing transfiere pesos desde una malla fuente correctamente ponderada. Los ajustes están sobre el botón.

1. En **Mesh to Reweight**, selecciona la malla de destino.
2. En **Existing Armature**, selecciona el esqueleto.
3. Selecciona el modo Body o Clothing.

Para Body, selecciona el método.

Para Clothing:

1. En **Weighted Body**, selecciona la malla fuente con pesos correctos.
2. Selecciona el método.

Para cualquiera de los modos:

1. Configura la mezcla.
2. Configura el suavizado.
3. Configura el máximo de influencias de huesos por vértice.
4. Configura el peso mínimo.
5. Elige si conservar una copia de seguridad.
6. Selecciona **Automatic Bone Weight Recalculation**.

El acceso CATS **Smart Automatic Weights** abre un diálogo para la malla de destino, el esqueleto y el modo. En Clothing también incluye la malla fuente.

**Dónde encontrarla:** pestaña BoneCraft → Skin → Weight Tools

Descripción de imagen del original en inglés (imagen omitida): ajustes de Automatic Bone Weight Recalculation con la malla y el esqueleto de ejemplo seleccionados.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Ajustes de Automatic Bone Weight Recalculation con la malla y el esqueleto de ejemplo seleccionados.*

---

### Weight Mirror {#weight-mirror}

**Qué hace:** copia pesos de un lado del avatar al otro. Úsala para personajes simétricos.

**Controles principales:**

- **Mirror All Weights** — refleja todos los grupos de huesos al lado opuesto
- **Mirror Active Weight** — refleja solo el grupo de huesos activo
- **Axis** y **Direction** — eligen el eje de reflexión y el lado que aporta pesos
- **Search Distance** — distancia permitida entre la posición reflejada de un vértice y su pareja espacial
- **Select Unmatched** — selecciona vértices sin pareja. **Normalize Weights** hace después que los pesos sumen 1.0

El reflejo usa posiciones espaciales, no la topología de la malla.

1. Haz clic en un botón de reflejo.
2. En Adjust Last Operation, selecciona **Axis**.
3. Selecciona **Direction**.
4. Configura **Search Distance**.

**Mirror Active Weight** también está en Weights → BoneCraft y en la pestaña Weights de Tool Shelf.

**Dónde encontrarla:** pestaña BoneCraft, en modo Weight Paint → Weight Mirror

Descripción de imagen del original en inglés (imagen omitida): acciones Weight Mirror. Después del clic, configura el eje en Adjust Last Operation. Configura allí las opciones de búsqueda.

*Panel emergente nativo, BoneCraft 9.2.18. Acciones Weight Mirror. Después del clic, configura el eje en Adjust Last Operation. Configura allí las opciones de búsqueda.*

---

### Weight Transfer {#weight-transfer}

**Qué hace:** copia pesos de una malla fuente a la activa. Sirve para adjuntar ropa a un cuerpo o pasar pesos de una malla de alta resolución a otra de menor resolución.

**Controles principales:** **Normalize** en Adjust Last Operation mantiene la suma de pesos en 1.0. **Select Problem Vertices** selecciona vértices con malas coincidencias.

Mantén activa la malla de destino en modo Weight Paint.

1. En **Source Mesh**, selecciona la malla fuente.
2. Haz clic en **Transfer Weights**.
3. En Adjust Last Operation, selecciona el método de transferencia.
4. Selecciona el filtro de huesos.

El resultado muestra la distancia media y máxima.

**Dónde encontrarla:** pestaña BoneCraft, en modo Weight Paint → Weight Transfer (también en Skin → Weight Tools)

Descripción de imagen del original en inglés (imagen omitida): elige Source Mesh antes de Transfer Weights. Los campos de distancia conservan sus valores iniciales en este ejemplo.

*Panel emergente nativo, BoneCraft 9.2.18. Elige Source Mesh antes de Transfer Weights. Los campos de distancia conservan sus valores iniciales en este ejemplo.*

---

### Weight Table {#weight-table}

**Qué hace:** muestra el peso exacto del vértice seleccionado para cada hueso. Puedes establecer valores precisos.

**Uso:**

1. Entra en el modo Weight Paint.
2. Activa la **máscara de selección de vértices**.
3. Selecciona un vértice.

La tabla enumera los huesos y pesos del vértice seleccionado.

4. Haz clic en el icono de mano de la fila de un hueso.
5. En Adjust Last Operation, configura **Weight**.

Add Influence usa el hueso que seleccionas. Después de Add Influence, configura también su nuevo peso en Adjust Last Operation. Con varios vértices seleccionados, **Normalize All Vertices** normaliza todos ellos.

**Dónde encontrarla:** pestaña BoneCraft, en modo Weight Paint → Weight Table

Descripción de imagen del original en inglés (imagen omitida): Weight Table con varios vértices seleccionados. Selecciona uno para editar los pesos en detalle.

*Panel emergente nativo, BoneCraft 9.2.18. Weight Table con varios vértices seleccionados. Selecciona uno para editar los pesos en detalle.*

---

### Flood Fill {#flood-fill}

**Qué hace:** cambia los pesos del grupo de vértices activo en toda la malla, incluidos los vértices no seleccionados.

Antes de cualquier acción Flood Fill:

1. Selecciona la malla.
2. Entra en el modo Weight Paint.
3. Activa el grupo de vértices necesario.

**Acciones:**

- **Flood to 0.0** elimina los pesos positivos asignados al grupo activo en toda la malla. Los otros grupos no cambian.
- **Flood to 1.0** asigna 1.0 al grupo activo en cada vértice. Para cada vértice, elimina los demás pesos positivos si su suma supera 1e-6.
- **Flood to Custom** asigna un **Value** positivo al grupo activo en cada vértice. Con **Normalize** activado, también normaliza los pesos de toda la malla. Un **Value** de 0 no realiza asignaciones ni normalización. Para borrar pesos, usa **Flood to 0.0**.

El menú y la estantería Weights llaman Flood to Zero y Flood to One a los botones de valor fijo.

Para un relleno personalizado:

1. Selecciona **Flood to Custom**.
2. Configura inmediatamente **Value** en Adjust Last Operation.
3. Activa o desactiva **Normalize**.

**Dónde encontrarla:** en modo Weight Paint: pestaña BoneCraft → Skin → Weight Tools; también Weights → BoneCraft y Tool Shelf → Weights → BoneCraft

Descripción de imagen del original en inglés (imagen omitida): acciones Flood Fill. Después del clic, configura el valor personalizado en Adjust Last Operation.

*Panel emergente nativo, BoneCraft 9.2.18. Acciones Flood Fill. Después del clic, configura el valor personalizado en Adjust Last Operation.*

---

### Deform vs Control {#deform-vs-control}

**Qué hace:** separa huesos deformadores de huesos de control. Los deformadores mueven la malla. El animador mueve los controles. La herramienta marca los deformadores y les asigna nombres de deformación. También exporta un esqueleto solo de deformadores.

**Dónde encontrarla:** pestaña BoneCraft, en Pose Mode → Deform vs Control

Descripción de imagen del original en inglés (imagen omitida): listas Deform y Control del rig de ejemplo. Tiene 19 huesos deformadores y ningún hueso de control.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Listas Deform y Control del rig de ejemplo. Tiene 19 huesos deformadores y ningún hueso de control.*

---

### Delta Mush {#delta-mush}

**Qué hace:** una deformación suavizada que reduce pinzamientos en articulaciones. La malla mantiene su forma en reposo y se deforma mejor en movimiento.

**Uso:** estas acciones requieren Object Mode y una malla activa.

1. Haz clic en **Add Delta Mush**.

La herramienta añade el modificador y lo vincula a la forma de reposo. Ajusta sus opciones inmediatamente después:

2. En Adjust Last Operation, configura **Iterations**.
3. Configura **Smooth Strength**.
4. Activa o desactiva **Pin Borders**.
5. Activa o desactiva **Only Smooth Deform**.

Cuando existe el modificador, el panel muestra **Rebind** y **Remove**. Su desplegable Settings contiene las iteraciones, la intensidad de suavizado y el anclaje de bordes del modificador.

**Dónde encontrarla:** BoneCraft → Skin → Delta Mush (Object Mode; malla)

Descripción de imagen del original en inglés (imagen omitida): Add Delta Mush inicia la configuración. Ajusta sus opciones inmediatamente después del clic.

*Panel emergente nativo, BoneCraft 9.2.18. Add Delta Mush inicia la configuración. Ajusta sus opciones inmediatamente después del clic.*

---

### Proximity Wrap {#proximity-wrap}

**Qué hace:** hace que una malla siga la superficie de otra como una segunda piel. Sirve para ropa ajustada al cuerpo.

**Uso:** requiere Object Mode y una malla de destino activa. Mantén el esqueleto de la malla conductora en reposo al vincular.

1. Selecciona la malla de destino.
2. Selecciona otra **Driver Mesh**.
3. Haz clic en **Bind Proximity Wrap**.

El desplegable Options bajo el botón enumera **Falloff Type** y **Max Distance**. En 9.1.2, la configuración guarda esos valores, pero no cambian su vinculación Surface Deform. Después de vincular, el panel muestra **Rebind** y **Unbind**. Unbind desactiva el modificador en la vista y el render. No lo elimina.

**Dónde encontrarla:** BoneCraft → Skin → Proximity Wrap (Object Mode; malla)

Descripción de imagen del original en inglés (imagen omitida): elige Driver Mesh antes de Bind Proximity Wrap. El desplegable Options está cerrado.

*Panel emergente nativo, BoneCraft 9.2.18. Elige Driver Mesh antes de Bind Proximity Wrap. El desplegable Options está cerrado.*

---

## Controles del rig {#rig-controls}

Estas herramientas aparecen en BoneCraft en Pose Mode.

---

### Space Switch {#space-switch}

**Qué hace:** cambia el espacio que sigue un hueso durante la animación. Una mano que sostiene un accesorio puede dejar de seguir al cuerpo y permanecer quieta en el mundo con un clic.

**Controles principales:**

- **Add Space** y **Remove Space** (X en Manage Spaces) — espacios que puede seguir un hueso (World, Origin u otro hueso)
- Un botón por espacio, con su nombre. El espacio actual tiene una marca ●. Para cambiar el hueso, haz clic en otro espacio

**Dónde encontrarla:** pestaña BoneCraft, en Pose Mode → Space Switch

Descripción de imagen del original en inglés (imagen omitida): Space Switch antes de definir ningún espacio. Add Space inicia la configuración.

*Panel emergente nativo, BoneCraft 9.2.18. Space Switch antes de definir ningún espacio. Add Space inicia la configuración.*

---

### Spline IK {#spline-ik}

**Qué hace:** hace que una cadena de huesos siga una curva. Sirve para colas, tentáculos, cuerdas, cabello largo y columnas que necesitan movimientos amplios y suaves.

**Uso:**

1. Activa el hueso inicial.
2. Haz clic en **Generate Spline IK**.
3. En Adjust Last Operation, configura **Chain Length**.
4. Configura **Curve Resolution**.
5. Configura **Stretch**.
6. Configura **Volume Preservation**.

**Remove Spline IK** elimina la configuración.

**Dónde encontrarla:** pestaña BoneCraft, en Pose Mode → Spline IK

Descripción de imagen del original en inglés (imagen omitida): acciones Spline IK. Configura las opciones de cadena en Adjust Last Operation después de generar.

*Panel emergente nativo, BoneCraft 9.2.18. Acciones Spline IK. Configura las opciones de cadena en Adjust Last Operation después de generar.*

---

### Chain Dynamics {#chain-dynamics}

**Qué hace:** añade movimiento secundario de apariencia física a una cadena de huesos. Los huesos se retrasan respecto al padre en movimiento y rebotan al detenerse. Sirve para mechones, colas y accesorios.

**Uso:**

1. Selecciona la cadena de huesos.
2. Haz clic en **Add Chain Dynamics**.
3. En Adjust Last Operation, configura **Stiffness**.
4. Configura **Damping**.
5. Configura **Mass**.
6. Configura **Gravity Scale**.

El desplegable Settings bajo la acción también enumera estos parámetros. Cuando existe dinámica, el panel muestra **Bake** y **Remove**. La colisión usa una esfera simplificada, por lo que las superficies cóncavas pueden no colisionar correctamente.

**Dónde encontrarla:** pestaña BoneCraft, en Pose Mode → Chain Dynamics

Descripción de imagen del original en inglés (imagen omitida): Add Chain Dynamics inicia la configuración. Despliega Settings para sus parámetros.

*Panel emergente nativo, BoneCraft 9.2.18. Add Chain Dynamics inicia la configuración. Despliega Settings para sus parámetros.*

---

### Ribbon {#ribbon}

**Qué hace:** crea una cinta de Bendy Bones —huesos que se curvan y tuercen suavemente— para labios, cejas, cinturones y otras zonas curvas blandas.

**Uso:**

1. Selecciona la cadena de huesos.
2. Haz clic en **Generate Ribbon**.
3. En Adjust Last Operation, configura **Control Bones**.
4. Configura **Ribbon Width**.

**Remove Ribbon** elimina la configuración.

**Dónde encontrarla:** pestaña BoneCraft, en Pose Mode → Ribbon

Descripción de imagen del original en inglés (imagen omitida): acciones Ribbon y longitud de cadena. Ajusta la cinta generada inmediatamente después del clic.

*Panel emergente nativo, BoneCraft 9.2.18. Acciones Ribbon y longitud de cadena. Ajusta la cinta generada inmediatamente después del clic.*

---

### Viseme Library {#viseme-library}

**Qué hace:** crea y administra conjuntos de visemas (formas de boca) vinculados a claves de forma. También genera claves de sincronización labial a partir de texto. Para mapear visemas VRChat, usa VRChat Viseme Mapping. Para generar visemas nuevos, usa Visemes de CATS.

**Controles principales:**

- **New Set** y **Delete** — crean o eliminan un conjunto de visemas
- En cada conjunto, un botón por visema (con altavoz) permite previsualizarlo
- Lip Sync — genera claves de visemas desde texto, con fotogramas por fonema y suavizado

**Dónde encontrarla:** CATS → Avatar Tools → Viseme Library (esqueleto); Lip Sync (Pose Mode)

Descripción de imagen del original en inglés (imagen omitida): Viseme Library empieza con New Set. Cambia a Pose Mode para usar Lip Sync.

*Panel emergente nativo, BoneCraft 9.2.18. Viseme Library empieza con New Set. Cambia a Pose Mode para usar Lip Sync.*

Descripción de imagen del original en inglés (imagen omitida): texto de Lip Sync y Generate Lip Sync. Despliega Options para temporización y suavizado.

*Panel emergente nativo, BoneCraft 9.2.18. Texto de Lip Sync y Generate Lip Sync. Despliega Options para temporización y suavizado.*

---

### Set Driven Key {#set-driven-key}

**Qué hace:** vincula el valor de transformación de un hueso con otro sin expresiones Python. Por ejemplo, mover un control en X puede elevar un hueso de destino en Z. Este panel crea destinos de transformación de huesos.

1. Selecciona **Driver Bone**.
2. Selecciona **Driver Attribute**.
3. Selecciona **Target Bone**.
4. Selecciona **Target Attribute**.
5. Coloca los huesos en una pose.
6. Registra cada punto.
7. Selecciona **Create SDK**.

**Controles principales:**

- **Driver Bone** y **Driver Attribute** — qué controla
- **Target Bone** y **Target Attribute** — qué es controlado
- **Set Value** y **Record Point** — registran un punto de la curva
- **Create SDK** — crea el controlador

**Dónde encontrarla:** pestaña BoneCraft, en Pose Mode → Set Driven Key

Descripción de imagen del original en inglés (imagen omitida): elige los huesos conductor y de destino antes de registrar un punto de clave controlada. Los campos están sin asignar en el ejemplo.

*Panel emergente nativo, BoneCraft 9.2.18. Elige los huesos conductor y de destino antes de registrar un punto de clave controlada. Los campos están sin asignar en el ejemplo.*

---

### Rig Validator {#rig-validator}

**Qué hace:** comprueba el rig mediante reglas e informa de problemas. Comprueba nombres, huesos ausentes, restricciones rotas, jerarquía, pesos, controladores que necesitan Python y reglas de Mechanisms. Los nombres de huesos con guiones (como `DEF-upper_arm.L`) son válidos.

**Controles principales:**

- **Run Validation** — ejecuta todas las comprobaciones y enumera los resultados
- **Export Report** — guarda los resultados en un archivo

Task Board (pestaña BoneCraft → Overview → Task Board) muestra una tarea del validador si falla una comprobación.

**Dónde encontrarla:** pestaña BoneCraft → Review → Rig Validator

Descripción de imagen del original en inglés (imagen omitida): la validación indica un aviso de colección. Sin una malla emparentada en el rig de ejemplo, omite la comprobación de pesos.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. La validación indica un aviso de colección. Sin una malla emparentada en el rig de ejemplo, omite la comprobación de pesos.*

---

### Rig Notes {#rig-notes}

**Qué hace:** notas escritas adjuntas a los huesos del rig: lo que configuraste, recordatorios y notas para colaboradores.

**Controles principales:** **Add Note** y **Remove** en cada nota. Rig Readme muestra las notas del rig como página de solo lectura.

**Dónde encontrarla:** pestaña BoneCraft → Overview → Rig Notes y Review → Rig Readme

Descripción de imagen del original en inglés (imagen omitida): una nota adjunta a Hips en Pose Mode. Add Note crea una anotación. Remove la elimina.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Una nota adjunta a Hips en Pose Mode. Add Note crea una anotación. Remove la elimina.*

Siguiente: [Rig Builder](06-rig-builder.md)
