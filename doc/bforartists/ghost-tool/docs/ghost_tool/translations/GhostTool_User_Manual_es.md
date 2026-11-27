<a id="ghost-tool-433-user-guide"></a>

# Guía del usuario de Ghost Tool 4.3.3

Ghost Tool muestra mallas fantasma, trayectorias y marcadores de movimiento editables en Bforartists. Las mallas fantasma, también llamadas piel de cebolla, muestran el objetivo en otros momentos de la animación. Las trayectorias muestran su movimiento. Los marcadores de movimiento son puntos editables en esas trayectorias. Esta guía describe la versión 4.3.3.

Las capturas de pantalla muestran Ghost Tool 4.3.3 en la compilación suministrada de Bforartists 5.2.3. Los paneles de ajustes nativos pueden mostrar Tear Off Panel en su barra de título.

La versión 4.3.2 añadió el plegado en la Línea de tiempo y un espacio entre los dos iconos de fantasma. La versión 4.3.3 puede generar previsualizaciones mientras el puntero de la Línea de tiempo de Anim Assist está inactivo. Las operaciones de edición en curso aún pausan el muestreo.

El [ZIP de instalación de Ghost Tool 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/ghost-v4.3.3/b4_ghost_tool_v4.3.3.zip) instala el complemento independiente. Las [notas de la versión 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/RELEASE-NOTES.md) y el [registro del paquete](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/package-receipt.json) contienen los registros de verificación de la versión y la suma de comprobación.

<a id="install-and-find-ghost-tool"></a>

## Instalar y localizar Ghost Tool

La compilación de prueba personalizada/nativa suministrada incluye Ghost Tool 4.3.3. Sus preferencias de fábrica activan el complemento. Esta compilación no requiere instalar el ZIP por separado ni activarlo manualmente. Las ubicaciones de la barra de herramientas, el estante de herramientas, el panel lateral y Preferencias descritas abajo también se aplican a ella.

Para instalar el complemento independiente:

1. Descargue `b4_ghost_tool_v4.3.3.zip`.

2. Abra Editar > Preferencias > Complementos > Instalar desde el disco.

3. Seleccione el ZIP.

4. Active Ghost Tool.

5. Tras sustituir una versión instalada, reinicie Bforartists.

6. Compruebe que Preferencias indique la versión 4.3.3.

Los cambios del repositorio no actualizan automáticamente un complemento instalado. Un ZIP antiguo instala su versión original.

