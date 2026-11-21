# Mechanisms {#mechanisms}

[← Índice](index.md)

## Qué hace Mechanisms {#what-mechanisms-does}

Mechanisms crea rigs mecánicos a partir de piezas de superficie rígida. Admite bisagras, deslizamientos, telescopios, pistones, engranajes, seguidores y transformaciones completas controladas por un deslizador. Crea huesos y restricciones normales de Blender. Puedes examinar y modificar todo lo que crea. El rig funciona en Blender sin scripts. Los motores reciben los huesos `DEF-`. La exportación de movimiento mecánico horneado a motores llegará más adelante (consulta Límites de esta versión).

BoneCraft aporta las herramientas. Tú aportas las piezas del arma.

Un ejemplo completo con pasos escritos y descripciones de imágenes conservadas del original en inglés es [Tutorial: Crescent Rose con Mechanisms](12-crescent-rose.md).

Términos de los paneles y esta página:

| Término | Significado |
|---|---|
| *Part* | Pieza que se mueve como un bloque sólido: un objeto o un trozo suelto de una malla. Puede ir montada sobre otra pieza. |
| *Joint* | Cómo puede moverse una pieza: Hinge (gira), Slide (se desplaza), Telescope (extiende segmentos encajados). |
| *Link* | Lo que mueve una pieza: Piston, Gear Link, Follow. |
| *Handle* | Hueso de control que arrastras en la vista. Cada articulación tiene uno. Su valor también aparece como deslizador del panel. |
| *Sequence* | Transformación reproducida con un deslizador y formada por pasos. |
| *Form* | Conjunto guardado de valores de controles y Sequence, como «Stowed» o «Rifle». |

## Dónde está {#where-it-is}

- **Pestaña BoneCraft → Mechanisms** en la Vista 3D. BoneCraft está en la Tool Shelf izquierda (pulsa **T**) salvo que la hayas movido a la barra lateral derecha (**N**) en Preferences. Está entre Skin y Review. Se muestra con una malla activa (para empezar un rig) o un esqueleto activo con mecanismos. De lo contrario, explica qué seleccionar.
- **Editor Properties → pestaña Scene → Mechanisms**, justo después de Rig Builder. Aparece mientras Preferences → Tabs → Scene Properties → Show está activado. Sin selección utilizable muestra: «Select a mesh to start, or an armature with mechanisms.» Desactivar la pestaña de la vista BoneCraft no lo elimina. El interruptor Scene Properties oculta solo la copia Scene. El interruptor de herramienta `mechanisms` (**Preferences → Add-ons → BoneCraft → Tools**) elimina la herramienta de todas las ubicaciones. Las secciones Scene empiezan contraídas: haz clic en **Mechanisms** para desplegarla.
- **Menú Object → Mechanisms** ofrece accesos para añadir piezas, articulaciones y vínculos y probar movimiento.
- **Barra de herramientas de la vista → Build Mechanism** inicia una articulación o vínculo guiado al pulsar una pieza en Modo Objeto o Pose.

Para preparar Build Mechanism:

1. Añade las piezas.
2. Selecciona el rig del mecanismo o una de sus piezas.
3. En la cabecera de la herramienta, selecciona el tipo.

Mechanisms tiene cuatro subsecciones: **1. Parts**, **2. Joints & Links**, **3. Sequences** y **4. Controls**. Aparecen cuando el rig tiene piezas. Antes solo ves **Add Parts from Selection**.

Cada botón es un paso de deshacer. Si una construcción falla, BoneCraft restaura todo lo que cambió y el panel muestra el motivo.

Descripción de imagen del original en inglés (imagen omitida): Mechanisms en la pestaña BoneCraft.

*Captura histórica del taller. Mechanisms en la pestaña BoneCraft.*

## Piezas {#parts}

1. Selecciona los objetos de las piezas (o una malla de trozos sueltos) en Modo Objeto.
2. Haz clic en **Add Parts from Selection**.
    - Varios objetos: una pieza por objeto. Cada objeto queda emparentado al hueso de su pieza y permanece en su sitio.
    - Una malla con trozos sueltos: una pieza por trozo. Cada trozo recibe un grupo de vértices para su hueso y la malla recibe un modificador Armature.
    - La primera vez, BoneCraft crea el rig (un esqueleto).
