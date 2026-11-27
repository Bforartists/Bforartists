# Tutorial: Crescent Rose con Mecanismos {#tutorial-crescent-rose-with-mechanisms}

[← Contenido](index.md)

<!-- Print layout is scoped to this illustrated chapter; the shared renderer is unchanged. -->
<style>
@media print {
  h3[id^="12-crescent-rose--"] { break-before: page; break-after: avoid; }
  h2:has(+ h3[id^="12-crescent-rose--"]) { break-before: page; break-after: avoid; }
  h2 + h3[id^="12-crescent-rose--"] { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) { break-after: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) + p { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) table { break-inside: avoid; }
  [id="12-crescent-rose--what-you-built"] { break-before: page; break-after: avoid; }
}
</style>

## Qué vas a construir {#what-you-will-build}

Crescent Rose combina una guadaña y un rifle. En este tutorial se prepara el rig del modelo con Mecanismos. Un deslizador convierte la guadaña en rifle. Un segundo deslizador pliega el rifle hasta su forma compacta.

El tutorial utiliza todas las articulaciones y vínculos actuales excepto el vínculo de engranajes. Incluye ocho bisagras, tres deslizamientos, un telescopio, un pistón y un seguimiento. También crea dos secuencias y tres formas.

Las formas son poses didácticas de este modelo creado por aficionados. Mecanismos no detecta colisiones ni produce una réplica diseñada con criterios de ingeniería física. Al adaptar el rig, comprueba las holguras.

El resultado es el archivo `examples/crescent-rose/CrescentRose_Mechanisms.blend`. Puedes abrirlo en cualquier momento para comparar.

## Antes de empezar {#before-you-start}

- Archivos: `examples/crescent-rose/CrescentRose_parts.blend` contiene el modelo dividido en 15 objetos de piezas. Empieza el tutorial con este archivo. `CrescentRose_Mechanisms.blend` es el rig terminado.
- Tiempo: reserva una sesión para preparar el FBX y otra para la lección de Mecanismos. Son ejercicios extensos. Guarda puntos de control entre etapas.
- Terminología: lee primero «Qué hace Mecanismos» en [Mecanismos](07-mechanisms.md). Allí se definen pieza, articulación, vínculo, control, secuencia y forma.
- Idioma: las capturas del original inglés, omitidas aquí, muestran Bforartists y los paneles de BoneCraft en inglés. Los paneles de BoneCraft siguen la preferencia **Language**. El resto de Bforartists sigue su idioma de interfaz. Si BoneCraft no admite el idioma de Bforartists, sus paneles permanecen en inglés. Las instrucciones escritas de esta edición sin imágenes siguen siendo aplicables.
- Ruta de inicio: utiliza P1-P8 a continuación para el FBX original, o pasa al Paso 1 con el archivo preparado. Ambas rutas utilizan las mismas 15 piezas.
- Comprobaciones históricas del original inglés: las instrucciones y las capturas auténticas de la interfaz se comprobaron con BoneCraft `9.1.2` en Bforartists `5.2.0`, con su mapa de teclas predeterminado. Para esta edición sin imágenes no se realizaron capturas nuevas ni se repitió el tutorial.

**Navegación actual:** en 9.2.18, utiliza **BoneCraft → Mechanisms** o **Properties → Scene → Mechanisms**. Si las secciones de Escena están ocultas, activa **Tabs → Scene Properties → Show**. Parts, Joints & Links, Sequences y Controls conservan sus nombres. Las capturas antiguas del original inglés, omitidas aquí, pueden mostrar una disposición anterior de estas secciones.

