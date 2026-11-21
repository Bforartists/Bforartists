# Guías 1–7 {#guides-17}

[← Índice](index.md)

## Guía 1: llevar tu primer avatar a VRChat {#guide-1-get-your-first-avatar-into-vrchat}

Para obtener una malla de práctica, sigue el [taller escrito del maniquí](06-rig-builder.md#illustrated-mannequin-workshop). Sus etapas son Simple Human, un maniquí sin rig, Auto-Rig e IK/FK.

> **Tiempo:** unos 45–60 minutos para una primera ejecución completa
> **Resultado:** un avatar con rig, listo para VRChat y exportado para el SDK de VRChat

**Antes de empezar, comprueba esto:**

- [ ] Tu modelo 3D está importado en Bforartists (File > Import, elige tu formato)
- [ ] El modelo está en pose en T (brazos extendidos a los lados y cuerpo erguido), o casi
- [ ] El modelo no tiene geometría claramente rota (sin triángulos sueltos flotando)
- [ ] Ves tu modelo en la Vista 3D como una forma gris sólida

---

### Paso 1 — Abrir Rig Builder {#step-1--open-the-rig-builder}

1. En la Vista 3D, pulsa **T** para mostrar la Tool Shelf izquierda.

2. Abre **Rig Builder**.

Rig Builder también aparece en **Properties → Scene** cuando Preferences → Tabs → Scene Properties → Show está activado. Sus tres partes son **Auto-Rig Wizard**, Quick Rig (esqueletos prefabricados) y **Mannequin**.

3. Despliega **Auto-Rig Wizard**.

4. Selecciona **Start Auto-Rig**.

También puedes iniciar el asistente desde Add → Armature → Auto-Rig Wizard en la Vista 3D y continuar después en Rig Builder.

Descripción de imagen del original en inglés (imagen omitida): Auto-Rig Wizard en la pestaña Rig Builder.

*Captura histórica del taller. Auto-Rig Wizard en la pestaña Rig Builder.*

---

### Paso 2 — Seleccionar tu malla {#step-2--select-your-mesh}

El asistente enumera las mallas de la escena.

1. Selecciona la malla de tu avatar en la lista.

2. Selecciona **Next**.

**Deberías ver:** una línea «Selected:» con el nombre de tu malla y después el paso del tipo de rig.

Descripción de imagen del original en inglés (imagen omitida): elegir la malla de entrada de Auto-Rig Wizard.

*Captura histórica del taller. Elegir la malla de entrada de Auto-Rig Wizard.*

---

### Paso 3 — Elegir el tipo de rig {#step-3--choose-the-rig-type}

1. Para parpadeos, expresiones y sincronización labial, selecciona **Body + Face**.

2. Para un cuerpo sin controles faciales, selecciona **Body Only**.

3. En Generation Options, configura **Kinematics** como IK/FK, IK only o FK only.

4. Selecciona **Next**.

Descripción de imagen del original en inglés (imagen omitida): elegir el tipo de rig corporal y los métodos IK/FK.

*Captura histórica del taller. Elegir el tipo de rig corporal y los métodos IK/FK.*

---

### Paso 4 — Colocar los marcadores del cuerpo {#step-4--place-body-markers}

Los marcadores identifican pelvis, columna, cuello, cabeza, hombros, brazos, manos, piernas y pies. BoneCraft usa esas posiciones para crear los huesos. Comprueba cada marcador con cuidado.

**Smart Detection:**

1. Selecciona **Detect Markers**.

2. Selecciona **Accept High** para conservar los marcadores de confianza alta.

3. Selecciona **Reset Low** para borrar los marcadores de confianza baja y colocarlos manualmente.

BoneCraft sigue las extremidades de la malla y asigna una confianza a cada marcador. **Guess Markers from Mesh**, en cambio, estima las posiciones a partir de las proporciones de la malla.

**Con la herramienta de la vista:**

1. En Object Mode, activa Place Rig Markers en la barra de herramientas de la vista.

2. Haz clic en la malla para colocar y confirmar el marcador indicado en la cabecera de la herramienta.

3. Repite para el siguiente marcador sin confirmar.

4. Cuando termines el paso de marcadores, selecciona **Next** en el asistente.

La cabecera de la herramienta también contiene bloqueos de ejes y un interruptor de reflejo.

**Un marcador cada vez:** cada marcador tiene una fila de botones con iconos. Mantén el puntero sobre un botón para leer su descripción.

1. Selecciona **Place Marker**, el icono de flecha de la fila del marcador.

2. Haz clic en la posición deseada de tu avatar.

3. Cuando la posición sea correcta, selecciona **Confirm Marker**, la marca de verificación.

**Reset Marker**, la flecha circular, borra un marcador colocado para volver a colocarlo.

**Simetría:** **Toggle Symmetry** coloca el marcador opuesto cada vez que colocas uno. Es el primer icono de cada fila de marcador izquierdo o derecho. **Mirror L to R** y **Mirror R to L** copian todos los marcadores confirmados al lado opuesto.

1. Cuando todos los marcadores estén colocados, selecciona **Confirm All Placed**.

2. Selecciona **Next**.

Descripción de imagen del original en inglés (imagen omitida): revisar los marcadores corporales detectados antes de ajustarlos.

*Captura histórica del taller. Revisar los marcadores corporales detectados antes de ajustarlos.*

---

### Paso 5 — Colocar los marcadores de los dedos {#step-5--place-finger-markers}

1. En Finger Detail, selecciona la cantidad de dedos, desde «0 — No Fingers» hasta «5 — Full Human Hand».

2. Selecciona **Guess Finger Markers**.

3. Ajusta las posiciones incorrectas.

4. Selecciona **Next**.

BoneCraft sigue cada dedo desde el nudillo hasta la punta usando la forma de la mano. Una mano estándar usa «5 — Full Human Hand».

---

### Paso 6 — Colocar los marcadores de la cara (solo Body + Face) {#step-6--place-face-markers-body--face-only}

1. Selecciona **Guess Face Markers**.

2. Ajusta ojos, párpados, cejas, comisuras de la boca y mandíbula según sea necesario.

3. Selecciona **Next**.

Los marcadores de los ojos conservan sus posiciones asignadas manualmente.

---

### Paso 7 — Revisar y generar {#step-7--review-and-generate}

El paso de revisión enumera los avisos y las opciones de generación. Haz clic en **Generate Rig**.

**Deberías ver:** huesos naranjas dentro de tu avatar, incluidas extremidades IK/FK y huesos de los dedos. Un rig Body + Face también contiene un rig facial. La piel vinculada se deforma al mover los huesos.

El paso final ofrece **Build Control Rig** y **Close Wizard**. Build Control Rig aplica las opciones de revisión que Generate Rig no aplica. [Rig Builder](06-rig-builder.md) describe ambos controles.

> **Pesos de piel:** definen qué huesos mueven cada parte de la malla. BoneCraft asigna pesos automáticamente. Para afinarlos, usa Weight Tools en [Herramientas de rig](05-rig-tools.md).

Descripción de imagen del original en inglés (imagen omitida): revisar los ajustes del rig antes de generarlo.

*Captura histórica del taller. Revisar los ajustes del rig antes de generarlo.*

---

### Paso 8 — Mapear a los huesos humanoides de VRChat {#step-8--map-to-vrchats-humanoid-bones}

1. Pulsa **N** para mostrar la barra lateral derecha.

2. Abre **CATS → Avatar Tools → Set Up Humanoid Bones**.

3. Selecciona **Auto-Map All**.

4. Selecciona **Normalize Names**.

5. Selecciona **Validate**.

Auto-Map All conecta los huesos con las ranuras corporales de VRChat. Normalize Names asigna a los huesos mapeados los nombres que espera VRChat.

**Deberías ver:** las ranuras obligatorias (Hips, Spine, Head, LeftUpperArm, etc.) muestran cada una un hueso. La guía 5 explica las ranuras.

Consulta los [controles de mapeo humanoide](08-vrchat.md#set-up-humanoid-bones).

---

### Paso 9 — Exportar para VRChat {#step-9--export-for-vrchat}

Consulta los [ajustes de exportación Unity / VRChat](08-vrchat.md#export-to-vrchat).

1. Selecciona el esqueleto del avatar.
2. Abre **CATS → Import / Export → Game Engine Export → Unity / VRChat**.
3. Configura **Folder**.
4. Configura **Avatar** con el nombre de exportación.
5. Elige **Bone Names**.
6. Revisa la vista previa de nombres si usas un preajuste.
7. Haz clic en **Export to VRChat (Unity)**.

**Keep Original Names** es el valor predeterminado. **Unity-Preset** y **Unreal-Preset** renombran los huesos reconocidos en las copias de exportación. El rig de trabajo conserva sus nombres.

Los botones principales de exportación Unity y Unreal aceptan los modos Objeto, Pose y Edición. Restauran el modo y la selección anteriores.

Consulta [nombres de exportación y limitaciones](08-vrchat.md#export-bone-naming) para los conflictos y las restricciones de mapeo y animación.

**Deberías ver:** el avatar exportado en la carpeta elegida, listo para VRChat Creator Companion y VRChat SDK en Unity.

---

**Lo que esto permite:** un avatar de VRChat con rig. Después puedes añadir física de cabello (guía 6), ropa (guía 7), sincronización labial (guía 8) y comprobar el rendimiento (guía 9). Para limpieza CATS y configuración VRChat, consulta la [guía 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats).

---

## Guía 2: llevar un avatar de VRoid a VRChat {#guide-2-bring-a-vroid-avatar-into-vrchat}

> **Tiempo:** unos 15–25 minutos
> **Resultado:** tu avatar de VRoid listo para exportarlo a VRChat

**Antes de empezar, comprueba esto:**

- [ ] Has exportado tu avatar desde VRoid Studio como archivo `.vrm`, o lo has descargado de VRoid Hub como `.zip`
- [ ] BoneCraft está instalado y activado

---

### Paso 1 — Instalar el complemento VRM {#step-1--install-the-vrm-add-on}

BoneCraft necesita el complemento VRM para leer archivos `.vrm`.

1. Abre **CATS → Import / Export → VRM / VRoid**.

2. Instala la dependencia antes de importar.

3. Activa la dependencia.

El puente inactivo ofrece **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** y **Show Manual Instructions**.

Para un paquete sin conexión:

1. Abre las preferencias nativas.

2. Para un ZIP de complemento clásico, instálalo mediante **Add-ons → Install from Disk…**.

3. Para un paquete de extensión moderno, usa en su lugar el menú nativo de instalación de Extensions.

4. Vuelve al puente.

5. Confirma que el puente indica **Active**.

Consulta los [controles de instalación de puentes de formatos](08-vrchat.md#vrm-bridge).

---

### Paso 2 — Importar tu avatar {#step-2--import-your-avatar}

1. En **VRM / VRoid**, selecciona **Import VRM…**.

2. Selecciona tu archivo `.vrm`.

Para una descarga de VRoid:

1. Selecciona **Import VRoid (.vroid / .zip)…**.

2. Selecciona el archivo `.zip` descargado.

Si seleccionas un proyecto de VRoid Studio (`.vroid`), BoneCraft muestra una tarjeta «VRoid Studio Project». Un proyecto todavía no es un avatar.

Para ese archivo de proyecto:

1. Exporta el proyecto a VRM en VRoid Studio.

2. Importa ese archivo VRM.

**Deberías ver:** tu personaje de VRoid en la vista con su esqueleto colocado.

---

### Paso 3 — Mapear a los huesos humanoides de VRChat {#step-3--map-to-vrchats-humanoid-bones}

1. Abre **CATS → Avatar Tools → Set Up Humanoid Bones**.

2. Selecciona **Auto-Map All**.

Los esqueletos de VRoid siguen una distribución estándar, así que esto suele rellenar todas las ranuras. Si una ranura es incorrecta, selecciona **Fix Humanoid Map** en Lint, dentro de **VRM / VRoid**. Repara errores comunes de asignación de nombres de VRoid.

---

### Paso 4 — Corregir los nombres de los huesos {#step-4--fix-bone-names}

En **Set Up Humanoid Bones**, selecciona **Normalize Names**. Sustituye los nombres de VRoid de los huesos mapeados por los que espera VRChat.

---

### Paso 5 — Configurar visemas (sincronización labial) {#step-5--set-up-visemes-lip-sync}

Los avatares de VRoid ya tienen las formas de boca para la sincronización labial. En **VRM / VRoid**, haz clic en **Map VRoid Visemes**. BoneCraft relaciona las claves de forma de VRoid con las formas de sincronización labial de VRChat.

---

### Paso 6 — Física del cabello (opcional) {#step-6--hair-physics-optional}

El cabello de VRoid usa SpringBones. **Convert SpringBones → PhysBones** en **VRM / VRoid** los convierte en PhysBones de VRChat. La guía 6 trata la física del cabello con más detalle.

---

### Paso 7 — Exportar {#step-7--export}

Exporta como en la guía 1, paso 9.

**Lo que esto permite:** tu avatar de VRoid está listo para VRChat Creator Companion. También puedes comprobar el rendimiento (guía 9) antes de subirlo.

---

## Guía 3: llevar un avatar MMD a VRChat {#guide-3-bring-an-mmd-avatar-into-vrchat}

> **Tiempo:** unos 20–30 minutos
> **Resultado:** tu modelo MMD `.pmx` listo para VRChat

**Antes de empezar, comprueba esto:**

- [ ] Tienes un archivo de modelo MMD `.pmx` o `.pmd`
- [ ] BoneCraft está instalado

---

### Paso 1 — Instalar mmd_tools {#step-1--install-mmd_tools}

BoneCraft necesita **mmd_tools** para leer archivos MMD. Reconoce tanto complementos clásicos como extensiones modernas de Blender.

1. Abre **CATS → Import / Export → MMD / PMX**.
2. Haz clic en **Auto-Install Latest from GitHub** cuando el puente indique que falta una dependencia.
3. Usa **Open Add-on Preferences** para activar una copia instalada pero desactivada.
4. Confirma que el puente indica **Active** antes de importar.

Para una instalación manual:

1. En la tarjeta del puente inactivo, selecciona **Website** o **Show Manual Instructions**.

2. Instala la extensión oficial MMD mediante **Preferences → Get Extensions**.

Para un ZIP sin conexión:

1. Para un paquete de extensión moderno, usa el menú de instalación de extensiones.

2. Para un paquete de complemento clásico, usa **Add-ons → Install from Disk…**.

El contenido independiente del puente también ofrece **Install from .zip on Disk...** cuando se muestra.

Si la instalación indica que no hay un repositorio local de extensiones:

1. Abre **Preferences → Get Extensions → Repositories**.

2. Añade o activa un repositorio local.

3. Reintenta la instalación.

Usa el paquete de publicación original. Un error de instalación o una importación cancelada no cuentan como importación correcta.

Consulta los [controles de instalación de puentes de formatos](08-vrchat.md#vrm-bridge).

---

### Paso 2 — Importar tu archivo PMX {#step-2--import-your-pmx-file}

1. En **MMD / PMX**, selecciona **Import PMX / PMD...**.

2. Selecciona tu modelo.

**Deberías ver:** tu personaje MMD en la vista con nombres de huesos japoneses.

---

### Paso 3 — Corregir los nombres de los huesos {#step-3--fix-bone-names}

Mapea los huesos MMD a las ranuras humanoides de Unity antes de exportar a VRChat.

1. En **MMD / PMX**, selecciona **Convert Bone Names -> Unity**.

Para nombres en otro idioma:

1. Abre **CATS → CATS → Translate Bone Names**.

2. Selecciona el **Language** de origen.

3. Selecciona **Translate Bone Names**.

---

### Paso 4 — Limpiar el modelo {#step-4--clean-up-the-model}

Los modelos MMD suelen contener geometría adicional y piezas separadas.

1. Abre **CATS → CATS**.

2. Revisa las opciones de **Fix Model**.

3. Selecciona las operaciones de limpieza que necesita tu avatar.

4. Ejecuta **Fix Model**.

5. Selecciona **Join Meshes** para combinar las piezas del cuerpo en una malla, como se recomienda para VRChat.

La [guía 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats) explica el pipeline completo de CATS.

---

### Paso 5 — Mapear a los huesos humanoides de VRChat {#step-5--map-to-vrchats-humanoid-bones}

1. Abre **CATS → Avatar Tools → Set Up Humanoid Bones**.

2. Selecciona **Auto-Map All**.

3. Para una ranura vacía, selecciona su botón.

4. Selecciona el hueso correspondiente.

Los esqueletos MMD se parecen a los de VRChat, así que la mayoría de las ranuras se rellenan automáticamente.

---

### Paso 6 — Física y exportación {#step-6--physics-and-export}

**Convert Physics -> PhysBones** en **MMD / PMX** convierte la física de cuerpos rígidos del cabello y las faldas de MMD en PhysBones de VRChat. Después exporta como en la guía 1, paso 9.

**Lo que esto permite:** tu avatar MMD está listo para VRChat. Puedes añadir física de cabello (guía 6) y configurar sincronización labial (guía 8) antes de subirlo.

---

## Guía 4: corregir los nombres de los huesos de tu avatar {#guide-4-fix-your-avatars-bone-names}

> **Tiempo:** unos 5–15 minutos
> **Resultado:** los huesos necesarios para VRChat renombrados con nombres compatibles

**Antes de empezar, comprueba esto:**

- [ ] Tu avatar está abierto y su esqueleto es visible

---

### Paso 1 — Detectar el estilo de nombres actual {#step-1--detect-the-current-naming-style}

Consulta los [controles de nombres](08-vrchat.md#vrchat-naming-extras).

1. Abre **CATS → VRChat Tools**.

2. En Naming, selecciona **Detect**.

3. Después de cambiar nombres, selecciona **Force Rescan** para comprobar de nuevo.

BoneCraft indica el estilo detectado, por ejemplo Mixamo, VRoid o Unity, y una puntuación.

Para nombres de huesos en japonés, chino, coreano, portugués, español o francés:

1. Abre **CATS → CATS → Translate Bone Names**.

2. Selecciona el **Language** de origen.

3. Selecciona **Translate Bone Names**.

Esto convierte los nombres reconocidos al inglés.

---

### Paso 2 — Renombrar con los nombres de VRChat {#step-2--rename-to-vrchat-names}

Para cambiar nombres solo en la exportación, conserva los nombres de trabajo y elige **Unity-Preset** en la sección de exportación. Consulta [Nombres de huesos al exportar](08-vrchat.md#export-bone-naming).

1. Mapea los huesos como en la guía 5, paso 2.

2. En **Set Up Humanoid Bones**, selecciona **Normalize Names**.

Cada hueso mapeado recibe el nombre que espera VRChat.

**Deberías ver:** nombres como `Hips`, `Spine`, `Chest` y `LeftUpperArm`.

---

### Paso 3 — Correcciones manuales (si hacen falta) {#step-3--manual-fixes-if-needed}

El grupo Naming de **VRChat Tools** también tiene herramientas por lotes para los huesos restantes:

- **Find and Replace** — sustituye un fragmento de texto por otro en cada nombre de hueso
- **Add Prefix** y **Add Suffix** — añaden texto al principio o al final de cada nombre de hueso
- **Remove Prefix** y **Remove Suffix** — lo eliminan de nuevo
- **Regex Replace** — lo mismo, con una expresión regular

**Lo que esto permite:** los nombres correctos permiten que el mapeo humanoide (guía 5) funcione automáticamente. Sin ellos, VRChat no puede determinar cómo debe moverse tu personaje.

---

## Guía 5: mapear tu avatar al sistema corporal de VRChat {#guide-5-map-your-avatar-to-vrchats-body-system}

> **Tiempo:** unos 10–15 minutos
> **Resultado:** el esqueleto de tu avatar conectado al sistema de movimiento humanoide de VRChat

**Antes de empezar, comprueba esto:**

- [ ] Los huesos de tu avatar tienen nombres razonables (si no, consulta la guía 4)
- [ ] El esqueleto está seleccionado
- [ ] Estás en **Object Mode** (comprueba el desplegable superior izquierdo de la vista)

---

### Paso 1 — Abrir Set Up Humanoid Bones {#step-1--open-set-up-humanoid-bones}

En **CATS**, despliega **Avatar Tools** → **Set Up Humanoid Bones**.

---

### Paso 2 — Mapear automáticamente {#step-2--auto-map}

Haz clic en **Auto-Map All**. BoneCraft examina tu esqueleto y rellena las ranuras corporales.

> Una ranura humanoide identifica una parte del cuerpo, como Hips, Head o Left Hand. BoneCraft asigna huesos a esas ranuras. Los mapeos humanoides guardados se cargan correctamente al volver a abrir un archivo.

**Deberías ver:** las asignaciones de huesos y la proporción de ranuras obligatorias rellenas. Hay 15 ranuras obligatorias: Hips, Spine, Head, ambos brazos superiores, antebrazos, manos, muslos, piernas y pies. Las opcionales incluyen Chest, UpperChest y Neck.

---

### Paso 3 — Comprobar el mapeo {#step-3--check-the-mapping}

Haz clic en **Validate**. BoneCraft comprueba que cada ranura obligatoria tiene un hueso y que la jerarquía tiene sentido.

---

### Paso 4 — Rellenar a mano las ranuras vacías {#step-4--fill-empty-slots-by-hand}

Una ranura vacía muestra «(click to map)».

1. Selecciona la ranura vacía.

2. Selecciona el hueso correcto.

3. Selecciona **Validate** otra vez.

4. Selecciona **Normalize Names** para asignar los nombres de VRChat a los huesos mapeados.

---

### Paso 5 — Configurar seguimiento ocular (opcional) {#step-5--set-up-eye-tracking-optional}

Si tu avatar tiene huesos de ojos:

1. Abre **CATS → CATS → Eye Tracking**.

2. Selecciona **Auto-Detect** para buscar nombres de huesos de ojos.

3. Comprueba las asignaciones **Left Eye** y **Right Eye**.

4. Si hace falta, selecciona manualmente los huesos correctos.

5. Configura los límites de rotación.

6. Selecciona **Create Eye Tracking**.

La [guía 13, fase 3](03-guides-b.md#phase-3--eye-tracking) explica los ajustes.

**Lo que esto permite:** el mapeo humanoide permite que el avatar siga tus movimientos en VRChat. IK (cinemática inversa) hace que las manos del juego sigan tus mandos.

---

## Guía 6: añadir física del cabello {#guide-6-add-hair-physics}

> **Tiempo:** unos 15–25 minutos
> **Resultado:** el cabello y otras partes blandas del avatar se balancean con naturalidad en VRChat

**Antes de empezar, comprueba esto:**

- [ ] Tu avatar está abierto con el esqueleto seleccionado
- [ ] Set Up Humanoid Bones está completado (guía 5)

> PhysBone es el componente de VRChat que hace que los huesos reboten y se balanceen como si tuvieran peso. BoneCraft los configura en cadenas de huesos: cabello, orejas, colas, faldas y accesorios.

---

### Paso 1 — Abrir Add Hair Physics {#step-1--open-add-hair-physics}

En **CATS**, despliega **Avatar Tools** → **Add Hair Physics**. Tiene cuatro partes: Hair Chain Detection, Hair Chain Generation, PhysBone Configuration y Hair Physics Colliders.

---

### Paso 2 — Encontrar las cadenas del cabello {#step-2--find-the-hair-chains}

Si tu cabello ya tiene huesos, selecciona **Detect Hair Physics Chains**. BoneCraft busca cadenas de huesos parecidas al cabello, unidas extremo con extremo desde una raíz. La lista muestra el hueso raíz y la longitud de cada cadena.

Si tu cabello no tiene huesos:

1. Selecciona las mallas del cabello.

2. En Hair Chain Generation, selecciona **Generate**.

3. Configura inmediatamente **Chain Density** como Low, Medium o High en **Adjust Last Operation**.

**Replace** pide confirmación y actualmente crea nuevas cadenas sin eliminar las anteriores.

Antes de volver a generar:

1. Revisa la lista de huesos.

2. Si hay cadenas no deseadas, elimínalas.

---

### Paso 3 — Elegir un preajuste de PhysBone {#step-3--choose-a-physbone-preset}

1. Selecciona un hueso de la cadena.

2. En PhysBone Configuration, selecciona **Hair**, **Skirt** o **Tail**.

Skirt sirve para faldas y capas. Tail sirve para colas y cuerdas.

**Deberías ver:** los parámetros de la cadena: Pull, Spring, Stiffness, Gravity y Max Angle.

---

### Paso 4 — Ajustar con precisión (opcional) {#step-4--fine-tune-optional}

El panel muestra los valores de la cadena, pero no permite editarlos. Mayor Stiffness reduce la flexión. Mayor Gravity tira de la cadena hacia abajo. Un Max Angle menor restringe su balanceo. Para cambiar los valores, selecciona otro preajuste. También puedes editar su componente PhysBone en Unity después de importar el avatar.

---

### Paso 5 — Añadir colisionadores (recomendado) {#step-5--add-colliders-recommended}

Los colisionadores son formas invisibles que impiden que el cabello atraviese la cabeza y el cuerpo. En Hair Physics Colliders, selecciona **Place Default Colliders**. Añade colisionadores a cabeza, hombros y pecho. **Add Collider** y **Remove Collider** añaden o eliminan un colisionador cada vez.

**Lo que esto permite:** el cabello del avatar se mueve con naturalidad en VRChat al girar la cabeza, saltar o bailar. Los mismos pasos sirven para colas, orejas, faldas y accesorios colgantes.

---

## Guía 7: adjuntar ropa que se mueva con tu cuerpo {#guide-7-attach-clothing-that-moves-with-your-body}

> **Tiempo:** unos 20–30 minutos
> **Resultado:** una prenda unida al esqueleto de tu avatar, que se mueve con tu cuerpo

**Antes de empezar, comprueba esto:**

- [ ] Tu avatar base tiene un esqueleto terminado y su cuerpo tiene pesos pintados
- [ ] La prenda está en el mismo archivo (con su propio esqueleto si venía con uno)
- [ ] La prenda encaja aproximadamente alrededor del cuerpo del avatar

---

### Paso 1 — Abrir Attach Clothing {#step-1--open-attach-clothing}

Consulta los [controles de ropa y el orden de selección](08-vrchat.md#attach-clothing).

En **CATS**, despliega **VRChat Tools** y busca el grupo Clothing. Tiene tres partes: Bone Matching, Collision Detection y Clothing Merge.

---

### Paso 2 — Emparejar huesos {#step-2--match-bones}

Si la ropa tiene un esqueleto:

1. Cambia a Object Mode.

2. Selecciona tanto el esqueleto de la ropa como el del avatar.

3. Selecciona **Match Bones** para comparar sus nombres de huesos.

**Deberías ver:** las cantidades de coincidencias HIGH, MEDIUM, LOW y UNMATCHED. El panel no muestra una lista de parejas de huesos. Para ropa sin esqueleto, omite este paso.

Antes de combinar dos esqueletos:

1. Selecciona **Detect Collisions** para comprobar si hay nombres de huesos en conflicto.

2. Revisa los cambios de nombre propuestos.

3. Haz activo el esqueleto de la ropa.

4. Selecciona **Resolve Collisions** para aplicar los cambios de nombre a ese esqueleto.

Detect Collisions comprueba solo nombres. No comprueba intersecciones de mallas.

---

### Paso 3 — Combinar la ropa {#step-3--merge-the-clothing}

1. Si la ropa tiene un esqueleto, selecciona ese esqueleto y sus mallas.

2. Si no tiene esqueleto, selecciona solo sus mallas.

3. Haz Mayús+clic en el esqueleto del avatar en último lugar para activarlo.

4. Selecciona **Merge Clothing**.

Con un esqueleto de ropa, BoneCraft pasa la ropa al esqueleto del avatar y combina los huesos. Sin esqueleto de ropa, transfiere los pesos del cuerpo a las mallas de la prenda.

> Los pesos (pintura de pesos) son números que indican cuánto mueve cada hueso cada punto de una malla. Si la manga izquierda tiene peso en el hueso del brazo izquierdo, mover ese hueso arrastra la manga.

**Deberías ver:** la ropa bajo el esqueleto del avatar. Mover un hueso mueve tanto el cuerpo como la ropa.

---

### Paso 4 — Comprobar atravesamientos {#step-4--check-for-clipping}

1. Coloca el avatar en una pose.

2. Examina los lugares donde la ropa atraviesa el cuerpo.

3. Si hay atravesamientos, ajusta el encaje de la ropa o los pesos en esos lugares.

Consulta Weight Tools en [Herramientas de rig](05-rig-tools.md). **Detect Collisions** no comprueba los atravesamientos físicos.

**Lo que esto permite:** ropa que se mueve con naturalidad con tu cuerpo. Repite para cada pieza del conjunto.

Siguiente: [Guías 8–13](03-guides-b.md)