3. Selecciona una pieza en la lista para editarla.

Para cada pieza:

- **Rides on:** elige la pieza con la que se mueve. Una pieza hija sigue a su padre. «the rig» significa que sigue la raíz del rig.
- **Size** fija la longitud del hueso, que determina el tamaño del control.
- **Edit Pivot** coloca un marcador sobre la pieza. **Apply Pivot** mueve sus huesos al marcador. El objeto permanece en su sitio.
- **Apply Transforms** aparece si una pieza de objeto tiene rotación o escala sin aplicar. Las transformaciones sin aplicar inclinan los ejes. Cuando aparezca, pulsa **Apply Transforms**.
- **X** elimina la pieza. Se niega si una articulación, vínculo u otra pieza la usa y los identifica.
- **Merge for VRChat** necesita dos o más piezas de objeto. Combina solo piezas vinculadas exclusivamente al rig del mecanismo. Hazlo al final. Une las piezas de objeto en una malla con un grupo de vértices por antiguo objeto y un modificador Armature. Las piezas unidas pasan a ser trozos sueltos de esa malla. Elimina los grupos de vértices con nombres de huesos de este esqueleto, excepto el hueso `DEF-` propio de la pieza.

Para cambiar el pivote de una pieza:

1. Selecciona **Edit Pivot**.
2. Arrastra el marcador al lugar desde el que debe girar o deslizarse.
3. Haz clic en **Apply Pivot**.

Puedes renombrar el objeto de una pieza: las piezas están etiquetadas en sus objetos y vuelven a encontrarlos. Una copia del objeto (Shift+D) no se apropia de la pieza. Si se elimina su objeto, muestra «Part '&lt;name&gt;' is missing» con **Reassign** y **Delete**. Los demás mecanismos siguen funcionando.

- **Reassign** usa la malla seleccionada. Rechaza un objeto que no sea malla o que ya use otra pieza de objeto. Los trozos sueltos de una malla pueden compartirla.
- **Delete** elimina la pieza (consulta más abajo cuándo se rechaza).

Descripción de imagen del original en inglés (imagen omitida): piezas añadidas y controles de pivote de la pieza seleccionada.

Descripción de imagen del original en inglés (imagen omitida): piezas añadidas y controles de pivote de la pieza seleccionada.

*Captura histórica del taller. Piezas añadidas y controles de pivote de la pieza seleccionada.*

## Articulaciones y vínculos: un ejemplo de cada {#joints-and-links-one-example-each}

**Add Joint** inicia una construcción guiada de articulación. **Add Link** inicia una de vínculo. Funcionan desde la pestaña de la vista y Scene de Properties. Desde Scene, la guía usa la Vista 3D más grande de la pantalla.

También puedes usar la barra de herramientas:

1. Activa Build Mechanism en la barra de herramientas de la vista.
2. En su cabecera, selecciona el tipo de articulación o vínculo.
3. Haz clic en su primera pieza.

Ese clic inicia la misma guía y aporta la primera selección. Continúa con las selecciones y ejes solicitados en la vista. Los menús Add Joint y Add Link siguen disponibles.

**Align to Selection** admite bisagras inclinadas. Necesita la malla de la pieza en Modo Edición con una arista o cara seleccionada al pulsar **A**. La guía ignora **Tab**. Antes de usarla, prepara la malla:

1. Entra en Modo Edición en la malla de la pieza.
2. Selecciona una arista o cara.
3. Sin salir de Modo Edición, inicia **Add Joint → Hinge**.
4. Haz clic en la pieza.
5. Pulsa **A**.

Si no hay selección utilizable, la guía muestra un mensaje. Puedes pulsar otra tecla.

Reglas breves de toda construcción guiada:

- Haz clic en las piezas de la vista. Reciben un contorno y un número.
- Si un paso necesita un eje, pulsa **X**, **Y** o **Z**.
- Con **Align to Selection** preparado como arriba, pulsa **A** para alinearte a la selección.
- El último paso previsualiza el movimiento en bucle. **Enter** lo conserva. **Esc** lo elimina.
- La cabecera y la barra de estado muestran una frase completa por paso. Con Show Helpers desactivado muestran una etiqueta breve.

Cada fila de Joints & Links tiene cuatro iconos: **Test** (triángulo), **Edit** (lápiz; muestra ajustes), **Detach** (cadena rota) y **Delete** (X).

Después de construir, el elemento seleccionado muestra solo los ajustes de su tipo.

### Hinge {#hinge}

Blade Hinge, 0°…90°:

1. Usa Add Parts from Selection con una pieza Blade.
2. Selecciona **Add Joint → Hinge**.
3. Haz clic en Blade.
4. Pulsa **X**.
5. Pulsa **Enter**.

Crea un control semicircular, `CTRL-Blade`, y una *Blade Hinge* en la lista.

6. Configura **Min** en 0.
7. Configura **Max** en 90 (° para Hinge).
8. Para probar la bisagra, arrastra el control semicircular.

Se detiene en 90°. **Set Min** y **Set Max** copian la pose actual del control en los límites.

Un límite inferior a una vuelta completa debe quedar dentro de −180°…180°. Límites como 170°…190° se rechazan con un mensaje. Un rango de una vuelta completa o más (por ejemplo −180°…180°) gira libremente sin límite.

Descripción de imagen del original en inglés (imagen omitida): límites de Hinge y controles.

*Captura histórica del taller. Límites de Hinge y controles.*

### Slide {#slide}

Barrel Slide, 0…0.3:

1. Selecciona **Add Joint → Slide**.
2. Haz clic en la pieza Barrel.
3. Pulsa **Y**.
4. Pulsa **Enter**.

Crea un control de flecha.

5. Configura **Min** en 0.
6. Configura **Max** en 0.3 (unidades de escena).
7. Para probar el deslizamiento, arrastra la flecha.

El cañón se desliza y se detiene en 0.3.

Descripción de imagen del original en inglés (imagen omitida): límites de recorrido Slide de la pieza seleccionada.

*Captura histórica del taller. Límites de recorrido Slide de la pieza seleccionada.*

### Telescope {#telescope}

Mástil con tres segmentos:

1. Crea la base y tres piezas de segmento.
2. Selecciona **Add Joint → Telescope**.
3. Haz clic en la base.
4. Haz clic en cada segmento, desde la base hacia fuera.
5. Pulsa **Enter**.
6. Pulsa la tecla del eje.
7. Para conservar la construcción, pulsa **Enter**.

Crea un control de flecha en la base. **Length** es el recorrido total. **Shares (empty = even)** reparte el recorrido entre segmentos.

Para probar repartos personalizados:

1. Configura **Length** en 1.
2. Escribe `0.5, 0.25, 0.25` en **Shares (empty = even)**.
3. Arrastra el control de flecha.

Los tres segmentos se extienden según sus partes. Deben sumar Length para que la punta recorra toda la longitud. Texto incorrecto como `0.5, abc` produce un mensaje. Cada segmento necesita una parte numérica y la suma debe ser Length. **Set Max** configura Length a partir de la pose del control.

Descripción de imagen del original en inglés (imagen omitida): longitud Telescope y reparto entre segmentos.

*Captura histórica del taller. Longitud Telescope y reparto entre segmentos.*

### Piston {#piston}

Elevador: cilindro en el bastidor, vástago en el brazo.

1. Asigna una Hinge al brazo.
2. Configura el brazo para que siga al bastidor.
3. Selecciona **Add Link → Piston**.
4. Haz clic en la pieza del cilindro del bastidor.
5. Haz clic en la pieza del vástago del brazo.

Crea un Piston sin control propio. Cada pieza apunta al anclaje de la otra. **Stretch**, opcional, estira el vástago para muelles y cables.

6. Para probarlo, mueve el control del brazo.

