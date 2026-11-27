# Rig Builder {#rig-builder}

[← Contenido](index.md)

Para ver una demostración narrada de ambos tipos de rig, consulte la [guía de iniciación a IK/FK y su archivo de práctica](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

## Crear un rig nuevo {#building-a-new-rig}

Rig Builder crea un rig nuevo para un personaje. Su pestaña **Rig Builder** está en el Tool Shelf izquierdo. Pulse **T** para mostrarlo. Cuando Preferences → Tabs → Scene Properties → Show está activado, Rig Builder también aparece en la pestaña **Scene** del editor **Properties**. Si el Tool Shelf es estrecho, utiliza una distribución compacta con etiquetas cortas. Primero aparece Auto-Rig Wizard, seguido de Quick Rig y Mannequin. El menú Add → Armature del visor también ofrece el asistente y Quick Rig.

---

### Auto-Rig Wizard {#auto-rig-wizard}

**Qué hace:** Una guía paso a paso que coloca marcadores en la malla y, a partir de ellos, crea un rig completo con pesos. Es el método principal para crear el rig de un personaje desde cero.

La [Guía 1](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat) explica el proceso paso a paso.

**Pasos:** Select Mesh → Rig Type → Body Markers → Finger Markers → Face Markers → Review → Generate

**Controles principales:**

- **Start Auto-Rig** abre el asistente. **Back** y **Cancel** están arriba. **Next** está al final de los pasos de malla, tipo de rig y marcadores. Review utiliza **Generate Rig** en lugar de Next. El último paso utiliza **Close Wizard**
- La lista de mallas: haga clic aquí en su malla. El siguiente paso ofrece **Body + Face**, **Body Only** o **Face Only** (para una armadura existente)
- **Detect Markers** (en Smart Detection): recorre las extremidades de la malla y coloca todos los marcadores corporales con una valoración de confianza. **Accept High** conserva los marcadores de alta confianza. **Reset Low** borra los de baja confianza
- **Guess Markers from Mesh** y **Guess Precision** (cuerpo), **Guess Finger Markers** (los marcadores de los dedos se colocan a partir de la forma de la mano) y **Guess Face Markers**
- Finger Detail: cuántos dedos se crean, desde "0 — No Fingers" hasta "5 — Full Human Hand"
- La fila de cada marcador: **Place Marker** (icono de flecha), **Confirm Marker** (marca de verificación) y **Reset Marker** (flecha circular). Los marcadores izquierdos y derechos también tienen **Toggle Symmetry** como primer icono
- **Mirror L to R** y **Mirror R to L**: copian los marcadores confirmados al otro lado de la línea central
- **Confirm All Placed**: confirma todos los marcadores colocados en el paso
- **Generate Rig**: crea el rig a partir de los marcadores confirmados. El último paso ofrece **Build Control Rig** (véase más abajo) y **Close Wizard**

**Qué crea Generate Rig:**

- Un rig corporal con los segmentos de columna y cuello elegidos, y brazos y piernas con IK/FK, solo IK o solo FK (opción **Kinematics**)
- Huesos para la cantidad de dedos elegida
- Para **Body + Face**: un rig facial, con formas de control si **Generate Control Shapes** está activado
- Pesos de deformación con la calidad elegida. Las mallas densas se ponderan mediante una malla proxy más ligera, por lo que un personaje de 678,000 vértices (seiscientos setenta y ocho mil) tarda aproximadamente un minuto en lugar de fallar sin avisar.

**Build Control Rig:** el paso de revisión también muestra **Twist Bones**, **Skirt Bones**, **Face Controls** y **Joint Correctives**. Generate Rig no aplica estas opciones. Pertenecen al rig de control del motor. Este rig incluye huesos de torsión, huesos de falda que siguen a las piernas, controles de orientación ocular y parpadeo, y claves de forma correctivas de articulaciones. Después de Generate Rig, el último paso ofrece **Build Control Rig**. Este comando crea el rig de control sobre la armadura generada con las opciones seleccionadas. Antes de **Close Wizard**, haga clic en **Build Control Rig**. Al cerrar, se restablecen las opciones del asistente. El panel Control Layer (Rig Tools) solo aparece en un rig creado de esta manera.

**Dónde encontrarlo:** Rig Builder → Auto-Rig Wizard

**Colocar varios marcadores con la herramienta del visor:**

1. Inicie el asistente.
2. Avance hasta un paso de marcadores corporales, de dedos o faciales.
3. En Object Mode, active Place Rig Markers en la barra de herramientas del visor.

El encabezado de la herramienta indica el siguiente marcador sin confirmar y muestra los bloqueos de ejes y un interruptor de simetría.

4. Haga clic en la malla del asistente para colocar y confirmar ese marcador.
5. Cuando la herramienta indique que el paso ha terminado, pulse **Next** en el asistente.

La simetría sigue los ajustes del asistente. Los botones Place de cada marcador siguen funcionando. Hacer clic en otro sitio no coloca un marcador.

---

### Quick Rig {#quick-rig}

**Qué hace:** Añade Basic Humanoid de BoneCraft o uno de los metarigs de Rigify con un solo clic. Basic Humanoid tiene 19 huesos y no necesita Rigify. Quick Rig es más rápido que el asistente, pero se adapta menos a la malla.

**Controles principales:**

- El botón Basic Humanoid y los metarigs de Rigify. Para un preajuste de Rigify con Rigify desactivado, seleccione primero **Enable Rigify**
- El botón de un rig lo añade inmediatamente. Adjust Last Operation contiene las opciones de ajuste, pesos automáticos, **Add IK/FK Controllers** e **Initial Pose**
- **T-Pose** y **A-Pose**: cambian la pose de reposo del rig seleccionado
- Expanda Troubleshooting para acceder a **Diagnose Quick Rig (print to console)**. Si la armadura activa no es un metarig, también muestra **Inspect Active Rig Controls**
- Si hay un metarig de Rigify activo, Troubleshooting muestra **Generate Control Rig (active metarig)** en lugar de Inspect Active Rig Controls. Esto genera el rig de control de Rigify

**El catálogo inicial BoneCraft Rigs:** los nueve rigs iniciales incluidos comparten un catálogo **Starter Rigs** en el estante nativo de recursos situado abajo.

1. Abra el menú de catálogos a la izquierda del estante.
2. Seleccione **All** para las bibliotecas.
3. Active **Starter Rigs** una vez para añadir su pestaña junto a las de los catálogos existentes.
4. Seleccione esa pestaña para explorar los rigs iniciales.

**Add → Armature → Starter Rig Catalog** abre la ventana emergente que gestiona las dependencias para ajustar y añadir un rig inicial.

Basic Humanoid no necesita Rigify. Las demás miniaturas llevan la etiqueta **Rigify**. Si Rigify está inactivo, al seleccionar o soltar una de ellas en la ventana del catálogo se ofrecen **Enable Rigify & Add Rig** y Cancel. Al aceptar, se activa el Rigify instalado y se continúa con ese rig inicial. Al cancelar, no se añade nada. **Quick Rig** también ofrece **Enable Rigify**. El menú contextual de la ventana del catálogo lo ofrece cuando Rigify no está disponible. Si falta una dependencia o un preajuste, aparece una explicación. La ventana no añade un rig sustituto cuando la versión instalada carece de ese preajuste.

El estante nativo de recursos inferior importa recursos de armadura. Use **Add → Armature → Starter Rig Catalog** para el flujo de trabajo con gestión de dependencias que se describe a continuación.

Si hay una malla seleccionada, la herramienta ajusta el rig inicial a esa malla al añadirlo. En la ventana emergente, haga clic en una miniatura para añadir un rig inicial o arrástrela al visor. Los pesos automáticos y la generación de controles están desactivados inicialmente. Ajuste estas opciones después en **Adjust Last Operation**.

Si no había ninguna malla seleccionada:

1. Seleccione el nuevo rig inicial.
2. En Quick Rig, seleccione **Mesh**.
3. Haga clic en **Fit Dropped Rig**.

El ajuste escala y coloca el esqueleto. Antes de generar controles o pesos:

1. Revise la colocación de las articulaciones.
2. Edítela según sea necesario.

Arrastrar fuera del visor, pulsar Esc o hacer clic con el botón derecho cancela la operación sin añadir nada.

**Dónde encontrarlo:** Rig Builder → Quick Rig; Add → Armature → Quick Rig también añade los rigs predefinidos

---

### Mannequin {#mannequin}

**Qué hace:** Crea una malla de previsualización alrededor de un rig existente para revisar su deformación sin disponer de la malla definitiva del personaje. Si aún no tiene un rig, añada uno con Quick Rig. Antes de usar Mannequin, seleccione la armadura o una malla emparentada con ella. El maniquí es solo una previsualización: sustitúyalo por su propia malla antes del uso final.

**Controles principales:**

- **Quick Mannequin**: crea una previsualización con valores predeterminados fijos y sustituye el maniquí anterior de ese rig
- **Add Mannequin**: crea una previsualización con los ajustes de la escena. Por defecto, sustituye un maniquí existente. Replace Existing se encuentra en Adjust Last Operation después del clic
- **Regenerate**: reconstruye la previsualización existente con sus ajustes guardados
- **Remove**: elimina la malla del maniquí y conserva la armadura
- Options, debajo de los botones, contiene **Mode**, **Body Type**, la densidad y **Radius Scale**. Advanced, dentro de Options, contiene las escalas regionales y los ajustes de salida. Para usar los ajustes de escena modificados, vuelva a hacer clic en **Add Mannequin**

**Dónde encontrarlo:** Rig Builder → Mannequin

---

## Taller del maniquí: instrucciones en texto {#illustrated-mannequin-workshop}

<!-- Keep each illustrated step together and preserve the manual's print scale. -->
<style>
section.chapter:has(#ch-06-rig-builder) img { max-width: 100%; max-height: 155mm; width: auto; height: auto; }
@media print {
  [id="06-rig-builder--illustrated-mannequin-workshop"] { break-before: page; break-after: avoid; }
  h4[id^="06-rig-builder--"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] + h4 { break-before: avoid; }
  section.chapter:has(#ch-06-rig-builder) h4 + p { break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) { break-before: avoid; break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) + p { break-before: avoid; }
}
</style>

Siga estas tres partes en orden:

1. [A — De Simple Human a un maniquí](#part-a-simple-human-to-mannequin).
2. [B — Del maniquí sin rig a Auto-Rig](#part-b-rigless-mannequin-through-auto-rig).
3. [C — Comprobar los pesos y utilizar IK/FK](#part-c-test-weights-and-use-ikfk).

El original inglés proporciona una captura real de la interfaz para cada paso numerado del taller; los números rojos corresponden a sus leyendas. Esas capturas se realizaron con la **versión BoneCraft 9.1.2** en `Bforartists 5.2.0`. Esta edición de solo texto omite las imágenes y conserva los pasos escritos, las descripciones de las imágenes y las leyendas. La distribución de los paneles y los atajos de Blender pueden ser diferentes. Use los comandos por su nombre como referencia.

Las capturas del original inglés, omitidas aquí, conservan sus etiquetas de captura 9.1.2. La navegación actual es **Rig Builder → Quick Rig**, **Rig Builder → Auto-Rig Wizard** y **BoneCraft → Skin → Weight Tools**. Starter Rigs utiliza ahora la pestaña de catálogo nativa inferior. Esta edición de solo texto no afirma que se haya repetido el ejercicio con 9.2.18 ni con 9.2.19.

Este ejercicio produce una previsualización sencilla de cápsulas para aprender a crear rigs. La cabeza, las manos y el torso son provisionales. No es un modelo de personaje terminado. Empiece en un archivo nuevo. Conserve ambos puntos de control guardados para repetir la conversión sin perder el metarig original.

El repositorio incluye ambos puntos de control en `examples/mannequin/`: `SimpleHuman_Mannequin.blend` es el resultado neutro de la Parte A y `Mannequin_AutoRig.blend` es el ejemplo completo y posado de la Parte C, con los pesos corregidos.

### Parte A: de Simple Human a un maniquí {#part-a-simple-human-to-mannequin}

#### A1. Activar Rigify {#a1-enable-rigify}

1. Empiece en una escena nueva.
2. Abra **Scene Properties → Rig Builder → Quick Rig**.
3. Si los preajustes de Rigify no están disponibles, haga clic en **Enable Rigify**.

Este tutorial utiliza el metarig `Simple Human` de Rigify. **BoneCraft Basic Humanoid (19 bones)** es un preajuste diferente.

Descripción de imagen del original inglés (imagen omitida): A1: activar Rigify

*1 — Scene Properties. 2 — Enable Rigify.*

#### A2. Añadir Simple Human {#a2-add-simple-human}

Haga clic en `Simple Human` dentro de Quick Rig. El resultado es un metarig editable, todavía no una malla. Tiene 29 huesos en esta versión.

Descripción de imagen del original inglés (imagen omitida): A2: añadir Simple Human

*1 — Preajuste Simple Human.*

#### A3. Revisar el metarig {#a3-inspect-the-metarig}

1. Mueva el puntero al visor.
2. Pulse `Numpad 1` para Front Orthographic.
3. Compruebe que se ve todo el esqueleto.
4. Use la rueda del ratón para encuadrar el esqueleto.

El nuevo metarig puede iniciarse en Pose Mode.

Descripción de imagen del original inglés (imagen omitida): A3: revisar el metarig

*1 — Vista frontal. 2 — Esqueleto Simple Human.*

#### A4. Volver a Object Mode {#a4-return-to-object-mode}

Antes de cambiar la pose de reposo o generar el maniquí:

1. En el desplegable de modo del visor, seleccione **Object Mode**.
2. Mantenga seleccionado `SimpleHumanArmature`.

Descripción de imagen del original inglés (imagen omitida): A4: volver a Object Mode

*1 — Desplegable de modo. 2 — Object Mode.*

#### A5. Utilizar una pose en T {#a5-use-a-t-pose}

En Quick Rig, haga clic en **T-Pose**. Los brazos se extienden horizontalmente. Para un cuerpo personalizado, ajuste el metarig en Edit Mode antes de generar su previsualización. En este ejercicio, mantenga simétricas las articulaciones de ambos lados.

Descripción de imagen del original inglés (imagen omitida): A5: utilizar una pose en T

*1 — Comando T-Pose.*

#### A6. Generar el maniquí {#a6-generate-the-mannequin}

1. Expanda **Mannequin → Options**.
2. Establezca `Mode: Universal`.
3. Establezca `Body Type: Neutral`.
4. Seleccione **Medium**.
5. Establezca `Radius Scale: 1.00`.
6. En Advanced, mantenga las escalas regionales en 1.00.
7. Seleccione `Joined (non-manifold)`.
8. Seleccione **Flat colour**.
9. Active **Joint Smoothing**.
10. Deje Unified Volume desactivado.
11. Haga clic en **Add Mannequin**.

La captura omitida del original inglés muestra la malla de cápsulas resultante. Add usa las opciones actuales. Regenerate reutiliza los ajustes guardados del maniquí.

Descripción de imagen del original inglés (imagen omitida): A6: generar el maniquí

*1 — Add Mannequin. 2 — Universal y ajustes del cuerpo. 3 — Salida Joined y suavizado.*

#### A7. Probar una pose de hueso {#a7-try-a-bone-pose}

En la vista frontal, el lado izquierdo del personaje está a su derecha.

1. Seleccione la armadura.
2. Cambie a **Pose Mode**.
3. Haga clic en el hueso del antebrazo izquierdo.
4. Con la herramienta Rotate, gire el hueso ligeramente.

El maniquí conectado lo sigue. Es una previsualización con pesos sobre el metarig. Todavía no tiene los controles de animación que se usan en la Parte C.

Descripción de imagen del original inglés (imagen omitida): A7: probar una pose de hueso

*1 — Pose Mode. 2 — Antebrazo seleccionado y su manipulador de transformación.*

#### A8. Restaurar y guardar la previsualización {#a8-restore-and-save-the-preview}

1. Con el puntero en el visor, seleccione todos los huesos de pose.
2. Pulse **F3**.
3. Busque `Clear Pose Transforms`.
4. Seleccione **All**.
5. Confirme que el maniquí vuelve a su pose en T.
6. Abra **File → Save As**.
7. Guarde el archivo como `SimpleHuman_Mannequin.blend`.

Conserve este punto de control antes de continuar.

Descripción de imagen del original inglés (imagen omitida): A8: restaurar y guardar la previsualización

*1 — Búsqueda de Clear Pose Transforms. 2 — All restablece los huesos de pose seleccionados.*

### Parte B: del maniquí sin rig a Auto-Rig {#part-b-rigless-mannequin-through-auto-rig}

#### B1. Seleccionar la malla del maniquí {#b1-select-the-mannequin-mesh}

Continúe desde el punto de control neutro de la Parte A. En esta parte se retira deliberadamente el rig del maniquí antes de ejecutar el asistente.

1. Cambie a **Object Mode**.
2. En el Outliner, seleccione `SimpleHumanArmature_Mannequin`.

Para conservar la Parte A, guarde el resultado con otro nombre de archivo.

Descripción de imagen del original inglés (imagen omitida): B1: seleccionar la malla del maniquí

*1 — Seleccione la malla, no la armadura.*

#### B2. Convertir la previsualización en una malla {#b2-bake-the-preview-into-a-mesh}

Mantenga el maniquí en su pose en T restaurada. Mantenga seleccionado únicamente el maniquí.

1. Pulse **F3**.
2. Busque `Convert Mesh`.
3. Ejecute `Convert Mesh`.

Esto conserva la geometría neutra visible y elimina el modificador Armature.

Descripción de imagen del original inglés (imagen omitida): B2: convertir la previsualización en una malla

*1 — Comando Convert Mesh.*

#### B3. Eliminar la relación de parentesco {#b3-clear-the-parent}

1. Pulse **Alt+P**.
2. Seleccione `Clear and Keep Transformation`.

Esto desvincula la malla del metarig anterior sin moverla.

Descripción de imagen del original inglés (imagen omitida): B3: eliminar la relación de parentesco

*1 — Clear and Keep Transformation.*

#### B4. Eliminar los pesos anteriores {#b4-remove-the-old-weights}

Esta acción es para esta malla de práctica desechable. Los grupos pertenecen al metarig anterior. El asistente creará grupos nuevos.

1. Abra **Object Data Properties → Vertex Groups**.
2. En el menú desplegable de la lista, seleccione `Delete All Groups`.

Descripción de imagen del original inglés (imagen omitida): B4: eliminar los pesos anteriores

*1 — Menú Vertex Groups. 2 — Delete All Groups.*

#### B5. Verificar el punto de control sin rig {#b5-verify-the-rigless-checkpoint}

1. Oculte el antiguo `SimpleHumanArmature` con su icono de ojo en el Outliner.
2. Compruebe que el maniquí sigue visible.
3. Compruebe que su panel Modifiers no contiene ningún modificador Armature.
4. Compruebe que su lista Vertex Groups está vacía.

Esta es la malla de entrada del maniquí sin rig. BoneCraft 9.1.2 genera maniquíes a partir de una armadura. Al desvincular esta previsualización, se obtiene una malla de práctica sin rig.

Descripción de imagen del original inglés (imagen omitida): B5: verificar el punto de control sin rig

*1 — Oculte el metarig anterior. 2 — Pila de modificadores vacía.*

#### B6. Activar la pestaña Rig Builder del visor {#b6-enable-the-viewport-rig-builder-tab}

En el programa anfitrión probado con 9.1.2, Place Marker iniciado desde Scene Properties no aceptaba clics en el visor. Use la pestaña del visor para colocar los marcadores.

1. Abra **Edit → Preferences → Add-ons → BoneCraft → Tabs**.
2. Active **Rig Builder**.
3. Seleccione **Left**.
4. Cierre Preferences.
5. Sitúe el puntero sobre el visor.
6. Si el Tool Shelf izquierdo está oculto, pulse **T**.

Descripción de imagen del original inglés (imagen omitida): B6: activar la pestaña Rig Builder del visor

*1 — Active Rig Builder. 2 — Colocación en el Tool Shelf izquierdo.*

#### B7. Iniciar Auto-Rig {#b7-start-auto-rig}

Con el maniquí sin rig seleccionado, haga clic en **Start Auto-Rig**. La captura omitida del original inglés muestra el botón equivalente de Scene Properties. La pestaña Rig Builder del visor, activada en el paso anterior, tiene el mismo comando en la parte superior.

Descripción de imagen del original inglés (imagen omitida): B7: iniciar Auto-Rig

*1 — Start Auto-Rig.*

#### B8. Elegir la malla de entrada {#b8-choose-the-input-mesh}

No seleccione un widget ni otro objeto de previsualización.

1. En `Select Mesh`, seleccione el maniquí.
2. Verifique la marca de comprobación de malla seleccionada.
3. Haga clic en **Next**.

Descripción de imagen del original inglés (imagen omitida): B8: elegir la malla de entrada

*1 — Maniquí de entrada. 2 — Next.*

#### B9. Elegir un rig corporal con ambos métodos {#b9-choose-a-body-rig-with-both-methods}

Este maniquí de cápsulas no tiene topología facial, por lo que Body + Face es innecesario.

1. Seleccione **Body Only**.
2. Seleccione `Kinematics: IK + FK`.
3. Mantenga activado **Generate Control Shapes**.
4. Haga clic en **Next**.

Descripción de imagen del original inglés (imagen omitida): B9: elegir un rig corporal con ambos métodos

*1 — Body Only. 2 — IK + FK. 3 — Next.*

#### B10. Detectar los marcadores corporales iniciales {#b10-detect-initial-body-markers}

Las estimaciones de detección son un punto de partida. No las acepte sin revisarlas.

1. Para este maniquí simétrico, mantenga activado **Mirror Symmetry**.
2. En Body Markers, haga clic en **Detect Markers** dentro de Smart Detection.

Descripción de imagen del original inglés (imagen omitida): B10: detectar los marcadores corporales iniciales

*1 — Detect Markers. 2 — Mirror Symmetry.*

#### B11. Revisar las posiciones detectadas {#b11-review-the-detected-positions}

Esta previsualización segmentada produce varias estimaciones de baja confianza. Antes de generar:

1. Compare la parte superior de la cabeza, la base del cuello, la pelvis, las muñecas y los tobillos con la malla visible.
2. Revise los puntos de referencia principales y los de precisión opcionales.
3. Corríjalos según sea necesario.

Las etiquetas de confianza describen la detección original. Una marca verde al comienzo de una fila indica que la colocación actual está confirmada.

Descripción de imagen del original inglés (imagen omitida): B11: revisar las posiciones detectadas

*1 — Resumen de confianza de la detección. 2 — Filas de marcadores corporales.*

#### B12. Colocar una muñeca en la malla {#b12-place-a-wrist-on-the-mesh}

En vista frontal, la muñeca izquierda del personaje está a la derecha de la pantalla.

1. Si el marcador ya está confirmado, restablezca su fila para mostrar el botón de colocación.
2. En la pestaña **Rig Builder** del visor, haga clic en el cuentagotas **Place Marker** de Wrist Left.
3. Haga clic en la superficie de la muñeca en el visor.

Descripción de imagen del original inglés (imagen omitida): B12: colocar una muñeca en la malla

*1 — Control de colocación Wrist Left. 2 — Haga clic en la superficie de la muñeca.*

#### B13. Comprobar la muñeca reflejada y los tobillos {#b13-check-the-mirrored-wrist-and-ankles}

1. Verifique que ambas filas de muñeca muestran marcas verdes y coordenadas X opuestas.
2. Repita la colocación de `Ankle Left` en su articulación, no en los dedos del pie.

La simetría coloca Ankle Right. Compruebe la simetría con respecto a la malla. No copie las coordenadas del ejemplo a un personaje de otro tamaño.

Descripción de imagen del original inglés (imagen omitida): B13: comprobar la muñeca reflejada y los tobillos

*1 — Par de muñecas confirmado. 2 — Muñeca reflejada en la malla.*

#### B14. Afinar hombros y codos {#b14-refine-shoulders-and-elbows}

1. Desplácese hasta Precision Markers.
2. Restablezca `Shoulder Left`.
3. Coloque `Shoulder Left` en el pivote del brazo.
4. Restablezca `Elbow Left`.
5. Coloque `Elbow Left` en el hueco del codo.
6. Confirme sus parejas reflejadas.
7. Mantenga la muñeca en el extremo del antebrazo que corresponde a la mano.

Estos puntos determinan la cadena del brazo. Corrija cualquier hombro o codo estimado en la cápsula equivocada.

Descripción de imagen del original inglés (imagen omitida): B14: afinar hombros y codos

*1 — Filas de marcadores de hombro y codo. 2 — Hombro. 3 — Codo.*

#### B15. Afinar caderas y rodillas {#b15-refine-hips-and-knees}

1. Coloque `Hip Left` en la parte superior del muslo.
2. Coloque `Knee Left` en el hueco entre muslo y espinilla.
3. Compruebe el lado opuesto colocado por simetría.
4. Mantenga la pelvis en la línea central, entre las caderas.

Descripción de imagen del original inglés (imagen omitida): B15: afinar caderas y rodillas

*1 — Filas de cadera y rodilla. 2 — Superficie de la cadera. 3 — Hueco de la rodilla.*

#### B16. Comprobar la profundidad y los dedos del pie desde un lado {#b16-check-depth-and-toes-from-the-side}

1. Con el puntero sobre el visor, pulse `Numpad 3`.
2. Compruebe los puntos de referencia tanto en Right Orthographic como desde el frente.
3. Coloque `Toe Left` cerca de la parte delantera del pie.
4. Verifique su pareja reflejada.

Un marcador puede parecer correcto desde el frente y, sin embargo, estar demasiado adelantado o detrás del cuerpo.

Descripción de imagen del original inglés (imagen omitida): B16: comprobar la profundidad y los dedos del pie desde un lado

*1 — Right Orthographic. 2 — Fila del marcador del dedo del pie. 3 — Superficie del pie.*

#### B17. Colocar los talones {#b17-place-the-heels}

1. Si la posición estimada de un talón es incorrecta, restablezca ese talón.
2. En vista lateral, coloque `Heel Left` cerca de la parte posterior del pie.
3. Verifique Heel Right.

Estos marcadores son opcionales. Dejar ambos en cero produjo una advertencia de proximidad en la versión probada. Colocarlos en los pies eliminó esa advertencia.

Descripción de imagen del original inglés (imagen omitida): B17: colocar los talones

*1 — Par de talones confirmado. 2 — Posición del talón.*

#### B18. Confirmar y continuar {#b18-confirm-and-continue}

1. Revise la parte superior de la cabeza, la base del cuello y la pelvis, así como todos los pares de puntos de referencia.
2. Haga clic en **Confirm All Placed**.
3. Haga clic en **Next**.

Las marcas verdes junto a los nombres muestran el estado de confirmación. Las etiquetas de confianza originales REVIEW/ADJUST pueden seguir visibles en 9.1.2.

Descripción de imagen del original inglés (imagen omitida): B18: confirmar y continuar

*1 — Confirm All Placed. 2 — Next.*

#### B19. Omitir los dedos de las manos en esta malla {#b19-skip-fingers-for-this-mesh}

Este maniquí tiene cápsulas para las manos, pero no geometría de dedos.

1. Seleccione `0 — No Fingers`.
2. Haga clic en **Next**.

Si utiliza una malla de mano real en su lugar:

1. Seleccione la cantidad de dedos adecuada.
2. Coloque los marcadores de los dedos.

Descripción de imagen del original inglés (imagen omitida): B19: omitir los dedos de las manos en esta malla

*1 — No Fingers. 2 — Next.*

#### B20. Revisar y generar {#b20-review-and-generate}

Antes de continuar, exija el estado **All checks passed**. Estos ajustes corresponden a este sencillo maniquí de práctica. No son requisitos universales de exportación.

1. Seleccione **IK + FK**.
2. Active las formas de control.
3. Establezca `Spine Segments: 3`.
4. Establezca `Neck Segments: 1`.
5. Seleccione `No Fingers`.
6. Seleccione **Game Ready**.
7. Desactive Twist Bones.
8. Desactive Skirt Bones.
9. Desactive Preserve Volume.
10. Desactive Joint Correctives.
11. Haga clic en **Generate Rig**.

Descripción de imagen del original inglés (imagen omitida): B20: revisar y generar

*1 — Comprobaciones de marcadores. 2 — Ajustes de generación. 3 — Generate Rig.*

#### B21. Crear los controles de animación {#b21-build-the-animator-controls}

Después de generar, haga clic en **Build Control Rig**. Generate Rig proporciona el rig corporal y los pesos. Build Control Rig añade la capa de control que se utiliza más adelante. La malla de entrada ya está presente, aunque el panel de finalización muestre su oferta genérica de un maniquí. No vuelva a hacer clic en Quick Mannequin.

Descripción de imagen del original inglés (imagen omitida): B21: crear los controles de animación

*1 — Build Control Rig.*

#### B22. Finalizar el asistente {#b22-finish-the-wizard}

1. Espere el mensaje de finalización del rig de control.
2. Haga clic en **Close Wizard**.
3. Mantenga oculto el metarig Simple Human anterior.

La nueva armadura aparece en el Outliner. El nuevo rig debe deformar la malla. Que los huesos sean visibles no demuestra por sí solo que la deformación funcione.

Descripción de imagen del original inglés (imagen omitida): B22: finalizar el asistente

*1 — El botón de creación está ahora desactivado. 2 — Close Wizard.*

### Parte C: comprobar los pesos y utilizar IK/FK {#part-c-test-weights-and-use-ikfk}

En la versión probada, la armadura generada tiene este nombre de objeto (úselo en el Outliner y en la herramienta de pesos):

```text
BoneForge_Rig
```

`FK (Forward Kinematics)` transmite las rotaciones a lo largo de una jerarquía. La rotación del brazo afecta al antebrazo y, después, a la mano. Es útil para movimientos amplios y extremidades que se mueven libremente. `IK (Inverse Kinematics)` parte de un extremo. Cuando mueve un objetivo de muñeca o tobillo, el solucionador flexiona la cadena para alcanzarlo. Es útil para pies apoyados y manos que deben llegar a una superficie.

| Tarea | Control que debe utilizar | Qué observar |
|---|---|---|
| Balancear un brazo | Controles FK de hombro y codo | Los controles hijos siguen a su padre |
| Colocar una mano | Objetivo IK de la muñeca | El hombro y el codo se resuelven hacia el objetivo |
| Apoyar un pie | Objetivo IK del tobillo de esa pierna | Mueva el cuerpo mientras el objetivo, dentro del alcance, permanece colocado |
| Orientar la flexión de un codo o una rodilla | Control de polo IK | El polo establece la dirección de flexión; no es el objetivo de muñeca o tobillo |
| Cambiar de método | Botones IK/FK de la extremidad | Compruebe la pose ajustada antes de insertar claves de animación |

El siguiente ejercicio compara un brazo en ambos modos. Cada extremidad tiene su propio interruptor. `Bake IK / Bake FK` son herramientas de conversión de animación. Cambiar una sola pose no sustituye el horneado ni la inserción de claves de una animación. Consulte [Control Layer](05-rig-tools.md#control-layer-ikfk) para los demás controles.

#### C1. Abrir la capa de control {#c1-open-the-control-layer}

1. Seleccione la **armadura generada**.
2. Seleccione **Pose Mode**.
3. Abra **BoneCraft → Review → Control Layer**.
4. Seleccione **arm-L → FK**.

Cada brazo y cada pierna tiene su propio interruptor IK/FK. Izquierda y derecha se refieren al personaje. En vista frontal, arm-L aparece a su derecha.

Descripción de imagen del original inglés (imagen omitida): C1: abrir la capa de control

*1 — Pose Mode. 2 — Control Layer e interruptor arm-L.*

#### C2. Mostrar los controles de animación {#c2-show-the-animator-controls}

1. Abra **Object Data Properties → Bone Collections** de la armadura.
2. Seleccione la estrella Solo de `Controls`.
3. Seleccione la estrella Solo de **FK**.
4. Si la malla oculta los controles, active **In Front** en Viewport Display.
5. Cuando utilice objetivos más adelante, incluya **IK**.

Las selecciones Solo aíslan esas formas de control. Esta lista nativa de colecciones también funciona si el panel Collections de BoneCraft no se dibuja en este programa anfitrión.

Descripción de imagen del original inglés (imagen omitida): C2: mostrar los controles de animación

*1 — Estrellas Solo de Controls y FK. 2 — In Front.*

#### C3. Seleccionar el control FK del antebrazo {#c3-select-the-forearm-fk-control}

1. En vista frontal, haga clic en el control circular del codo izquierdo del personaje.
2. Compruebe que el nombre de la selección del visor es **forearm.fk-L**.

Un control FK de antebrazo gira alrededor del codo. Seleccionar el control del hombro giraría, en cambio, el brazo y sus hijos.

Descripción de imagen del original inglés (imagen omitida): C3: seleccionar el control FK del antebrazo

*1 — Control forearm.fk-L seleccionado. 2 — FK está activo para arm-L.*

#### C4. Girar y revisar la deformación {#c4-rotate-and-inspect-the-deformation}

El objetivo es una rotación aproximada de `−45°` alrededor del eje **Y** global para este ejemplo en vista frontal. Use uno de estos métodos:

- Con la herramienta Rotate, gire el control FK seleccionado.
- Para el mapa de teclas de Bforartists mostrado, siga estos pasos:

1. Pulse **Ctrl+E**.
2. Pulse **Y**.
3. Escriba **-45**.
4. Pulse **Enter**.

El atajo de rotación predeterminado de Blender es **R**. La captura omitida del original inglés muestra deliberadamente el problema inicial de los pesos: la cápsula del brazo se inclina junto con el antebrazo. No acepte esto como un rig terminado.

Descripción de imagen del original inglés (imagen omitida): C4: girar y revisar la deformación

*1 — Movimiento incorrecto del brazo durante la prueba FK.*

#### C5. Recalcular los pesos del maniquí {#c5-recalculate-the-mannequin-weights}

Si la prueba de pose anterior falla, siga estos pasos:

1. Cambie a **Object Mode**.
2. Seleccione la malla.
3. Abra **BoneCraft → Skin → Weight Tools → Automatic Bone Weight Recalculation**.
4. Establezca el maniquí en Mesh to Reweight.
5. Establezca la **armadura generada** en Existing Armature.
6. Seleccione **Body**.
7. Seleccione `Body Method: Bone Heat`.
8. Establezca `New Weight Strength: 1.00`.
9. Establezca `Smooth Passes: 0`.
10. Establezca `Max Bones per Vertex: 0`.
11. Establezca `Minimum Weight: 0.001`.
12. Mantenga activado **Keep Weight Backup**.
13. Ejecute **Automatic Bone Weight Recalculation**.

Esto corrigió la previsualización segmentada en la versión probada.

Descripción de imagen del original inglés (imagen omitida): C5: recalcular los pesos del maniquí

*1 — Malla y armadura. 2 — Bone Heat. 3 — Ajustes de sustitución y copia de seguridad. 4 — Recalcular.*

#### C6. Verificar la flexión FK corregida {#c6-verify-the-repaired-fk-bend}

1. Vuelva a seleccionar la armadura generada.
2. Vuelva a **Pose Mode**.

Ahora el brazo debe permanecer horizontal desde el hombro hasta el codo, mientras el antebrazo se eleva desde el codo. El objeto oculto `WEIGHTS_BACKUP_…` conserva los pesos anteriores. Antes de animar su propio personaje, pruebe también las demás extremidades. Un esqueleto generado no demuestra por sí solo que los pesos de deformación sean correctos.

Descripción de imagen del original inglés (imagen omitida): C6: verificar la flexión FK corregida

*1 — El brazo permanece en su sitio. 2 — El antebrazo se flexiona en el codo.*

#### C7. Cambiar el mismo brazo a IK {#c7-switch-the-same-arm-to-ik}

Haga clic en **arm-L → IK**. El cambio ajusta el objetivo a la pose actual, por lo que el brazo debe permanecer elevado. Si los objetivos están ocultos, añada **IK** a las colecciones Solo visibles. El cambio modifica qué controles dirigen la cadena. No registra una animación nueva.

Descripción de imagen del original inglés (imagen omitida): C7: cambiar el mismo brazo a IK

*1 — Interruptor IK de arm-L. 2 — La pose se mantiene al cambiar.*

#### C8. Seleccionar el objetivo IK de la muñeca {#c8-select-the-wrist-ik-target}

1. Haga clic en el control de la muñeca.
2. Compruebe que el nombre de la selección es **forearm.ik-L**.

A pesar de su nombre de antebrazo, este es el objetivo del extremo de la cadena del brazo. Mueva este objetivo para colocar la mano. El solucionador cambia los ángulos del hombro y del codo para alcanzar el objetivo.

Descripción de imagen del original inglés (imagen omitida): C8: seleccionar el objetivo IK de la muñeca

*1 — Objetivo de muñeca seleccionado. 2 — Nombre de la selección.*

#### C9. Mover el objetivo y comparar {#c9-move-the-target-and-compare}

Mantenga el objetivo dentro del alcance del brazo. El objetivo del ejercicio es mover ligeramente el objetivo de muñeca hacia dentro, a lo largo del eje **X** global. En este ejemplo, `−0.15 m` produce una flexión visiblemente distinta. Use uno de estos métodos:

- Arrastre la flecha X de la herramienta Move.
- Para el mapa de teclas mostrado, siga estos pasos:

1. Pulse **Ctrl+W**.
2. Pulse **X**.
3. Escriba `-0.15`.
4. Pulse **Enter**.

El atajo de movimiento predeterminado de Blender es **G**. Compare todo el brazo con el ejemplo FK. El extremo dirige el movimiento y ambos segmentos del brazo lo siguen.

Descripción de imagen del original inglés (imagen omitida): C9: mover el objetivo y comparar

*1 — Extremo de la muñeca. 2 — La cadena responde. 3 — Movimiento X del ejemplo.*

#### C10. Volver a FK y guardar el ejemplo {#c10-switch-back-and-save-the-example}

1. Vuelva a hacer clic en **arm-L → FK**.

Los controles FK se ajustan a la pose IK actual.

2. Verifique que la malla no salta.
3. Abra **File → Save As**.
4. Guarde `Mannequin_AutoRig.blend`.

La captura omitida del original inglés muestra el ejemplo guardado con FK activo. Para una copia de práctica neutra:

1. Mantenga las cuatro extremidades en FK.
2. Seleccione todos los controles de pose visibles.
3. Pulse **F3**.
4. Busque `Clear Pose Transforms`, como en la Parte A.
5. Seleccione **All**.
6. Guarde la copia neutra con otro nombre.

Descripción de imagen del original inglés (imagen omitida): C10: volver a FK y guardar el ejemplo

*1 — FK activo de nuevo. 2 — Pose conservada. 3 — Nombre del archivo guardado.*

**Comprobación final:** La previsualización del metarig original sigue guardada. El maniquí desvinculado tiene un nuevo rig corporal y controles. Los pesos de la previsualización están corregidos. Ha comparado una rotación FK con un movimiento de objetivo IK. Conserve el rig guardado como ejemplo de aprendizaje. Para producción, sustituya la previsualización por una geometría de personaje adecuada.

---

### Retargeting de animación {#animation-retargeting}

La transferencia de animación de un esqueleto a otro se explica en [Rig Tools: Retarget](05-rig-tools.md#retarget).

Consulte la [imagen de Retarget](05-rig-tools.md#retarget) para sus controles de clips.

---

## Bone Merge {#bone-merge}

**Qué hace:** Combina dos armaduras en una, por ejemplo un rig corporal y uno de ropa o pelo, y conserva todos los pesos.

La [Guía 11](03-guides-b.md#guide-11-merge-two-rigs-together) explica el proceso paso a paso.

**Las tres etapas:**

- Scope: selección de las dos armaduras y revisión de sus diferencias
- Rename: resolución de conflictos de nombres e identificación de huesos nuevos
- Merge: previsualización seguida de la fusión final

**Controles principales:**

- **Base**: la armadura que permanece. La otra se fusiona con ella y después se oculta
- **Analyze**: compara los dos esqueletos. **Acknowledge Scope — Proceed to Rename** abre la etapa 2
- **Normalize Both Armatures**: cambia los nombres de los huesos estándar de ambos rigs a una misma convención (Mixamo Prefixed, Mixamo Stripped o personalizada)
- **Auto-Propose Renames**: propone nombres para los huesos propios del rig que se fusiona
- **Apply Rename**: cambia el nombre de una entrada (un paso de deshacer). **Apply Batch Pattern** cambia muchos nombres mediante un patrón (con `{bone}`, `{side}` y `{index}`)
- **Mark as Unique**: conserva un hueso como nuevo en lugar de fusionarlo
- **Verify Rename — Proceed to Merge**: abre la etapa 3
- **Run Merge Preview**: informa de lo que haría la fusión sin modificar nada
- **Merge Armatures**: crea copias de seguridad de ambas armaduras y las fusiona

**Dónde encontrarlo:** BoneCraft → Setup Rigging → Bone Merge

Descripción de imagen del original inglés (imagen omitida): Bone Merge comienza con Stage 1: Scope. Las etapas posteriores permanecen bloqueadas hasta completar las comprobaciones previas.

*Ventana emergente del panel nativo, BoneCraft 9.2.18. Bone Merge comienza con Stage 1: Scope. Las etapas posteriores permanecen bloqueadas hasta completar las comprobaciones previas.*

Siguiente: [Mechanisms](07-mechanisms.md)