Esta edición sin imágenes conserva los límites originales de captura y repetición de la versión 9.1.2 del original inglés; las imágenes se omiten. La revisión de la fuente para 9.2.18 no los sustituye por una nueva ejecución del tutorial. Las formas guardadas antiguas siguen pudiendo leerse y utilizarse. Abrirlas o aplicarlas no vuelve a guardar sus valores. Consulta [Formas](07-mechanisms.md#forms).

Las imágenes del original inglés utilizan marcas rojas numeradas para identificar dónde hacer clic, escribir o comprobar un resultado. Esta edición sin imágenes omite esas imágenes y conserva sus descripciones escritas y los pies con las acciones numeradas. Sigue los pasos escritos y las notas de acciones en orden (1, después 2 y después 3). Estos números se refieren a anotaciones del original inglés y vuelven a empezar en cada imagen original. En esa evidencia original, un recuadro marca un resultado que comprobar y un círculo marca una pieza o un botón que utilizar.

## Preparar el FBX original (P1-P8) {#prepare-the-original-fbx-p1-p8}

Si utilizas `CrescentRose_parts.blend`, omite esta sección.

1. Trabaja en un archivo nuevo.

2. Mantén juntos el FBX de origen y su carpeta `CrescentRoseTextures`.

Estos pasos se repitieron en Bforartists 5.2.0 con el mapa de teclas predeterminado. Utiliza el menú de modos visible. En este mapa de teclas, Tab puede alternar las superposiciones en vez de entrar en el modo Edición.

### P1 - Importar el FBX {#p1---import-the-fbx}

Utiliza el importador Legacy para este procedimiento.

1. Empieza con una escena vacía.

2. Selecciona **File > Import > FBX (.fbx) (Legacy)**.

3. Selecciona `CrescentRose.fbx`.

4. Mantén la escala de importación en `1.00`.

5. Selecciona Import FBX.

6. Pulsa 3 del teclado numérico para la vista derecha.

7. Pulsa Inicio para encuadrar los objetos importados.

El listado de objetos contiene una raíz y tres mallas de materiales: `Black01`, `Blades01` y `Red01`.

Descripción de la imagen del original inglés (imagen omitida): P1: opciones de importación FBX Legacy con escala 1.00

*1: Selecciona CrescentRose.fbx. 2: Mantén Scale en 1.00. 3: Haz clic en Import FBX; utiliza el importador Legacy.*

### P2 - Conservar la colocación y establecer el tamaño {#p2---preserve-placement-and-set-the-size}

El arma importada mide aproximadamente `0.32 m` de alto. El archivo preparado ya está escalado. Realiza este procedimiento de cambio de tamaño una sola vez sobre las mallas importadas.

1. Cambia al modo Objeto.

2. Selecciona las tres mallas.

3. Selecciona **Object > Parent > Clear and Keep Transformation**.

4. Elimina de la escena de trabajo la raíz que ya no se utiliza.

5. Con las tres mallas seleccionadas, selecciona **Object > Apply > Rotation & Scale**.

6. Pulsa Ctrl+R para iniciar Escalar en este mapa de teclas de Bforartists.

7. Escribe `6.25` para escalar las tres mallas juntas.

8. Confirma el escalado.

9. Selecciona de nuevo **Object > Apply > Rotation & Scale**.

El arma completa mide ahora aproximadamente `1.997 m` de alto.

Descripción de la imagen del original inglés (imagen omitida): P2: eliminar el emparentado conservando la colocación

*1: Pulsa F3 y busca Clear Parent Keep Transform. 2: Elige Clear and Keep Transformation. Repite la operación en las tres mallas antes de eliminar la raíz.*

Descripción de la imagen del original inglés (imagen omitida): P2: rotación y escala aplicadas al arma importada

*1: Después de escalar juntas las tres mallas por 6.25, aplica Rotation & Scale; Rotation debe indicar 0. 2: Scale debe indicar 1 en todos los ejes.*

El campo Dimensions de un objeto individual solo mide la malla de ese material. Comprueba la extensión conjunta de abajo arriba al medir el arma. Los tres objetos deben mostrar rotación cero y escala 1 antes de separarlos.

### P3 - Conectar los materiales {#p3---connect-the-materials}

1. Cambia al espacio de trabajo Shading.

2. Selecciona Material Preview.

Cada uno de los tres materiales utiliza cuatro imágenes de `CrescentRoseTextures`:

| Imagen | Espacio de color |
|---|---|
| `BaseColor` | **sRGB** |
| `Metallic` | `Non-Color` |
| `Roughness` | `Non-Color` |
| `Normal` | `Non-Color` |

Para cada material, procesa una imagen cada vez:

1. Carga la imagen correspondiente de `CrescentRoseTextures`.

2. Establece el espacio de color de esa imagen según la tabla.

3. Para una imagen BaseColor, Metallic o Roughness, conecta la salida Color de Image Texture a la entrada correspondiente de Principled BSDF.

Para cada imagen Normal, utiliza esta rama de conexión independiente:

1. Inserta un nodo **Normal Map**.

2. Mantén el nodo Normal Map en `Tangent Space`.

3. Conecta Color de la imagen Normal a Color de Normal Map.

4. Conecta Normal de Normal Map a Normal de Principled BSDF.

Conserva las UV existentes.

Descripción de la imagen del original inglés (imagen omitida): P3: cuatro mapas de textura y Normal Map en espacio tangente conectados para el material negro

*1: Conecta Color de BaseColor a Base Color del BSDF. 2: Mantén BaseColor en sRGB. 3: Establece todos los mapas de datos en Non-Color. 4: Conecta imagen Normal > Normal Map > Normal del BSDF, utilizando Tangent Space.*

Descripción de la imagen del original inglés (imagen omitida): P3: los tres materiales en Material Preview

*1: Comprueba el material de la hoja. 2: Comprueba los materiales rojo y negro del cuerpo en Material Preview; no debe haber texturas ausentes de color rosa.*

El procedimiento se aplica a los materiales negro, de la hoja y rojo. Después de seleccionar cada imagen, comprueba su espacio de color. La configuración del espacio de color pertenece a la imagen. El arma debe ser roja, negra y metálica, sin texturas ausentes de color rosa.

### P4 - Separar las piezas sueltas {#p4---separate-loose-pieces}

1. Selecciona las tres mallas de materiales.

2. Selecciona **Edit Mode** en el menú de modos de la vista.

3. Selecciona toda la geometría.

4. Selecciona **Mesh > Separate > By Loose Parts**.

5. Vuelve al modo Objeto.

Ahora hay **37** objetos de malla. Los sufijos numéricos generados pueden variar. Identifica los objetos por su posición y forma.

Descripción de la imagen del original inglés (imagen omitida): P4: entrar en Edit Mode y elegir By Loose Parts

*1: Cambia al modo Edit Mode y selecciona toda la geometría. 2: Pulsa F3, busca Separate Loose y elige By Loose Parts.*

Descripción de la imagen del original inglés (imagen omitida): P4: las 37 piezas sueltas después de la separación

*1: Comprueba que el total de objetos sea 37 después de la separación. 2: Utiliza el listado de objetos para seleccionar piezas por su forma y ubicación; los sufijos pueden variar.*

### P5 - Unir los 15 grupos móviles {#p5---join-the-15-moving-groups}

La tabla enumera cada isla de la malla de origen. Los nombres de materiales describen el aspecto, no los nombres finales de los objetos.

| Objeto final | Piezas que combinar | Vértices de malla después de unir |
|---|---|---:|
| `BladeTip` | Perilla negra de la articulación de la punta y pincho metálico de la punta | 252 |
| `Blade2` | Dos placas metálicas del segundo segmento y dos cubiertas rojas | 1000 |
| `Blade1` | Dos placas metálicas del primer segmento más próximas al cabezal | 512 |
| `HeadMount` | Bloque trasero negro, tapa superior y núcleo; dos placas interiores rojas y dos cubiertas superiores finas | 1395 |
| `PlateL` | Una placa exterior roja del cabezal en X negativo | 676 |
| `PlateR` | Una placa exterior roja del cabezal en X positivo | 676 |
| `RearSpike` | Dos hojas metálicas del pincho, dos tapas rojas del pivote y dos placas rojas de montaje | 1194 |
| `Receiver` | Cuerpo negro y perilla pequeña, anillo metálico encima del cerrojo y carcasa roja larga | 2609 |
| `Grip` | Bloque rojo de la empuñadura debajo del cajón de mecanismos | 194 |
| `Magazine` | Tubo negro debajo del cuerpo | 96 |
| `Bolt` | Cilindro rojo del cerrojo y sus dos piezas de perilla | 362 |
| `Pole` | Asta metálica inferior y collar rojo | 148 |
| `ButtSpike` | Pincho metálico inferior | 110 |
| `StrutBase` | Varilla roja fina entre el cajón de mecanismos y el cabezal | 34 |
| `StrutRod` | Manguito negro con muescas alrededor de esa varilla | 108 |

No unas las placas exteriores a Blade1. No unas entre sí las dos piezas del puntal. El puntal ya tiene dos piezas separadas. No es necesario bisecarlo.

Trabaja desde la punta de la hoja hacia dentro y después por el cajón de mecanismos y el asta. Para cada grupo móvil:

1. Selecciona las piezas que deben moverse juntas.

2. Para las piezas emparejadas de lados opuestos, orbita la vista para seleccionar ambas.

3. Comprueba la selección antes de unir.

4. Selecciona **Object > Join** (Ctrl+J).

5. Cambia el nombre del objeto unido en el listado de objetos.

Debe haber **15 mallas y 9,366 vértices** en total. El Paso 2 repite los nombres de las piezas terminadas y su posterior emparentado.

Descripción de la imagen del original inglés (imagen omitida): P5: los 15 grupos móviles con sus nombres en el listado de objetos

*1: Cambia el nombre de cada grupo unido en el listado de objetos para que coincida con los 15 nombres de la tabla.*

Descripción de la imagen del original inglés (imagen omitida): P5: las dos placas de origen de Blade1 seleccionadas antes de unir

*1: Selecciona las dos placas metálicas de Blade1 de lados opuestos. 2: Comprueba que ambos objetos estén seleccionados; utiliza Join y llama Blade1 al resultado.*

Descripción de la imagen del original inglés (imagen omitida): P5: comando Join del menú Object

*1: Abre Object después de seleccionar solo las piezas de un grupo. 2: Elige Join (Ctrl+J). Este recorte de menú identifica el comando; utiliza la selección de dos piezas descrita arriba.*

### P6 - Centrar los orígenes {#p6---centre-the-origins}

1. Cambia al modo Objeto.

2. Selecciona las 15 mallas.

3. Selecciona **Object > Set Origin > Origin to Geometry**.

4. Establece la opción Center de la operación en `Bounds Center`.

5. Comprueba que la rotación sea cero y la escala sea 1.

Los objetos siguen sin tener padres. No hay un esqueleto. Estos orígenes son para la preparación. El Paso 6 mueve los pivotes del mecanismo hasta las articulaciones reales.

Descripción de la imagen del original inglés (imagen omitida): P6: Object > Set Origin > Origin to Geometry

*1: Abre Object. 2: Pasa el puntero por Set Origin. 3: Elige Origin to Geometry; establece Bounds Center en las opciones de la operación.*

Descripción de la imagen del original inglés (imagen omitida): P6: origen centrado de Blade1 con transformaciones aplicadas

*1: El origen naranja está ahora centrado en la malla. 2: Confirma Rotation 0. 3: Confirma Scale 1. Los pivotes del mecanismo se moverán más adelante.*

### P7 - Cambiar el tamaño de las texturas y empacarlas {#p7---resize-and-pack-the-textures}

Hay **12 mapas utilizados**, cuatro por material. No sobrescribas los JPEG de origen. Para cada mapa utilizado:

1. Selecciona el mapa en el Editor de imágenes.

2. Selecciona **Image > Resize**.

3. Establece la anchura en **1024**.

4. Establece la altura en **1024**.

5. Confirma el cambio de tamaño.

6. Selecciona **Image > Pack**.

El empacado conserva los píxeles redimensionados dentro del archivo blend. Después de procesar todos los mapas, comprueba Material Preview.

Descripción de la imagen del original inglés (imagen omitida): P7: menú Image empacando una textura redimensionada a 1024 por 1024

*1: Elige Image > Resize e introduce 1024 para anchura y altura. 2: Comprueba las dimensiones resultantes de 1024 x 1024. 3: Elige Pack. Repite la operación en los 12 mapas utilizados.*

### P8 - Guardar y volver a abrir el archivo preparado {#p8---save-and-reopen-the-prepared-file}

1. Guarda la copia de trabajo como `CrescentRose_parts.blend`.

2. Vuelve a abrir ese archivo.

3. Comprueba las 15 mallas con nombre, sus transformaciones y los materiales rojo y negro.

4. Selecciona de nuevo la vista derecha.

5. Pulsa Inicio.

6. Continúa con el Paso 1.

Los 12 mapas deben seguir disponibles sin el directorio original de texturas.

Descripción de la imagen del original inglés (imagen omitida): P8: archivo preparado abierto de nuevo con el arma texturizada intacta

*1: Abre File para Save As y después Open para cargar de nuevo tu copia de trabajo. 2: Confirma que se han conservado las 15 mallas con nombre. 3: Comprueba los materiales; la barra de título identifica el archivo abierto de nuevo.*

## A. Abrir el archivo {#a-open-the-file}

### Paso 1 — Abrir el archivo de piezas {#step-1--open-the-parts-file}

1. Abre `examples/crescent-rose/CrescentRose_parts.blend`.

2. Selecciona el sombreado Material Preview en la vista.

3. Pulsa 3 del teclado numérico para la vista derecha.

4. Pulsa Inicio para encuadrar el arma.

La hoja apunta a la izquierda y el pincho inferior apunta hacia abajo.

Descripción de la imagen del original inglés (imagen omitida): Paso 1: archivo de piezas en la vista derecha

*1: Haz clic en Material Preview. 2: Pulsa 3 del teclado numérico hasta que la vista indique Right Orthographic; pulsa Home para encuadrar el arma.*

**Qué deberías ver:** La guadaña roja y negra, de unos 2 m de altura, sin nada seleccionado.

### Paso 2 — Conocer las piezas {#step-2--meet-the-parts}

El listado de objetos muestra los 15 objetos. Cada uno es una pieza que se mueve como un bloque:

| Objeto | Qué es | Se monta sobre |
|---|---|---|
| `Receiver` | Cuerpo del rifle con la mira telescópica, el gatillo y el alza | el rig |
| `Grip` | Empuñadura debajo del cajón de mecanismos | `Receiver` |
| `Magazine` | Cargador cilíndrico | `Receiver` |
| `Bolt` | Cerrojo | `Receiver` |
| `Pole` | Asta inferior y su collar | `Receiver` |
| `ButtSpike` | Pincho de la parte inferior | `Pole` |
| `HeadMount` | Bloque del cabezal del que cuelga la hoja | `Receiver` |
| `Blade1` | Primer segmento de la hoja, el más próximo al cabezal | `HeadMount` |
| `Blade2` | Segundo segmento | `Blade1` |
| `BladeTip` | Punta | `Blade2` |
| `RearSpike` | Pincho de la parte posterior del cabezal | `HeadMount` |
| `PlateL`, `PlateR` | Placas laterales exteriores del cabezal | `HeadMount` |
| `StrutBase` | Varilla fina entre el cajón de mecanismos y el cabezal | `Receiver` |
| `StrutRod` | Manguito con muescas alrededor de esa varilla | `HeadMount` |

Descripción de la imagen del original inglés (imagen omitida): Paso 2: los 15 objetos de piezas en el listado de objetos

*1: Identifica los tres segmentos de la hoja. 2: Compara los nombres del cuerpo, del cabezal y del asta con la tabla. 3: Mantén StrutBase y StrutRod como objetos separados.*

Para el FBX original, sigue P1-P8 arriba. Esas acciones de interfaz produjeron el archivo preparado suministrado. El script de preparación del repositorio proporciona una tabla de agrupación de referencia.

### Paso 3 — Encontrar Mecanismos {#step-3--find-mechanisms}

Si el estante de herramientas izquierdo está oculto:

1. Con el puntero sobre la vista, pulsa T.

2. Selecciona Tools en el menú Region Toggle.

Después:

1. Abre la pestaña BoneCraft en el estante de herramientas izquierdo.

2. Expande **Mechanisms**.

3. Arrastra el borde derecho del estante para que el texto del panel resulte legible.

La misma sección aparece en **Properties > Scene** cuando Scene Properties está en Show en las preferencias de BoneCraft. Las capturas omitidas del original inglés utilizan el estante de herramientas.

Con una malla activa y sin rig, **Add Parts from Selection** aparece arriba. Antes de utilizarlo, selecciona todas las piezas como se describe en el Paso 4. Las subsecciones numeradas se pueden utilizar después de añadir las piezas.

Descripción de la imagen del original inglés (imagen omitida): Paso 3: sección Mechanisms de la pestaña BoneCraft

*1: Haz clic en la pestaña BoneCraft. 2: Expande Mechanisms. 3: Localiza Add Parts from Selection; selecciona las mallas antes de utilizarlo.*

## B. Piezas {#b-parts}

### Paso 4 — Añadir piezas de la selección {#step-4--add-parts-from-selection}

1. Con el puntero sobre la vista, pulsa A para seleccionar los 15 objetos.

2. Selecciona **Add Parts from Selection**.

Descripción de la imagen del original inglés (imagen omitida): Paso 4: todas las piezas seleccionadas, Add Parts from Selection

*1: Sitúa el puntero sobre la vista y pulsa A para seleccionar las 15 mallas. 2: Haz clic en Add Parts from Selection.*

**Qué deberías ver:** Aparece un esqueleto nuevo, «Mechanism Rig», en el listado de objetos, con las piezas debajo. Los objetos de malla permanecen seleccionados. **1. Parts** enumera las 15 piezas. La pestaña BoneCraft empieza ahora con la sección Overview desplegable del rig.

### Paso 5 — Se monta sobre {#step-5--rides-on}

Una pieza se monta sobre la pieza a la que está unida.

1. Selecciona `Blade1` en **1. Parts**.

2. Abre el menú «Rides on» situado debajo de la lista.

3. Selecciona `HeadMount`.

4. Repite la operación para cada pieza según la tabla del Paso 2.

`Receiver` conserva «the rig».

Descripción de la imagen del original inglés (imagen omitida): Paso 5: Blade1 se monta sobre HeadMount

*1: Selecciona Blade1 en la lista Parts. 2: Abre Rides on y elige HeadMount. Repite la operación siguiendo la tabla de padres.*

### Paso 6 — Pivotes {#step-6--pivots}

Una bisagra gira alrededor del pivote de su pieza. Los segmentos de la hoja, el cabezal y la empuñadura deben girar en sus articulaciones, en vez de hacerlo alrededor de sus centros. Trabaja en la vista lateral ortográfica para conservar la posición lateral del pivote.

1. Selecciona `Blade1` en la lista.

2. Selecciona **Edit Pivot**.

3. Selecciona el marcador.

4. Pulsa Ctrl+W para Move en Bforartists.

5. Haz clic donde el segmento se une al cabezal.

6. Selecciona **Apply Pivot**.

7. Repite el procedimiento del pivote para las piezas siguientes.

| Pieza | Posición del pivote |
|---|---|
| `Blade2` | Donde se une a `Blade1` |
| `BladeTip` | Donde se une a `Blade2` |
| `HeadMount` | Su punto más bajo, donde el puntal se une a él |
| `Grip` | Su borde superior |
| `RearSpike` | Donde se une al cabezal |
| `PlateL` y `PlateR` | Centro del perno redondo, donde Blade1 se une al cabezal |
| `StrutBase` | Su extremo inferior |
| `StrutRod` | Su extremo superior |

La posición del marcador en la captura omitida del original inglés sirve de orientación. Una diferencia de unos milímetros no produce ningún cambio visible.

Descripción de la imagen del original inglés (imagen omitida): Paso 6: seleccionar la pieza y hacer clic en Edit Pivot

*1: Selecciona Blade1 en Parts. 2: Haz clic en Edit Pivot; después mueve y aplica el marcador como se explica a continuación.*

Descripción de la imagen del original inglés (imagen omitida): Paso 6: marcador del pivote de Blade1 en la articulación, Apply Pivot

*1: Mueve el marcador del pivote hasta la articulación de la hoja con Ctrl+W. 2: Haz clic en Apply Pivot para conservar esa ubicación.*

## C. El cabezal {#c-the-head}

### Paso 7 — Añadir articulación → Bisagra {#step-7--add-joint--hinge}

Si necesitas ocultar un obstáculo, ocúltalo antes de iniciar la guía.

Abre **Add Joint → Hinge**. La cabecera y la barra de estado de la construcción guiada explican cada paso.

Descripción de la imagen del original inglés (imagen omitida): Paso 7: menú Add Joint, Hinge

*1: Abre Add Joint. 2: Haz clic en Hinge. La construcción guiada espera ahora una pieza.*

### Paso 8 — Hacer clic en el cabezal {#step-8--click-the-head}

La cabecera indica «haz clic en la pieza que gira». En la vista derecha, la placa exterior tapa el cabezal. Haz clic en el bloque posterior del cabezal, detrás de las placas, señalado por el círculo.

Si la cabecera indica `PlateR`:

1. Pulsa Esc.

2. Reinicia **Add Joint > Hinge**.

3. Haz clic más atrás en el cabezal.

Mientras está activa, la guía intercepta los atajos de teclado habituales.

Descripción de la imagen del original inglés (imagen omitida): Paso 8: hacer clic en el bloque posterior del cabezal

*1: Haz clic en el bloque negro posterior de HeadMount, detrás de la placa exterior roja. Comprueba que la guía indique HeadMount.*

### Paso 9 — Pulsar X y después Intro {#step-9--press-x-then-enter}

La cabecera solicita el eje.

1. Pulsa X.

2. Inspecciona la previsualización en bucle.

3. Pulsa Intro para conservar la bisagra.

El cabezal gira alrededor del eje lateral.

Descripción de la imagen del original inglés (imagen omitida): Paso 9: paso de selección del eje

*1: Sigue la indicación del eje: pulsa X y después Intro. 2: Observa cómo gira el cabezal alrededor de su pivote antes de confirmar.*

**Qué deberías ver:** `HeadMount Hinge` en **2. Joints & Links**, con su deslizador en **4. Controls**. Utiliza estos deslizadores en el modo Objeto.

Para utilizar los controles de huesos de la vista:

1. Selecciona el esqueleto.

2. Cambia al modo Pose.

### Paso 10 — Límites {#step-10--limits}

1. Selecciona `HeadMount Hinge` en la lista.

2. Establece **Min** en 0.

3. Establece **Max** en 120.

Los valores positivos giran el cabezal hacia abajo y hacia atrás. Conserva el límite de recorrido de 120 grados. La secuencia Rifle utiliza un objetivo de 90 grados junto con las bisagras de la hoja.

Descripción de la imagen del original inglés (imagen omitida): Paso 10: Min 0, Max 120

*1: Selecciona HeadMount Hinge. 2: Establece Min en 0. 3: Establece Max en 120; haz doble clic en el número, escribe y pulsa Intro.*

### Paso 11 — Probar {#step-11--test}

Haz clic en el botón de reproducción de la fila. El cabezal recorre 120° y vuelve, y se restaura la pose.

Descripción de la imagen del original inglés (imagen omitida): Paso 11: Test en la fila de la bisagra

*1: Haz clic en el pequeño triángulo de reproducción de la fila HeadMount Hinge. Observa el recorrido de ida y vuelta.*

## D. La cadena de la hoja {#d-the-blade-chain}

### Paso 12 — Tres bisagras más {#step-12--three-more-hinges}

Para cada pieza `Blade1`, `Blade2` y `BladeTip`, repite los Pasos 7 a 10:

1. Abre **Add Joint → Hinge**.

2. Haz clic en el segmento.

3. Pulsa X.

4. Pulsa Intro.

5. Establece **Max** en 120.

Cada segmento se monta sobre el segmento anterior. Las tres bisagras forman una cadena.

Descripción de la imagen del original inglés (imagen omitida): Paso 12: las tres bisagras de los segmentos de la hoja y la bisagra independiente del cabezal en la lista

*1: Crea y selecciona cada bisagra de la hoja: Blade1, Blade2 y BladeTip. 2: Establece Max en 120 para cada una; utiliza X como eje.*

### Paso 13 — Probar la cadena {#step-13--try-the-chain}

1. Contrae **2. Joints & Links** para hacer sitio.

2. Expande **4. Controls**.

3. En modo Objeto, establece `Blade1 Hinge`, `Blade2 Hinge` y `BladeTip Hinge` en 60 grados cada uno.

Para introducir cada valor:

1. Haz doble clic en su campo numérico.

2. Pulsa Ctrl+A.

3. Escribe el valor.

4. Pulsa Intro.

Los segmentos posteriores se mueven con los anteriores, curvando la cadena. Antes de continuar, restablece los tres valores a 0.

Descripción de la imagen del original inglés (imagen omitida): Paso 13: las tres bisagras de la hoja a 60 grados en Controls

*1: Introduce 60 en cada uno de los tres deslizadores de la hoja. 2: Comprueba que la cadena se curve en conjunto. Devuelve los tres deslizadores a 0.*

## E. Placas y puntal {#e-plates-and-strut}

### Paso 14 — Bisagras en las placas {#step-14--hinges-on-the-plates}

`PlateL` queda oculta detrás del cabezal en la vista derecha.

1. Añade una bisagra en `PlateR` con el mismo procedimiento.

2. Establece su **Max** en 30.

3. Pulsa Ctrl+3 del teclado numérico para la vista izquierda.

4. Añade una bisagra en `PlateL`.

5. Establece su **Max** en 30.

6. Pulsa 3 del teclado numérico para volver a la vista derecha.

Descripción de la imagen del original inglés (imagen omitida): Paso 14: PlateL Hinge y PlateR Hinge

*1: Crea las bisagras PlateR y PlateL; utiliza la vista lateral opuesta para acceder a PlateL. 2: Establece Max en 30 para cada una.*

### Paso 15 — Añadir vínculo → Seguimiento {#step-15--add-link--follow}

Un solo control debe mover ambas placas. Prepara la vista antes de iniciar la guía:

1. Pulsa 1 del teclado numérico para la vista frontal.

2. Selecciona `Blade2`.

3. Utiliza F3 > Frame Selected para acercar el cabezal.

Las dos placas exteriores aparecen en los bordes izquierdo y derecho.

1. Abre **Add Link > Follow**.

2. Haz clic en `PlateL`, en el borde izquierdo, como pieza conductora.

3. Haz clic en `PlateR`, en el borde derecho, como pieza seguidora.

4. Pulsa Intro.

Descripción de la imagen del original inglés (imagen omitida): Paso 15: la vista frontal deja accesibles ambas placas exteriores para seleccionarlas en Seguimiento

*1: Haz clic primero en PlateL, la pieza conductora. 2: Haz clic después en PlateR, la pieza seguidora. Pulsa Intro.*

### Paso 16 — Rangos {#step-16--ranges}

1. Selecciona el nuevo seguimiento.

2. Comprueba los valores rellenados automáticamente de **Source Range** 0…30 y **Target Range** 0…30.

3. En **Name**, cambia el nombre del vínculo a `PlateR Follow`.

Descripción de la imagen del original inglés (imagen omitida): Paso 16: Source Range y Target Range

*1: Llama PlateR Follow al vínculo. 2: Comprueba que Source Range sea de 0 a 30. 3: Comprueba que Target Range sea de 0 a 30.*

### Paso 17 — Añadir vínculo → Pistón {#step-17--add-link--piston}

El puntal debe apuntar entre el cajón de mecanismos y el cabezal mientras el cabezal se pliega. La guía intercepta los atajos de navegación mientras está activa. Antes de iniciar la guía:

1. Pulsa 3 del teclado numérico para la vista derecha.

2. Selecciona `StrutRod` en el listado de objetos.

3. Utiliza F3 > Frame Selected para obtener una vista cercana.

4. Abre **Add Link > Piston**.

Descripción de la imagen del original inglés (imagen omitida): Paso 17: menú Add Link, Piston

*1: Abre Add Link después de encuadrar StrutRod. 2: Elige Piston; la guía solicita primero el cilindro.*

### Paso 18 — El cilindro y la varilla {#step-18--the-cylinder-and-the-rod}

Las funciones de cilindro y varilla de la guía describen los extremos del vínculo. Los nombres de los objetos del modelo describen sus piezas originales. `StrutBase` es la varilla roja fina expuesta en las muescas del manguito. `StrutRod` es el manguito negro.

1. En la vista cercana, haz clic primero en `StrutBase` como pieza del cilindro.

2. Haz clic después en `StrutRod` como pieza de la varilla.

3. Pulsa Intro para aceptar.

4. Cambia el nombre del vínculo a `Head Strut`.

5. Mantén **Stretch** desactivado.

1. Cambia `HeadMount Hinge` en Controls.

2. Inspecciona el puntal.

3. Restablece el valor a cero.

**Qué deberías ver:** El puntal sigue al cabezal. Cada pieza apunta hacia la otra.

Descripción de la imagen del original inglés (imagen omitida): Paso 18: guía del pistón, primero el cilindro rojo expuesto y después el manguito negro

*1: Haz clic primero en StrutBase, la pieza roja expuesta. 2: Haz clic después en el manguito negro StrutRod. Pulsa Intro.*

Descripción de la imagen del original inglés (imagen omitida): Paso 18: ajustes de Head Strut con Stretch desactivado

*1: Cambia el nombre del vínculo a Head Strut. 2: Deja Stretch sin marcar; después prueba HeadMount Hinge y restablece 0.*

## F. El rifle {#f-the-rifle}

### Paso 19 — Bisagras de la empuñadura y del pincho trasero {#step-19--grip-and-rear-spike-hinges}

Para cada pieza `Grip` y `RearSpike`:

1. Abre **Add Joint → Hinge**.

2. Haz clic en la pieza.

3. Pulsa X.

4. Pulsa Intro.

5. Establece **Min** en 0.

6. Establece **Max** en 90.

Después:

1. Selecciona `RearSpike Hinge` en la lista.

2. Establece su eje X en -1.

3. Mantén Y y Z en 0.

4. Mantén Grip en X positivo.

5. Confirma que `Grip Hinge` y `RearSpike Hinge` aparezcan en la lista de articulaciones.

Invertir el eje X de RearSpike lo pliega hacia el cabezal plegado en Compact. Estos controles pliegan la empuñadura y el pincho trasero para la forma compacta del Paso 25.

Descripción de la imagen del original inglés (imagen omitida): Paso 19: Grip Hinge, Max 90

*1: Selecciona Grip Hinge. 2: Mantén el eje X en 1, y Y y Z en 0. 3: Establece Max en 90; mantén Min en 0.*

Descripción de la imagen del original inglés (imagen omitida): Paso 19: RearSpike Hinge con eje X -1 y Max 90

*1: Selecciona RearSpike Hinge. 2: Establece el eje X en -1. 3: Establece Max en 90; mantén Min en 0.*

### Paso 20 — Deslizamientos de Magazine y Bolt {#step-20--magazine-and-bolt-slides}

Para `Magazine` y después `Bolt`:

1. Abre **Add Joint → Slide**.

2. Haz clic en la pieza.

3. Pulsa Z.

4. Pulsa Intro.

5. Establece **Max** en 0.04 para Magazine o 0.06 para Bolt.

Los deslizamientos utilizan unidades de la escena. Un valor de 0.06 equivale a 6 cm.

Descripción de la imagen del original inglés (imagen omitida): Paso 20: Magazine Slide, eje Z y Max 0.04

*1: Selecciona Magazine Slide después de Add Joint > Slide. 2: Utiliza el eje Z (Z = 1, X = Y = 0). 3: Establece Max en 0.04; mantén Min en 0.*

Descripción de la imagen del original inglés (imagen omitida): Paso 20: Bolt Slide, eje Z y Max 0.06

*1: Selecciona Bolt Slide después de Add Joint > Slide. 2: Utiliza el eje Z (Z = 1, X = Y = 0). 3: Establece Max en 0.06; mantén Min en 0.*

### Paso 21 — Deslizamiento del asta {#step-21--pole-slide}

1. Abre **Add Joint → Slide**.

2. Haz clic en `Pole`.

3. Pulsa Z.

4. Pulsa Intro.

5. Establece **Max** en 0.6.

6. En **4. Controls**, establece `Pole Slide` en 0.6.

7. Inspecciona el asta retraída.

8. Restablece el control a cero.

Los valores positivos desplazan el asta hacia arriba, dentro del cajón de mecanismos.

Descripción de la imagen del original inglés (imagen omitida): Paso 21: ajustes de Pole Slide, eje Z y Max 0.6

*1: Selecciona Pole Slide después de Add Joint > Slide. 2: Utiliza el eje Z (Z = 1, X = Y = 0). 3: Establece Max en 0.6; mantén Min en 0.*

### Paso 22 — Telescopio del asta {#step-22--pole-telescope}

1. Abre **Add Joint → Telescope**.

2. Haz clic en `Pole` como base.

3. Haz clic en `ButtSpike` como segmento.

4. Pulsa Intro.

5. Pulsa Z.

6. Pulsa Intro.

7. Establece **Length** en 0.2.

8. Prueba el control independiente.

9. Restablece el control a cero.

El control desplaza el pincho hasta 20 cm a lo largo de Z positivo, hacia el interior del asta de este modelo.

Descripción de la imagen del original inglés (imagen omitida): Paso 22: selecciones guiadas de Telescopio, Pole como base y ButtSpike como segmento

*1: Haz clic en Pole como base. 2: Haz clic en ButtSpike como segmento. Pulsa Intro, después Z y después Intro.*

Descripción de la imagen del original inglés (imagen omitida): Paso 22: ajustes de Pole Telescope, eje Z y Length 0.2

*1: Selecciona Pole Telescope. 2: Comprueba que Z sea su eje. 3: Introduce Length 0.2; prueba el control y restablece cero.*

## G. Secuencias {#g-sequences}

### Paso 23 — Añadir secuencia {#step-23--add-sequence}

1. En **3. Sequences**, selecciona **Add Sequence**.

2. Haz doble clic en el nombre de la secuencia en la lista.

3. Escribe `Scythe to Rifle`.

4. Pulsa Intro.

Descripción de la imagen del original inglés (imagen omitida): Paso 23: Add Sequence

*1: Haz clic en Add Sequence. 2: Haz doble clic en el nombre nuevo y escribe Scythe to Rifle. Pulsa Intro.*

### Paso 24 — Grabar un grupo de movimiento {#step-24--record-a-motion-group}

1. Selecciona **Move Slider to End**.

El deslizador de la secuencia pasa a `100%`. El botón cambia a Record Step 1.

1. En **4. Controls**, establece `BladeTip Hinge` en 70.

2. Establece `Blade2 Hinge` en 120.

3. Selecciona Record Step 1.

Esto almacena dos entradas de destino, una por control movido. Ambos deslizadores de articulación se restablecen a cero.

Descripción de la imagen del original inglés (imagen omitida): Paso 24: Move Slider to End antes de posar el primer grupo

*1: Haz clic una vez en Move Slider to End. El botón cambia a Record Step 1.*

Descripción de la imagen del original inglés (imagen omitida): Paso 24: Record Step 1 con Blade2 a 120 y BladeTip a 70 grados

*1: Introduce Blade2 = 120 y BladeTip = 70. 2: Haz clic en Record Step 1; se almacenan ambos destinos y se restablecen los deslizadores de articulación.*

*Grupos de movimiento restantes.* La grabación permanece preparada después de cada captura. No la prepares de nuevo. Para cada grupo restante de la tabla:

1. Coloca los controles del grupo en los valores indicados.

2. Selecciona el botón Record Step que aparezca.

| Grupo de movimiento | Coloca estos controles | Botón de grabación después de los grupos anteriores |
|---|---|---|
| 2 | `Blade1 Hinge` 10 y `PlateL Hinge` 30 | Record Step 3 |
| 3 | `HeadMount Hinge` 90 | Record Step 5 |
| 4 | `Pole Slide` 0.6 | Record Step 6 |

El número del botón equivale a la cantidad de entradas de destino almacenadas más uno. Grabar dos controles hace avanzar el número en dos. No cuenta los clics de grabación. Los cuatro grupos de movimiento producen seis entradas de destino. Si cambias qué controles se mueven, utiliza el número que aparezca en el botón.

### Paso 25 — Los pasos {#step-25--the-steps}

Cada destino grabado tiene una entrada debajo de la secuencia. La entrada muestra **Target**, suavizado, **Start** y **End**. Los campos Start/End utilizan 0-1. Los deslizadores de Controls muestran 0-100%.

| Movimiento | Start | End |
|---|---:|---:|
| La hoja se pliega primero | 0 | 0.25 |
| Las placas y el primer segmento siguen | 0.25 | 0.5 |
| El cabezal se pliega en tercer lugar | 0.5 | 0.8 |
| El asta se mueve al final | 0.8 | 1 |

Las entradas del mismo grupo de movimiento utilizan los mismos valores Start y End. Para cada entrada de `Scythe to Rifle`:

1. Establece **Start** en el valor Start de su grupo de movimiento según la tabla.

2. Establece **End** en el valor End de su grupo de movimiento según la tabla.

3. Mantén la entrada en `Ease In Out`.

Antes del intervalo de un paso, este conserva su valor inicial. Después del intervalo, conserva su valor final.

Cuando termines cada secuencia, selecciona **Cancel** en el aviso de captura. Cancel termina la grabación, conserva las entradas almacenadas y devuelve el deslizador de esa secuencia a cero. Mientras la grabación está preparada, una advertencia de solapamiento describe el siguiente intervalo de grabación propuesto. No añadas un grupo vacío adicional.

Para la segunda secuencia, utiliza el procedimiento de grabación del Paso 24:

1. Añade `Rifle to Compact`.

2. Selecciona **Move Slider to End** una sola vez para preparar la grabación.

3. Establece `Grip Hinge` en 90 para el primer grupo.

4. Establece `RearSpike Hinge` en 90.

5. Selecciona Record Step 1.

6. Para cada entrada del primer grupo:

    1. Establece **Start** en 0.

    2. Establece **End** en 0.5.

7. Establece `Magazine Slide` en 0.04 para el segundo grupo.

8. Establece `Bolt Slide` en 0.06.

9. Selecciona Record Step 3.

10. Para cada entrada del segundo grupo:

    1. Establece **Start** en 0.5.

    2. Establece **End** en 1.

11. Mantén cada entrada en `Ease In Out`.

12. Selecciona **Cancel** en el aviso de captura para terminar la grabación.

Cada grupo crea dos entradas. Para el segundo grupo, el botón de grabación cambia de Record Step 1 a Record Step 3.

Descripción de la imagen del original inglés (imagen omitida): Paso 25: los seis destinos y sus intervalos temporales en Scythe to Rifle

*1: Target es el valor grabado de la articulación. 2: Elige Ease In Out. 3: Introduce Start. 4: Introduce End. Repite estos campos en las seis entradas utilizando los valores indicados.*

Descripción de la imagen del original inglés (imagen omitida): Paso 25: los cuatro destinos y sus intervalos temporales en Rifle to Compact

*1: Grip y RearSpike utilizan Target 90, Start 0 y End 0.5. 2: Magazine y Bolt utilizan 0.04 / 0.06, Start 0.5 y End 1. Mantén Ease In Out.*

Descripción de la imagen del original inglés (imagen omitida): Paso 25: terminar la grabación con Cancel en el aviso de captura

*1: Después de terminar una secuencia, haz clic en Cancel en este aviso de captura para finalizar la grabación. Esto conserva las entradas y devuelve la secuencia a cero.*

### Paso 26 — Probar la secuencia {#step-26--test-the-sequence}

**Test**, junto al botón de grabación de pasos, recorre el deslizador de 0% a 100% y de vuelta a 0%. Después restaura el valor que tenía el deslizador antes de la prueba.

1. Desde Scythe, selecciona **Test** para `Scythe to Rifle`.

2. Con la primera secuencia al 100%, selecciona **Test** para `Rifle to Compact`.

3. Después de probar, restablece ambas secuencias a 0%.

Descripción de la imagen del original inglés (imagen omitida): Paso 26: botón Test de la secuencia durante el plegado

*1: Haz clic en Test junto al botón de grabación. 2: Observa el plegado y el retorno. Prueba Compact con Scythe to Rifle al 100%.*

**Qué deberías ver:** La hoja se curva, las placas se cierran, el cabezal se pliega hacia abajo a lo largo del cajón de mecanismos y el asta se desliza hacia arriba. Después todo vuelve a su estado inicial.

## H. Formas {#h-forms}

### Paso 27 — Guardar forma {#step-27--save-form}

Mantén a cero todos los deslizadores de articulaciones individuales. Las secuencias proporcionan su movimiento. Llevar la secuencia seleccionada a su extremo puede preparar de nuevo la grabación. Guardar una forma no graba otro paso. A menos que quieras añadir otro destino, no selecciones Record Step.

En **4. Controls**:

1. Con todos los deslizadores en 0, selecciona **Save Form**.

2. Haz doble clic en la nueva entrada de la lista.

3. Llámala `Scythe`.

4. Establece `Scythe to Rifle` en `100%`.

5. Selecciona **Save Form**.

6. Llama `Rifle` a la entrada nueva mediante el mismo procedimiento de cambio de nombre.

7. Establece también `Rifle to Compact` en `100%`.

8. Selecciona **Save Form**.

9. Llama `Compact` a la entrada nueva.

Para quitar el estado de grabación preparada:

1. Selecciona `Scythe` en la lista de formas.

2. Selecciona **Go to Form**.

Ambas secuencias vuelven a cero. Ir a Rifle o Compact puede preparar de nuevo la grabación porque la secuencia seleccionada está al 100%.

Descripción de la imagen del original inglés (imagen omitida): Paso 27: Save Form con todos los deslizadores en 0

*1: Empieza con ambas secuencias y todas las articulaciones en 0. 2: Haz clic en Save Form. 3: Haz doble clic en la entrada nueva de la lista y llámala Scythe; repite la operación para Rifle y Compact.*

### Paso 28 — Ir a forma {#step-28--go-to-form}

1. Selecciona una forma en la lista.

2. Selecciona **Go to Form**.

**Go and Key** también inserta claves para todos los controles en el fotograma actual. Estas claves animan la transformación.

Descripción de la imagen del original inglés (imagen omitida): Paso 28: Rifle seleccionado, Go to Form

*1: Selecciona la forma guardada. 2: Haz clic en Go to Form. Go and Key también inserta claves de animación.*

### Paso 29 — El rifle {#step-29--the-rifle}

Descripción de la imagen del original inglés (imagen omitida): Paso 29: forma Rifle

*1: Selecciona Rifle. 2: Haz clic en Go to Form. 3: Compara los porcentajes de las secuencias con la pose representada en el original.*

### Paso 30 — Compact {#step-30--compact}

Descripción de la imagen del original inglés (imagen omitida): Paso 30: forma Compact

*1: Selecciona Compact. 2: Haz clic en Go to Form. 3: Compara los porcentajes de las secuencias con la pose representada en el original.*

1. Vuelve a `Scythe`.

2. Guarda el archivo.

## Qué has construido {#what-you-built}

| Registro | Huesos | Qué hace |
|---|---|---|
| 15 piezas | `MCH-<part>` y `DEF-<part>` | La malla de cada pieza está emparentada a su hueso `DEF-` |
| 8 bisagras, 3 deslizamientos, 1 telescopio | `CTRL-<part>` | Los controles; sus valores son los deslizadores de **4. Controls** |
| 1 pistón | `MCH-<part>-aim` y `MCH-<part>-target` | Mantienen las dos piezas del puntal apuntando una hacia otra |
| 1 seguimiento | ninguno | `PlateR` gira con `PlateL` |
| 2 secuencias | `CTRL-SEQ-<name>` | Un deslizador para cada una |
| 3 formas | ninguno | Valores guardados de los deslizadores |

El ejemplo actualizado superó el Rig Validator sin problemas notificados. También superó las comprobaciones de recarga con Auto Run Python Scripts desactivado, incluidos todos los controles individuales y las tres formas.

## Qué probar después {#try-next}

Para editar la correspondencia del seguimiento:

1. Activa **Curve** en `PlateR Follow`.

2. Remodela la correspondencia en el Graph Editor.

Para otra pose, guarda una cuarta forma, `Carry`, con la hoja plegada y el cabezal levantado.

Para animar y exportar:

1. Inserta claves de las formas a lo largo de los fotogramas con **Go and Key**.

2. Exporta los huesos `DEF-` (consulta [Herramientas de VRChat](08-vrchat.md)).

## Vínculo de engranajes {#gear-link}

Crescent Rose no tiene una pareja de engranajes, por lo que este rig no incluye un vínculo de engranajes. Un vínculo de engranajes hace girar una bisagra cuando gira otra, según una relación de dientes. Algunos ejemplos son una manivela y una rueda, o una cremallera que convierte la rotación en un deslizamiento. Consulta [Vínculo de engranajes](07-mechanisms.md#gear-link).

## Créditos {#credits}

Modelo de Crescent Rose de amandangm, https://sketchfab.com/3d-models/crescent-rose-dcb6bfbb3b824c01a182fa131fe35824, CC BY 4.0. Este tutorial utiliza una versión dividida, escalada y con rig. Crescent Rose es un diseño de Rooster Teeth Productions. Este es un recurso de tutorial creado por aficionados.

[← Contenido](index.md)