El pistón lo sigue. Si todavía nada mueve el Piston, se construye pero no tiene previsualización. **Test** informa de ello.

Descripción de imagen del original en inglés (imagen omitida): ajustes Piston de las piezas conectadas.

*Captura histórica del taller. Ajustes Piston de las piezas conectadas.*

### Gear Link {#gear-link}

Engranaje 20:40:

Ambas piezas necesitan primero una articulación. La conductora necesita Hinge. Para Gear y Belt, la conducida necesita Hinge. Para Rack necesita Slide.

1. Selecciona **Add Link → Gear Link**.
2. Haz clic en la pieza conductora.
3. Haz clic en la pieza conducida.

Para el método de cantidad de dientes:

1. En los ajustes del vínculo, configura **Source Teeth** en 20.
2. Configura **Target Teeth** en 40.

También puedes escribir un **Ratio**. **Kind** es Gear, Belt o Rack. **Reverse** invierte el sentido. Para probarlo, gira el origen.

Con **Kind** Gear, el destino gira −0.5× lo del origen (+0.5× con Belt). Gear invierte el sentido. Belt lo mantiene. Rack convierte rotación en deslizamiento. Su distancia por radián es **Ratio** × **Pinion Radius**.

La construcción depende del rango de Hinge de origen:

- Menos de una vuelta completa: restricción Transform. Sigue todo lo que mueve el origen, incluidas Sequences.
- Una vuelta completa o más: controlador que no necesita Python. El destino gira sin fin con el origen. Solo sigue controles y engranajes. Rig Validator avisa si se perdería una Sequence o Follow.

Descripción de imagen del original en inglés (imagen omitida): controles Gear Link antes del ejemplo 20:40. La proporción mostrada es 1.00 y ambas cantidades de dientes son 0.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Controles Gear Link antes del ejemplo 20:40. La proporción mostrada es 1.00 y ambas cantidades de dientes son 0.*

### Follow {#follow}

Blade 0–90° eleva Cover 0–40°:

Ambas piezas necesitan Hinge o Slide. La Hinge de origen necesita límites menores que una vuelta completa. BoneCraft rechaza un origen de giro libre.

1. Selecciona **Add Link → Follow**.
2. Haz clic en la pieza conductora (Blade).
3. Haz clic en la pieza seguidora (Cover).

Inicialmente, cada rango de correspondencia abarca todo el rango de su articulación.

4. Configura **Source Range** en 0…90.
5. Configura **Target Range** en 0…40.
6. Para probar Follow, mueve el control de Blade.

Cover lo sigue. Más allá de cualquiera de los extremos, el destino mantiene su valor. Para cambiar la correspondencia en Graph Editor, activa **Curve**. BoneCraft nunca sobrescribe tu curva (consulta Edición más abajo).

Descripción de imagen del original en inglés (imagen omitida): rangos fuente y destino de Follow.

*Captura histórica del taller. Rangos fuente y destino de Follow.*

### Sequence {#sequence}

Registrar pasos para plegar un arma:

1. En **3. Sequences**, haz clic en **Add Sequence**.

Crea un control de deslizador llamado `CTRL-SEQ-<name>`.

2. Haz clic en **Move Slider to End**.

El deslizador salta al final (1). El botón pasa a ser Record Step seguido del número del siguiente paso.

3. Coloca los controles de articulaciones en la pose del primer paso.
4. Haz clic en Record Step 1.

Cada control movido se convierte en un paso con su valor objetivo. Los controles vuelven a cero.

Para cada grabación adicional:

1. Haz clic en **Move Slider to End**.
2. Coloca los controles de articulaciones en la pose del siguiente paso.
3. Haz clic en el botón Record Step numerado actual.

De forma predeterminada, cada paso nuevo ocupa el siguiente cuarto del deslizador. Para cada paso registrado:

1. Configura **Target**.
2. Selecciona la transición: Linear, Ease In, Ease Out, Ease In Out o Snap.
3. Configura **Start**.
4. Configura **End**.

Fuera de su tramo, el paso mantiene su valor final. Se pueden superponer varias Sequences. Para probar una Sequence, haz clic en **Test**. El deslizador reproduce 0 → 1 → 0.