Estas instrucciones instalan el complemento independiente. La versión integrada propuesta depende del PR [7067](https://github.com/Bforartists/Bforartists/pull/7067) de Bforartists. Ese PR seguía sin fusionarse el 2026-11-19. Las compilaciones oficiales ya publicadas de Bforartists aún no incluyen esta integración propuesta.

Por defecto, Ghost Tool usa Barra superior en la fila nativa Opciones de herramientas de la Vista 3D. Cuando los encabezados nativos están arriba, esta fila queda debajo del encabezado principal de la vista. La fila sigue la alineación de los encabezados nativos.

El panel Preferencias también ofrece Panel lateral derecho (N) y Estante de herramientas izquierdo (T). Ghost Tool cambia las antiguas opciones guardadas de Top Header a Barra superior.

![Preferencias de Ghost Tool 4.3.3](images/es/4.3.3-preferences.png)

*Figura 1. La compilación suministrada activa Ghost Tool 4.3.3. Ubicación de controles muestra Barra superior.*

Los controles nativos de herramientas y modos siguen disponibles. Las vistas estrechas o divididas mantienen todos los controles de la barra Ghost en el mismo orden.

1. Arrastre horizontalmente la fila nativa con el botón central del ratón para acceder a los controles fuera de la anchura visible.

2. Si los controles Ghost están ocultos, seleccione Vista > Mostrar barra de fantasmas.

3. Guarde las preferencias para conservar las opciones de visualización.

<a id="set-the-interface-language"></a>

## Definir el idioma de la interfaz

La versión candidata de localización de Ghost Tool admite inglés, japonés, coreano, chino simplificado, portugués, español y francés. Estas instrucciones de idioma se aplican a esa versión candidata.
Los controles de idioma de Bforartists requieren una compilación compatible con traducciones.

1. Abra Editar > Preferencias > Interfaz.

2. En Idioma, seleccione el idioma necesario.

3. Para un idioma distinto del inglés, active Interfaz, Descripciones y Reportes en Traducir.

4. Abra las preferencias del complemento Ghost Tool.

5. Establezca Idioma en Idioma de interfaz.

Idioma de interfaz hace que los textos propios de Ghost Tool sigan el idioma de la interfaz de la aplicación.
Desactivar Interfaz devuelve al inglés los textos propios con selección automática de idioma.
Elegir explícitamente un idioma de Ghost Tool cambia sus textos propios. Los controles y las descripciones nativos siguen usando el idioma de la aplicación.
Use ajustes de idioma coincidentes para toda la interfaz.
Los nombres existentes de objetos y huesos y los identificadores de datos guardados conservan su texto original.

<a id="quick-start-inspect-an-animated-target"></a>

## Inicio rápido: inspeccionar un objetivo animado

1. Seleccione un objeto animado o un hueso en pose.

2. Active el primer icono de fantasma.

3. Haga clic en Fantasmas para mostrar las previsualizaciones de malla.

4. Defina Antes y Después por separado.

5. Seleccione Alambre o Sólido para la apariencia de la malla.

6. Mantenga pulsado Fantasmas para ajustar el muestreo y la apariencia.

7. Haga clic en Trayectorias para mostrar una trayectoria.

8. Haga clic en Añadir trayectoria seleccionada para conservar otro objetivo seleccionado.

9. Active Visualización de marcadores para mostrar puntos editables en una trayectoria añadida.

10. Haga clic en Arrastrar.

11. Seleccione un marcador en la Vista 3D.

12. Mueva el marcador.

13. Confirme el movimiento.

14. Seleccione otro marcador para continuar la edición.

15. Para salir del modo de arrastrar marcadores, haga clic de nuevo en Arrastrar o pulse Escape.

![Cubo animado con previsualizaciones de mallas fantasma](images/es/4.3.3-overview.png)

*Figura 2. Las mallas fantasma en caché rodean el cubo animado. El primer icono de fantasma activa Ghost Tool.*

Cuando no existe un objetivo de trayectoria, Trayectorias puede añadir el objetivo animado seleccionado. Seguir selección muestra la selección actual. Los objetivos añadidos con Añadir trayectoria seleccionada permanecen en la lista de trayectorias.

<a id="read-the-top-toolbar-from-left-to-right"></a>

## Leer la barra superior de izquierda a derecha

![Barra superior completa de Ghost Tool](images/es/4.3.3-toolbar-wide.png)

*Figura 3. La barra superior conserva el orden de controles indicado, desde el icono general de fantasma hasta Ajustes.*

| Control | Acción |
| --- | --- |
| Ghost Tool | Activa o desactiva la herramienta completa. Manténgalo pulsado para abrir los ajustes de actualización. |
| Fantasmas | Muestra u oculta mallas fantasma. Manténgalo pulsado para ajustar el muestreo y la apariencia. |
| Antes / Después junto a Fantasmas | Define cantidades independientes de muestras de malla. Cada número tiene botones de menos y más. |
| Alambre / Sólido | Selecciona el estilo de visualización de la malla. |
| Trayectorias | Muestra u oculta trayectorias. Manténgalo pulsado para ajustar el muestreo y las líneas. |
| Antes / Después junto a Trayectorias | Define cantidades independientes de muestras de trayectoria. Cada número tiene botones de menos y más. |
| Añadir trayectoria seleccionada | Conserva el objetivo seleccionado en la lista de trayectorias. |
| Seguir selección | Muestra una trayectoria de la selección actual. Manténgalo pulsado para abrir Resaltar trayectoria activa. |
| Arrastrar | Activa el modo de arrastrar marcadores para ediciones repetidas. Manténgalo pulsado para abrir los ajustes de edición de movimiento. |
| Fijar | Selecciona un marcador para fijarlo o liberarlo. Manténgalo pulsado para abrir Liberar todos los marcadores. |
| Visualización de marcadores | Muestra u oculta marcadores de trayectoria editables. Manténgalo pulsado para ajustar el muestreo y las etiquetas. |
| Estilo del arco | Abre las opciones Sólido, Color por velocidad y Desvanecer. |
| Marcas de espaciado | Muestra u oculta indicadores de espaciado. Manténgalo pulsado para abrir Indicadores de aceleración. |
| Ajustes | Abre los controles avanzados. |

El primer icono de fantasma controla la herramienta completa. Fantasmas controla por separado la visibilidad de las mallas. Desactivar la herramienta completa también desactiva la edición de marcadores y asas.

Las mallas ocultas conservan el estilo seleccionado. Alambre o Sólido selecciona un estilo. Fantasmas controla si las mallas son visibles.

Visualización de marcadores es el rombo inmediatamente a la derecha de Fijar. Las etiquetas aparecen cuando el puntero está sobre un control.

Estilo del arco controla el arco de movimiento de los fantasmas. Alambre/Sólido controla la visualización de las mallas. Estilo de línea en Trayectorias controla la visualización de las trayectorias.

El panel Ajustes incluye generación de marcadores, objetivos, rango, edición, Comparar, Física y opciones de apariencia. Generar y Limpiar no tienen iconos adicionales en la fila superior.

<a id="set-before-and-ahead-counts"></a>

## Definir las cantidades de Antes y Después

Cada visualización tiene dos cantidades independientes. Antes solicita muestras anteriores al cursor de tiempo. Después solicita muestras posteriores al cursor de tiempo.

1. Defina una cantidad con su campo numérico o los botones de menos y más de la barra superior.

2. Establezca una cantidad en cero para desactivar las muestras de ese lado.

El panel Opciones de piel de cebolla usa After para la cantidad Ahead de la barra. En español, ambos se muestran como Después.

![Opciones de piel de cebolla para cantidades de malla y muestreo](images/es/4.3.3-skin-options.png)

*Figura 4. El panel Opciones de piel de cebolla muestra cantidades de muestras de malla, muestreo, opacidad y Actualizar piel en tiempo real.*

Las cantidades especifican cuántas muestras solicitar. El muestreo especifica sus posiciones.

Para este ejemplo:

1. Sitúe el cursor de tiempo en el fotograma 20.

2. Establezca Antes de Fantasmas en 3.

3. Establezca Después en 2.

4. Establezca el paso de fotogramas en 2.

Las muestras anteriores solicitan los fotogramas 18, 16 y 14. Las posteriores solicitan los fotogramas 22 y 24. La animación disponible y los límites del rango pueden restringir estas solicitudes. La pose actual no cuenta como muestra de Antes o Después.

Por fotograma clave usa claves de animación en lugar de fotogramas con espaciado uniforme. Su intervalo puede omitir claves. Cambiar los campos de cantidad de Trayectorias selecciona un rango alrededor del cursor de tiempo según esas cantidades. Los modos avanzados de rango siguen sus propias reglas.

<a id="hold-a-tool-for-its-settings"></a>

## Mantener pulsado un control para abrir sus ajustes

Un botón compatible tiene dos acciones:

1. Para la acción principal, haga clic en el botón.

2. Para abrir el menú de parámetros, mantenga pulsado el botón.

Estilo del arco y Ajustes se abren con un clic normal.

| Control que debe mantener pulsado | Ajustes disponibles |
| --- | --- |
| Ghost Tool | Actualizar mallas al recorrer fotogramas, Actualizar marcadores al recorrer fotogramas, Pausar actualizaciones |
| Fantasmas | Muestreo, Cada (fotogramas), Intervalo de fotogramas clave, Opacidad, Delante, Desvanecer |
| Trayectorias | Muestreo e intervalo, Estilo de línea, Números de fotograma, Asas Bézier |
| Visualización de marcadores | Muestreo compartido con Trayectorias, Puntos de fotograma clave, Números de fotograma de marcadores |
| Arrastrar | Al soltar, Forma de curva o Suavizar vecinos, Alcance en fotogramas cercanos, Atenuación |
| Fijar | Instrucciones de fijación y Liberar todos los marcadores |
| Seguir selección | Resaltar trayectoria activa |
| Marcas de espaciado | Indicadores de aceleración |

El muestreo por paso de fotogramas usa Cada (fotogramas). El valor 1 muestrea todos los fotogramas. El muestreo por fotograma clave usa los controles de intervalo de fotogramas clave. Algunos controles ofrecen intervalos personalizados.

Los marcadores y Trayectorias comparten el muestreo. Cambiar el muestreo desde Visualización de marcadores también cambia el muestreo de Trayectorias.

Ajustes > Opciones de piel de cebolla abre los controles de malla de la Figura 4. Ajustes > Trayectorias abre los controles de objetivos y asas de la Figura 7.

<a id="use-the-bottom-timeline-toolbar"></a>

## Usar la barra inferior de la Línea de tiempo

La franja compacta está junto a los botones nativos de la Línea de tiempo, en la misma fila. No añade otra fila debajo de la barra de la Línea de tiempo.

1. Active el icono de fantasma izquierdo para mostrar los demás controles.

2. Desactive ese icono para plegar la franja.

Con Ghost Tool activo, un espacio visible separa el icono general de activación del icono Fantasmas de las mallas. Estos comportamientos comenzaron en la versión 4.3.2.

![Franja expandida de Ghost Tool en la Línea de tiempo](images/es/4.3.3-timeline-enabled.png)

*Figura 5. La franja activa de la Línea de tiempo muestra cantidades de muestras de malla, estilos de visualización, edición de marcadores y controles de trayectorias.*

![Franja plegada de Ghost Tool en la Línea de tiempo](images/es/4.3.3-timeline-collapsed.png)

*Figura 6. Con Ghost Tool desactivado, solo queda su icono general de fantasma junto a los controles nativos de la Línea de tiempo.*

La franja activa tiene este orden de izquierda a derecha:

1. Activación general de Ghost Tool.

2. Visualización de mallas en Fantasmas.

3. Cantidades de muestras de malla Antes y Después.

4. Estilos de malla Alambre y Sólido.

5. Arrastrar marcadores.

6. Rombo de marcadores editables.

7. Visualización de Trayectorias.

8. Cantidades de muestras de trayectoria Antes y Después.

Cada par de cantidades sigue el mismo orden temporal Antes/Después que la barra superior. La Línea de tiempo usa campos numéricos nativos compactos.

1. Para ajustar el muestreo y la visualización, mantenga pulsado Fantasmas o Trayectorias en la Línea de tiempo.

El menú incluye Fotograma a fotograma, Por fotograma clave e intervalos de muestreo. Más ajustes de fantasmas abre las opciones completas.

El rombo inferior muestra u oculta marcadores editables. Su menú independiente de pulsación prolongada está en el botón Visualización de marcadores de la barra superior. Comparar contiene controles de estados guardados en los ajustes avanzados.

El encabezado del Editor de curvas también ofrece la activación general y una sección de trayectorias cuando Ghost Tool está activo.

<a id="drag-markers-repeatedly"></a>

## Arrastrar marcadores repetidamente

1. Active Ghost Tool.

2. Active los marcadores editables de un objetivo animado.

3. Haga clic en Arrastrar.

4. Haga clic en un marcador visible de la Vista 3D.

5. Mueva el marcador.

6. Confirme el movimiento.

Si hace clic en un espacio vacío, el selector sigue esperando. Tras confirmar un movimiento, Arrastrar permanece activo para otra edición. Todos los botones de arrastrar marcadores comparten este modo.

Para detenerlo:

1. Haga clic de nuevo en Arrastrar o pulse Escape.

Durante un movimiento, Escape cancela ese movimiento. Ghost Tool restaura las curvas y posiciones originales de los marcadores de esa operación. Los movimientos confirmados anteriormente quedan como ediciones separadas.

1. Para revertir movimientos confirmados anteriormente, use Deshacer.

Desactivar Ghost Tool termina la edición. La pérdida del objetivo, un cambio de archivo o historial y el cierre del complemento también terminan o cancelan las sesiones afectadas.

El arrastre de asas de trayectoria también permite selecciones repetidas.

![Controles de objetivos y asas de Trayectorias](images/es/4.3.3-path-targets.png)

*Figura 7. El panel Trayectorias conserva el cubo animado como objetivo. Este ejemplo activa Marcadores y Asas.*

1. Active Asas Bézier en los ajustes de Trayectorias.

2. Inicie la acción de arrastrar asas.

3. Seleccione un asa visible.

4. Mueva el asa.

5. Confirme el movimiento.

6. Seleccione otra asa para continuar.

El acceso mediante Shift+G sigue disponible. Durante el arrastre de asas, Alt activa o desactiva el comportamiento de alineación de las asas. Escape cancela un movimiento de asa en curso y sale del modo.

<a id="choose-smooth-or-sharp-motion-edits"></a>

## Elegir ediciones de movimiento suaves o angulosas

1. Mantenga pulsado Arrastrar.

2. Examine Al soltar.

3. Seleccione Remodelar asas o Insertar fotograma clave.

Remodelar asas cambia las asas Bézier existentes para que la curva pase por la muestra movida. No añade ningún fotograma clave.

Forma de curva ofrece tres opciones:

| Opción | Efecto |
| --- | --- |
| Libre | Las asas se ajustan sin restricciones de ángulo. |
| Bloqueado | Los ángulos de las asas permanecen fijos. Sus longitudes pueden cambiar. |
| Suave | La influencia de las asas se redistribuye por el segmento. |

Ajustes > Editar movimiento contiene las mismas opciones de Al soltar y Forma de curva que el menú abierto al mantener pulsado Arrastrar.

![Ajustes de Remodelar asas en Editar movimiento](images/es/4.3.3-reshape-options.png)

*Figura 8. Editar movimiento muestra Remodelar asas con el tratamiento Libre de la curva. Alcance controla la influencia en los fotogramas cercanos.*

Insertar fotograma clave escribe una clave en el fotograma del marcador. Tras insertarla, Suavizar vecinos puede suavizar las asas de las claves adyacentes. Alcance en fotogramas cercanos y Atenuación controlan la influencia en los fotogramas circundantes.

![Controles de fotogramas clave y fijación en Editar movimiento](images/es/4.3.3-edit-motion.png)

*Figura 9. Editar movimiento muestra Insertar fotograma clave, Suavizar vecinos, suavizado de movimiento y controles de fijación. Dibujar claves necesita un trazo de anotación.*

La distancia entre muestras también afecta a la línea visible. Las muestras muy separadas producen una línea poco detallada aunque la curva de animación sea suave.

1. Para inspeccionar el resultado, seleccione un paso de fotogramas menor.

Las muestras de visualización adicionales no cambian la interpolación de la animación ni la forma de las asas.

<a id="pin-markers-and-manage-path-targets"></a>

## Fijar marcadores y gestionar objetivos de trayectorias

1. Haga clic en Fijar.

2. Haga clic en un marcador visible para alternar su estado de fijación.

3. Para seleccionar otro marcador, haga clic de nuevo en Fijar.

Fijar selecciona un marcador cada vez. No permanece activo como Arrastrar. Varios marcadores pueden permanecer fijados al mismo tiempo.

Los marcadores fijados mantienen su posición durante la remodelación. Una actualización conserva los registros coincidentes de marcadores fijados.

Para liberar todos los marcadores fijados:

1. Mantenga pulsado Fijar.

2. Seleccione Liberar todos los marcadores.

Un objetivo de trayectoria añadido conserva un objeto o hueso en la lista de trayectorias. No mantiene todas las muestras de animación en el estado de un único momento. Seguir selección cambia la previsualización de la selección. Los objetivos añadidos con Añadir trayectoria seleccionada permanecen en la lista de trayectorias.

La lista de trayectorias de Ajustes contiene los controles de objetivos. Visualización de marcadores muestra puntos editables en las trayectorias añadidas. La opción Puntos de fotograma clave ofrece una ayuda de visualización independiente.

La Figura 7 muestra la lista de trayectorias. La Figura 9 muestra Fijar y la opción de liberar todos en Editar movimiento.

<a id="live-updates-and-native-animation-editing"></a>

## Actualizaciones en tiempo real y edición nativa de animación

Actualizar marcadores en tiempo real y Actualizar piel en tiempo real están desactivados por defecto. Las escenas existentes mantienen sus valores guardados. Con estas opciones desactivadas, la última previsualización actualizada permanece al recorrer fotogramas.

1. Para abrir Actualizar marcadores al recorrer fotogramas y Actualizar mallas al recorrer fotogramas, mantenga pulsado el icono general de fantasma.

Estos controles usan los mismos ajustes de actualización de marcadores y mallas. Pausar actualizaciones interrumpe temporalmente las actualizaciones automáticas.

Ajustes > Opciones de marcadores contiene los mismos controles de actualización de marcadores. La Figura 4 muestra Actualizar piel en tiempo real en Opciones de piel de cebolla.

![Opciones de marcadores con controles de actualización en tiempo real](images/es/4.3.3-marker-options.png)

*Figura 10. El panel Opciones de marcadores contiene Actualizar marcadores en tiempo real, Pausar actualizaciones y el retraso de actualización.*

Durante las operaciones nativas de movimiento, rotación, escala y manipuladores, Ghost Tool mantiene la última previsualización. No recorre los fotogramas de animación durante esas operaciones. Tras confirmar o cancelar, espera a que la edición se estabilice. Después actualiza los fantasmas existentes.

La opción «Claves automáticos» puede permanecer activada. Sin inserción automática de claves:

1. Confirme la pose.

2. Inserte la clave deseada.

Generar en los controles avanzados de marcadores regenera las previsualizaciones cuando se solicita.

En la versión 4.3.3, Ghost Tool puede generar marcadores y pieles de cebolla mientras el puntero de la Línea de tiempo de Anim Assist está inactivo. Esta excepción solo se aplica a ese gestor pasivo del puntero.

Los controles deslizantes activos de Anim Assist, las transformaciones, los manipuladores, el recorrido de fotogramas y las operaciones modales desconocidas aún pausan el muestreo.

1. Antes de generar de nuevo, termine la operación en curso.

La corrección no cambia los valores predeterminados de actualización de las previsualizaciones ni el comportamiento de la animación de origen.

Los controles avanzados aún contienen Objetivos de marcadores, fuentes de piel de cebolla, rango, subdivisión y ajustes de apariencia. Los controles de visibilidad de marcadores y piel en caché ocultan o muestran las previsualizaciones existentes sin regenerarlas.

Limpiar todos los fantasmas quita los marcadores y las pieles de cebolla.

1. Para ocultar las previsualizaciones sin quitarlas, use los controles de visibilidad.

No puede seleccionar marcadores ocultos con un clic ni con selección por recuadro.

<a id="save-compare-and-restore-snapshots"></a>

## Guardar, comparar y restaurar estados

1. Abra Ajustes.

2. Abra Comparar.

3. Seleccione el Ámbito deseado.

4. Confirme el objetivo de captura mostrado.

5. Active los marcadores del objetivo seleccionado.

6. Haga clic en Guardar estado.

![Comparar con un estado guardado de la referencia Motion](images/es/4.3.3-compare.png)

*Figura 11. Comparar contiene el estado guardado de la referencia Motion y sus controles Ocultar, Restaurar, Guardar variante y Borrar.*

Ámbito ofrece Objeto activo / Huesos seleccionados, Trayectoria seleccionada, Canales de marcadores seleccionados y Todos los marcadores de la escena.

Los estados guardados conservan las muestras en el estado capturado, además de los fotogramas clave y las asas capturados. Los estados permanecen en la escena tras guardar y volver a abrir. Desactivar y reactivar el complemento también los conserva.

Ocultar o Mostrar cambia la superposición del estado guardado sin modificar la animación. Guardar variante crea un estado alternativo independiente y registra su origen. El alternativo permanece si borra el estado padre.

La escena puede conservar diez estados guardados.

1. Al alcanzar el límite, borre los registros innecesarios antes de guardar otro estado.

La captura, las variantes, el vínculo, la visibilidad, el borrado y la restauración admiten Deshacer y Rehacer nativos.

Antes de escribir, Restaurar valida la identidad de la escena, objeto, acción, contenedor de la acción, hueso y canal. Restaura las curvas capturadas y los registros de marcadores del ámbito del estado guardado. También actualiza la visualización cuando las actualizaciones en tiempo real están desactivadas o pausadas.

Restaurar no cambia objetos ajenos ni modificadores arbitrarios de acción. Las referencias antiguas que solo contienen muestras restauran valores muestreados adecuados cuando Ghost Tool puede remodelar las curvas.

Los objetivos sustituidos requieren un vínculo explícito. El vínculo asocia una referencia con su objetivo. Los contenedores de acción compartidos impiden el vínculo.

1. Antes de vincular, use Hacer de único usuario para independizar los datos de animación.

Vincular al objetivo activo admite, por referencia, un objeto original y sus canales de huesos identificados por nombre. Las referencias importadas con varios objetos siguen visibles y sin vínculo. Ghost Tool no puede vincular esos objetos a un único objetivo.

Los vínculos siguen los cambios de nombre de los huesos. Tras guardar y volver a abrir, la identidad del canal identifica la curva. La reversión restaura los valores originales de la curva tras cancelar. Durante una operación, Ghost Tool no escribe valores de reversión de las curvas originales en las curvas sustitutas.

<a id="transfer-snapshots-and-use-advanced-tools"></a>

## Transferir estados y usar herramientas avanzadas

1. Para transferir datos de comparación, exporte los estados guardados a JSON.

Importar valida y combina registros. Si los ID coinciden con registros existentes, Importar asigna nuevos ID. Rechaza versiones no compatibles o registros que superen la capacidad. Una importación rechazada no añade registros parciales.

Las referencias importadas y antiguas siguen visibles. La restauración requiere un vínculo explícito porque JSON no demuestra la identidad del objeto original. Una importación fallida conserva los registros existentes de la escena que no se pueden leer.

![Ajustes de exportación e importación JSON de Ghost Tool](images/es/4.3.3-transfer-settings.png)

*Figura 12. El panel Ajustes contiene Exportar e Importar para datos JSON de Ghost Tool.*

Editar movimiento contiene preajustes y controles personalizados de suavizado de movimiento. Este suavizado controla cómo cambia la velocidad del movimiento. Dibujar claves convierte el trazo de anotación más largo en una trayectoria de posición. Los trazos cortos que lo cruzan identifican las claves. El diálogo Dibujar claves conserva el objetivo seleccionado.

Ajustes, el panel lateral y el estante contienen Sensación física, Apariencia, Comparar y otras herramientas avanzadas.

La Figura 9 muestra el suavizado de movimiento y Dibujar claves en Editar movimiento.

![Controles de previsualización física y grabación](images/es/4.3.3-physics.png)

*Figura 13. Física muestra previsualizaciones de trayectorias de lanzamiento y controles de Sensación física. Grabar claves escribe la previsualización en las claves de animación.*

![Controles de Apariencia para colores de marcadores y visualización de trayectorias](images/es/4.3.3-look.png)

*Figura 14. Apariencia controla los colores de los marcadores, Líneas de arco, Marcas de espaciado y etiquetas de fotograma.*

<a id="troubleshooting-and-version-evidence"></a>

## Solución de problemas y registros de versión

| Problema | Comprobación o acción |
| --- | --- |
| No aparece ninguna previsualización | Active Ghost Tool. Compruebe la animación del objetivo, la visibilidad y las cantidades distintas de cero. |
| Faltan puntos editables | Añada el objetivo a Trayectorias. Active Visualización de marcadores. |
| Las muestras parecen demasiado separadas | Reduzca el paso de fotogramas o cambie el intervalo de fotogramas clave. |
| La Línea de tiempo solo muestra un icono de fantasma | Active ese icono para expandir la franja. |
| La barra está oculta | Seleccione Barra superior en las preferencias. Seleccione Vista > Mostrar barra de fantasmas. |
| Los controles sobrepasan una vista dividida | Arrastre horizontalmente la fila nativa con el botón central del ratón. |
| El muestreo espera durante la edición | Confirme o cancele la operación de edición en curso. |
| La generación sigue bloqueada con Anim Assist inactivo | Instale Ghost Tool 4.3.3. Reinicie Bforartists. |

La Figura 1 muestra las preferencias de Ghost Tool. Las Figuras 5 y 6 muestran la franja de la Línea de tiempo expandida y plegada.

El muestreo de marcadores sigue el muestreo de Trayectorias. Las preferencias de anchura del estante izquierdo siguen disponibles. La comprobación completa de anchura y escala estaba incompleta en 4.2.11. Esta guía no afirma una nueva corrección de anchura del estante.

La implementación anterior de la barra directa se sometió a 188 comprobaciones específicas en segundo plano. Esos resultados se aplican a aquella implementación. No proceden de pruebas nuevas para este manual.

Las [notas de la versión 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/RELEASE-NOTES.md) registran comprobaciones específicas de regresión e interfaz gráfica en Bforartists 5.2.3 oficial. La comprobación gráfica usó Anim Assist 12.11.0 y recursos de usuario aislados. Verificó nueve marcadores y tres previsualizaciones de malla. Las claves de origen y el cursor de tiempo permanecieron sin cambios.

Estos registros no certifican todos los operadores, rigs de producción ni aplicaciones anfitrionas futuras. El [registro del paquete](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/package-receipt.json) registra la integridad del ZIP, la versión y la correspondencia con el código fuente.

1. Indique el objetivo, la operación y el paso que falló en el [seguimiento de incidencias](https://github.com/Axleonex/B4Artists_Toolkit/issues).