Junto al botón de registro de pasos y **Test**, la Sequence seleccionada tiene **Detach** (cadena rota) y **Delete** (X). Una Sequence retenida (por ejemplo un paso cuya curva modificaste) muestra su mensaje y **Restore**. Restore regenera los pasos desde el registro. No se ofrece Keep mine para una Sequence.

Descripción de imagen del original en inglés (imagen omitida): creación de Sequence, pasos registrados y temporización.

Descripción de imagen del original en inglés (imagen omitida): creación de Sequence, pasos registrados y temporización.

*Captura histórica del taller. Creación de Sequence, pasos registrados y temporización.*

## Test {#test}

**Test** (reproducción en la lista y en 3. Sequences) recorre un mecanismo por todo su rango y vuelve. No escribe claves y restaura la pose al terminar. Para detenerlo antes, pulsa **Esc**; también restaura la pose. En Gear Link o Follow recorre el origen. En Piston recorre la articulación que lo mueve. BoneCraft no detecta colisiones. Vigila las piezas que choquen.

Descripción de imagen del original en inglés (imagen omitida): probar el mecanismo seleccionado por su rango de movimiento.

*Captura histórica del taller. Probar el mecanismo seleccionado por su rango de movimiento.*

## Formas {#forms}

En **4. Controls**:

- Cada articulación y Sequence tiene un deslizador. Es el canal propio del control; arrastrarlo y usar el deslizador son lo mismo.
- **Save Form** registra todos los valores de controles y deslizadores Sequence con un nombre. Renómbralo en la lista.
- **Go to Form** asigna los valores guardados a todos los controles.
- **Go and Key** hace lo mismo e inserta claves en el fotograma actual.
- La **X** junto a la lista elimina una forma.

**Archivos guardados anteriores:** BoneCraft 9.2.18 lee y aplica formas capturadas por versiones anteriores. Abrir o aplicar una forma no la vuelve a guardar. **Save Form** captura los valores actuales de controles con el formato actual. Guardar con un nombre de forma existente sustituye los valores capturados de esa forma.

Los controles permanecen en **Mechanisms → 4. Controls**. La reparación de compatibilidad no cambia los controles del rig, los deslizadores Sequence ni la ubicación de paneles.

Descripción de imagen del original en inglés (imagen omitida): controles Forms con deslizadores, Save Form, Go to Form y Go and Key.

*Captura histórica del taller. Controles Forms con deslizadores, Save Form, Go to Form y Go and Key.*

## Lo que construye BoneCraft {#what-bonecraft-builds}

Para cada pieza:

| Hueso | Función | Visible |
|---|---|---|
| `CTRL-<part>` | El control. Su valor es el deslizador del panel. Solo Hinge, Slide y Telescope crean uno. | Sí |
| `MCH-<part>` | Suma el control y cada vínculo y después aplica límites. | Oculto |
| `DEF-<part>` | Copia `MCH-<part>`. La malla está vinculada a él. Los motores reciben este hueso. | Oculto |

Los huesos están en las colecciones `Mechanism Controls`, `Mechanism MCH` y `Mechanism DEF`. Una pieza sin articulación solo tiene huesos `MCH-` y `DEF-`. El control de Telescope es `CTRL-<telescope name>`. El de Sequence es `CTRL-SEQ-<name>`. Piston añade huesos `MCH-<part>-aim` y `MCH-<part>-target` para cada una de sus dos piezas.

Las restricciones de `MCH-<part>` siempre siguen este orden: Copy Transforms del control, contribución de cada vínculo y después Limit Rotation o Limit Location de la articulación. `DEF-<part>` tiene una Copy Transforms desde `MCH-<part>`.

Todo lo que crea BoneCraft está etiquetado con su registro: los nombres de restricciones empiezan por `BC·<id>·<role>` y los huesos llevan `bc_mech_id` y `bc_mech_role`. BoneCraft encuentra los huesos por etiqueta, no por nombre, así que puedes renombrarlos. Una reconstrucción los vuelve a encontrar y no crea duplicados.

Con Show Helpers activado, cada articulación y vínculo tiene una nota **How this works**. Enumera las restricciones por nombre, explica cada una y tiene **Select** (flecha) para examinar el hueso.

Nunca se tocan tus restricciones, controladores y huesos propios. Una restricción que añadas a un hueso MCH permanece debajo de las de BoneCraft tras reconstruir.

## Edición y cambios manuales {#editing-and-hand-edits}

- **Ediciones de valores** (límites, proporción, rangos, temporización, transición, aspecto del control) actualizan las restricciones existentes en su sitio. No hay reconstrucción.
- **Ediciones estructurales** (**Kind** de Gear Link, **Curve** de Follow, **Stretch** de Piston) sustituyen las restricciones de ese mecanismo y reconstruyen solo ese mecanismo.
- **Changed by hand.** Después de editar una restricción BoneCraft, por ejemplo un límite, el mensaje termina en «(changed by hand)». BoneCraft nunca sobrescribe la edición silenciosamente. Elige:
    - **Keep mine** copia tus valores al registro. Rechaza lo que no puede recuperar; el mensaje indica usar Restore o Detach.
    - **Restore** descarta tu edición y reconstruye desde el registro.
- Un mecanismo retenido también retiene todos los mecanismos que usan sus huesos hasta que lo resuelvas.
- La misma protección se aplica a curvas modificadas. Con **Curve** activado puedes editar la curva Follow en Graph Editor. Cambiar después, por ejemplo, Target Range sustituiría la curva. Ese cambio hace que el mensaje Follow termine en «(changed by hand)». **Keep mine** conserva tu curva. **Restore** la regenera.
- Una Sequence retenida muestra su mensaje y **Restore** en **3. Sequences**, con **Detach** y **Delete** al lado. No se ofrece Keep mine para Sequences.
- **Detach** (cadena rota) elimina el registro y las etiquetas, pero conserva huesos y restricciones como un rig manual propio. Detach y Delete rechazan un registro usado por otro e identifican a los usuarios.
- **Delete** (X) elimina el registro y todo lo creado por BoneCraft para él.
- Un bucle de vínculos se rechaza antes de construir nada y se identifica, por ejemplo «Blade Hinge → Cover Follow → Blade Hinge would loop.»

Rig Validator y Task Board informan de:

- Bucles de vínculos.
- Piezas ausentes.
- Huesos DEF movidos desde fuera de su mecanismo.
- Controladores que necesitan Python.
- Gear Links que pierden una Sequence o Follow.

La comprobación de nombres acepta guiones (`CTRL-`, `MCH-`, `DEF-`). La de controladores avisa solo sobre expresiones que necesitan Python. Un rig Mechanisms limpio no muestra errores de validación. Solo muestra el aviso del hueso `root` descrito en Límites de esta versión.

## Show Helpers {#show-helpers}

**Show Helpers** es una preferencia para todo BoneCraft: **Preferences → Add-ons → BoneCraft → Helpers**. Desactivarla oculta el texto didáctico: líneas qué/cuándo, notas **How this works** y frases completas de pasos guiados (se convierten en etiquetas breves). Los pasos, listas, Test, avisos y descripciones emergentes de Blender permanecen siempre.

El botón VRChat **Compact Mode** es su acceso rápido: activarlo significa desactivar Show Helpers.

## Límites de esta versión {#limits-of-this-version}

- Los mecanismos Click Turn, Track y Linkage llegarán más adelante.
- La exportación a motores del movimiento mecánico horneado llegará después de la comprobación manual en escritorio. Hasta entonces se exportan los huesos `DEF-`.
- BoneCraft no detecta colisiones. Para comprobarlas:
    1. Usa Test.
    2. Observa las piezas.
- Un Gear Link de giro libre solo sigue controles y engranajes.
- El hueso `root` del rig no está en ninguna colección, por lo que Rig Validator avisa y Task Board muestra «Rig validation warnings (1)».

Siguiente: [Herramientas de VRChat](08-vrchat.md)
