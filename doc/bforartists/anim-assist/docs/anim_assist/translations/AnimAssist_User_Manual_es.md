<a id="anim-assist-12112-candidate-user-guide"></a>

# Guía de usuario de la versión candidata Anim Assist 12.11.2

Esta guía describe la versión candidata local y no publicada de Anim Assist 12.11.2. Incluye la corrección de la configuración de tiras de sonido de la revisión `7ec664d`. Las descargas publicadas siguen en la versión 12.11.1. La revisión del 20 de noviembre de 2026 abarcó el código fuente y la documentación.

Consulte el [registro de cambios actual](../../../../../../scripts/addons_core/B4_anim_assist/CHANGELOG.md) y el [índice de documentación](../README.md) para obtener información sobre las versiones.

Cada captura aparece junto a sus instrucciones. Cada pie de imagen indica la versión de la captura o la fecha de validación registrada. Las capturas antiguas permiten identificar los controles. No documentan nuevas pruebas de aceptación.

El manual fuente en inglés utiliza principalmente figuras de paneles de la versión 12.11.1 capturadas en la compilación suministrada de Bforartists 5.2.3, con una base Blender 5.4 Alpha, además de una figura de Sincronización labial de la versión candidata 12.11.2 capturada en Bforartists 5.2.3 oficial, con una base Blender 5.3 Alpha. Esta edición localizada utiliza nuevas capturas nativas de la versión candidata local y no publicada 12.11.2; sus pies de figura indican el contexto de captura y los límites de la evidencia. Los paneles emergentes nativos muestran claramente los controles registrados. Para usar una herramienta, abra su ubicación en el editor como se explica a continuación.

Use Planilla de tiempos para las poses y los tiempos. Use Editor de curvas para las curvas de acciones o los controladores. Use NLA Editor para los clips y las correcciones. Los controles de ayuda explican cada herramienta. Esta guía usa los nombres españoles de los controles. Los rótulos que todavía se muestran en inglés se conservan tal como aparecen.

<a id="install-and-find-the-tools"></a>

## Instalar y localizar las herramientas

<a id="install-the-standalone-add-on"></a>

### Instalar el complemento independiente

1. Descargue el [ZIP del complemento publicado 12.11.1](https://raw.githubusercontent.com/Axleonex/B4Artists_Toolkit/main/releases/b4_anim_assist_v12.11.1.zip).

2. En Bforartists, abra **Editar > Preferencias > Complementos > Instalar desde el disco**.

3. Seleccione el ZIP.

4. Active **Anim Assist**.

5. Después de actualizar, reinicie Bforartists.

El paquete independiente se llama `B4_anim_assist`. Mantenga el ZIP intacto durante la instalación.

La siguiente figura muestra la entrada integrada en la compilación suministrada. Para una copia independiente, siga los pasos de instalación del ZIP anteriores.

![Preferencias de Anim Assist: la entrada está activada, está seleccionado el idioma Español y aparecen las opciones generales de ayuda al pasar el puntero. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): e0130f45567a.](images/es/12.11.1-preferences.png)

<a id="use-a-proposed-built-in-integration"></a>

### Usar una propuesta de integración incorporada

La compilación de prueba personalizada/nativa suministrada incluye Anim Assist. Sus preferencias de fábrica activan el complemento. Esta propuesta de integración no necesita instalar un ZIP separado. Esta descripción no demuestra que las versiones oficiales de Bforartists incluyan Anim Assist.

1. Inicie la compilación personalizada suministrada.

2. Abra las ubicaciones de los editores indicadas a continuación.

3. Abra **Editar > Preferencias > Complementos > Anim Assist** para consultar sus preferencias.

No instale una segunda copia independiente sobre la integración incorporada.

La figura de preferencias anterior muestra la entrada integrada. Las figuras **Inicio en Escena** y **Configuración inicial** siguientes permiten localizar sus controles de configuración.

<a id="find-the-editor-homes"></a>

### Localizar las herramientas en los editores

La validación de ejecución anterior usó Bforartists 5.2.0 estándar, con base Blender 5.3.0 Alpha, compilación `0a1ca45552db`, y OpenGL. Esa evidencia histórica corresponde a ese entorno. Blender estándar no es compatible. Estos resultados no validan todas las demás compilaciones del programa.

- **Línea de tiempo:** la fila de herramientas de Anim Assist aparece en la parte inferior del área de trabajo. Consulte **Línea de tiempo: la fila inferior de herramientas** más adelante. Los controles de reproducción y de inserción de claves permanecen en la cabecera nativa.
- **Planilla de tiempos, Editor de curvas y NLA Editor:** la barra lateral tiene una pestaña **Anim Assist**. Su posición respecto a las pestañas nativas puede variar. El menú **Anim Assist** de la cabecera también permite acceder a las herramientas.
- **Controladores:** la pestaña **Anim Assist** de la barra lateral y el menú de la cabecera se adaptan al trabajo con controladores en el modo **Controladores** de Editor de curvas.
- **Propiedades de la escena > Anim Assist:** esta ubicación contiene la configuración del personaje, herramientas de animación de alcance más amplio, macros, ajustes y ayuda. La barra lateral de Vista 3D no tiene una pestaña Anim Assist.

Para abrir las herramientas de la barra lateral:

1. Mueva el puntero a Planilla de tiempos, Editor de curvas o NLA Editor.

2. Pulse N.

3. Seleccione la pestaña **Anim Assist**.

Para trabajar con controladores, cambie Editor de curvas al modo **Controladores**.

**Propiedades de la escena > Anim Assist > Configuración (una vez por esqueleto) > Ejecutar configuración inicial** crea la Estantería rápida general. La configuración también ofrece un espacio de trabajo. El menú circular opcional **Shift Alt D** está desactivado inicialmente. Para activarlo o cambiar su atajo, use **Ajustes**.

![Panel emergente nativo de herramientas de la escena. La Estantería rápida, los menús circulares y los grupos de herramientas aparecen juntos. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): b51ad4cc9540.](images/es/12.11.1-scene-home.png)

![Configuración inicial en un panel emergente nativo. Ejecutar configuración inicial y Añadir espacio de trabajo de Anim Assist aparecen arriba; los grupos Esqueleto y Cara quedan visibles. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 9f881805a33b.](images/es/12.11.1-scene-setup.png)

<a id="timeline-the-bottom-tool-row"></a>

## Línea de tiempo: la fila inferior de herramientas

La fila de herramientas aparece en la parte inferior de Línea de tiempo, por encima de la barra de desplazamiento horizontal nativa. No añade cabeceras, regiones ni divisiones del espacio de trabajo. Los controles de reproducción y de inserción de claves permanecen en la cabecera nativa. Para mostrar u ocultar la fila, use **Línea de tiempo > Vista > Mostrar fila de herramientas de Anim Assist**.

Los botones conservan toda su altura y unas áreas de clic correspondientes. Al cambiar el tamaño se reserva espacio sobre la barra de desplazamiento. Si suelta el separador por debajo de la altura mínima, Línea de tiempo recupera una altura suficiente para la fila. La barra de herramientas procesa los clics de la fila antes que los controles nativos del cabezal de reproducción y de selección de claves. Mantenga suficiente altura sobre la fila para examinar las claves.

De izquierda a derecha, la fila contiene:

| Control | Función |
|---|---|
| **Botón de etapa** (por ejemplo, **Todo**, con una flecha pequeña) | Muestra la etapa actual y abre la lista de etapas. |
| **Botones de familia** (Interpolación, Temporización, Curvas, Claves, Pose, Hornear, Movimiento) | Los nombres de colores abren la lista completa de herramientas de cada familia. Las herramientas de la fila siguen al nombre de su familia. |
| **Herramientas** | Los botones, iconos y deslizadores ejecutan herramientas. El texto al pasar el puntero explica cada herramienta. |
| **+N** | Abre la lista de N herramientas que no caben en la fila. |
| **Buscar** (lupa) | Busca o muestra las 96 herramientas. Cada resultado tiene controles para ejecutar o fijar la herramienta. |
| **Ajustes** | Abre Ajustes de barra de herramientas para configurar cada fila. |

1. Haga clic en un botón de etapa, un botón de familia o **+N** para abrir su lista.

2. Haga clic en un elemento para usarlo.

La lista permanece abierta al mover el puntero, incluso sobre otro editor. Al hacer clic en otro botón de familia, la lista cambia a esa familia.

Para cerrar la lista, vuelva a hacer clic en el mismo botón, haga clic fuera de ella o pulse **Esc**.

![Fila inferior de Línea de tiempo en la etapa Todo. La etapa, las familias, las herramientas, Buscar y Ajustes comparten la misma fila. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): d6e3be31eaa8.](images/es/stage-all.png)

<a id="tool-families"></a>

### Familias de herramientas

Cada familia agrupa comandos por su función. El texto de ayuda de cada herramienta indica su alcance y sus requisitos.

| Familia | Trabajo disponible |
|---|---|
| **Interpolación** | Porcentajes y arrastre de poses intermedias, intercalación, distribución y acercamiento o alejamiento respecto a las poses vecinas. |
| **Temporización** | Desplazamientos de fotogramas, preajustes de espaciado, deslizadores de tiempos, desplazamiento en cascada, inserción/eliminación de tiempo, distribución, inversión y redondeo. |
| **Curvas** | Interpolación spline/escalonada, mezcla con vecinos o con la referencia, mezcla de aceleración/desaceleración, amplificación, suavizado, tipos de manejador y marcadores de referencia. |
| **Claves** | Selección de claves visibles, rangos y extremos, ampliación de selección, tipos de clave, selección de claves de tipo Pose intermedia, Copiar y Pegar. |
| **Pose** | Reflejo, selección del opuesto, intercambio, alineación, coincidencia en espacio global/de padre/de destino y cambios configurados de propiedades del rig. |
| **Hornear** | Horneado de objeto/rango de previsualización, Horneado inteligente, reducción, tiempos enteros, creación de proxies, horneado de sesión y limpieza. |
| **Movimiento** | Trayectorias de movimiento global, actualización, diagnóstico de arcos, desplazamiento de la acción activa y su máscara de rango. |

![Comandos de la familia Pose, parte superior del menú vertical. Este detalle muestra las operaciones de reflejo, selección de opuestos, intercambio de poses y coincidencia con el origen global. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 802e5b1cdedc.](images/es/12.10.0-pose-family-left.png)

![Comandos de la familia Pose, parte inferior del mismo menú vertical. El comando de coincidencia con el origen global aparece en ambos detalles como referencia de solapamiento; debajo quedan los demás comandos de coincidencia, el cambio del esqueleto, las opciones de Pose y el acceso al panel de Anim Assist. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): cb810f94addb.](images/es/12.10.0-pose-family-right.png)

<a id="choose-a-stage"></a>

### Elegir una etapa

Una etapa contiene herramientas para una fase de la animación:

- **Todo:** una vista general con herramientas de todas las familias.
- **Bloqueo:** herramientas de Interpolación y Claves para plantear las poses.

- **Curvas:** herramientas de Curvas y Movimiento para ajustar curvas y comprobar arcos.

- **Pulido:** herramientas de Temporización y Pose para el espaciado y la simetría.

- **Preparación de entrega:** herramientas de Hornear para finalizar y exportar.

Para cambiar de etapa:

1. Haga clic en el botón de etapa situado a la izquierda de la fila.

2. Haga clic en una etapa de la lista que aparece encima.

La lista se cierra al seleccionar una etapa. Si Línea de tiempo tiene poca altura, las cinco opciones aparecen en una sola fila dentro del área útil.

También puede seleccionar una etapa con **Línea de tiempo > Vista > Etapa de Anim Assist**.

Para recorrer las etapas con la rueda:

1. Mantenga pulsado **Ctrl** sobre el botón de etapa.

2. Gire la rueda.

Cada espacio de trabajo conserva su propia etapa en el archivo guardado.

![Opciones de etapa sobre la barra de herramientas: Todo, Bloqueo, Curvas, Pulido y Preparación de entrega. El desplegable completo y el botón de la etapa actual están visibles. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 8561df7a7817.](images/es/12.10.0-stage-choices.png)

<a id="use-the-tools"></a>

### Usar las herramientas

Los botones e iconos ejecutan una herramienta al hacer clic. Los iconos de tipos de clave usan los colores de claves de Planilla de tiempos del tema. Los rombos de Pose intermedia son más pequeños. Los de Extremo son más grandes. Los iconos de manejadores usan los colores de manejadores de Editor de curvas.

1. Pase el puntero sobre un icono para leer su nombre.

2. Si una herramienta aparece desactivada, pase el puntero para leer su requisito, como tener claves seleccionadas.

3. Haga clic en un botón o icono disponible para ejecutar su herramienta.

Los **deslizadores integrados** permanecen en la fila. Un clic sin arrastrar no cambia nada.

1. Arrastre la pista para previsualizar un cambio.

2. Suelte el botón del puntero para aplicar el cambio.

Durante el arrastre, pulse **Esc** o haga clic con el botón derecho para cancelar. La cancelación restaura las claves originales.

- Para un movimiento más preciso, mantenga pulsado **Shift** durante el arrastre.
- Para ajustar al incremento de la herramienta, mantenga pulsado **Ctrl** durante el arrastre.

Para introducir un valor exacto durante el arrastre:

1. Escriba el número.

2. Pulse **Enter** para aplicarlo.

Las **marcas** son preajustes de la pista de un deslizador. El arrastre se ajusta a las marcas cercanas. Para aplicar el valor exacto de un preajuste, haga clic en su marca.

El número a la derecha de un deslizador integrado abre un campo de valor exacto. Para aplicar el valor predeterminado de la herramienta, pulse **R**.

Los **deslizadores emergentes** muestran su nombre en la fila. Arrastrar y hacer clic abren modos emergentes distintos.

Para un deslizador emergente temporal:

1. Arrastre el nombre para abrir el deslizador.

2. Suelte el botón del puntero para aplicar el cambio.

Para mantener abierto el deslizador emergente:

1. Haga clic una vez en el nombre.

2. Arrastre la pista para previsualizar un cambio.

3. Haga doble clic o clic fuera para aplicar el cambio.

Para cancelar un cambio del deslizador emergente, pulse **Esc**.

Para abrir **Ajustes de herramientas de animación** de una herramienta, haga clic sobre ella con el botón derecho.

Los diez deslizadores numéricos son Pose intermedia, Suavizar, Vecinas, Hacia referencia, Suavizado, Amplificar, Escala temporal, Desplazamiento temporal, Desplazamiento temporal y Reducir.

- **Pose intermedia** mezcla la pose anterior y la siguiente. Los valores inferiores a 0% o superiores a 100% se extienden más allá de esas poses.
- **Escala temporal** cambia el espaciado de las claves. Por debajo de 100%, las claves se acercan y la reproducción se acelera. Por encima de 100%, las claves se separan y la reproducción se ralentiza. **Desplazamiento temporal** desplaza en el tiempo la acción del objeto activo.
- **Desplazamiento temporal** mueve las claves posteriores al cabezal de reproducción la cantidad de fotogramas seleccionada. El movimiento hacia fotogramas anteriores se detiene un fotograma después del cabezal.
- **Reducir** elimina claves si el cambio resultante de la curva se mantiene por debajo de la tolerancia seleccionada. Las claves desaparecen durante la previsualización. Pulse **Esc** para restaurarlas.
- **Hacia referencia** mezcla hacia el fotograma de referencia. **Establecer referencia** guarda ese fotograma. **Amplificar** escala el movimiento respecto a esa referencia.

Las herramientas que abarcan toda la acción, como Desplazamiento temporal, afectan a más claves que las seleccionadas. Antes de cambiar una acción completa, consulte el texto de ayuda y las opciones de escena.

![Deslizador emergente de Escala temporal, abierto sobre el control correspondiente de la barra. La instrucción sigue en inglés por una carencia del catálogo de origen. Su significado es: arrastre para ajustar; haga doble clic o clic fuera para aplicar; Esc cancela. La imagen documenta esta ayuda real en inglés y no acredita una interfaz completamente traducida. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 371289315439.](images/es/12.10.0-timing-popout.png)

<a id="default-rows"></a>

### Filas predeterminadas

Cada fila tiene un conjunto predeterminado fijo. Las siguientes listas indican los controles de izquierda a derecha, en orden de trabajo.

- **Todo:** la fila comienza con el deslizador Pose intermedia, con marcas en 25, 50 y 75%. Le siguen los iconos de desplazamiento -1f/+1f y el emergente Escala temporal. A continuación vienen el deslizador Suavizar y los iconos Copiar, Pegar, Reflejar seleccionados, Hornear objeto y Trayectorias, en ese orden. El ojo de Trayectorias muestra u oculta las trayectorias de movimiento global.

![Fila Todo, detalle izquierdo. El detalle derecho procede de la misma captura y comparte controles completos como referencia de solapamiento. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 972b0c03641a.](images/es/12.10.0-all-row-left.png)

![Fila Todo, detalle derecho. El solapamiento con el detalle izquierdo permite reconocer los controles de la misma fila; las imágenes no están unidas ni retocadas. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): ff9e5fbfa95c.](images/es/12.10.0-all-row-right.png)

- **Bloqueo:** el deslizador Pose intermedia abarca de -25% a 125%. Sus marcas son -25, 25, 50, 75 y 125. Las marcas -25 y 125 se extienden más allá de las poses que delimitan el intervalo. Las de 25 y 75 mezclan hacia ellas. A continuación aparecen los iconos Intercalado y Distribuir. Después vienen Seleccionar rango de fotogramas, Todas las claves y Finales, seguidos de los iconos izquierdo y derecho de Ampliar selección. Les siguen los rombos Marcar como fotograma clave, Pose intermedia, Extremo y Pausa en movimiento. Los iconos Copiar y Pegar terminan la fila.

![Fila Bloqueo, detalle izquierdo. El detalle derecho procede de la misma captura y comparte controles completos como referencia de solapamiento. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 418198c69937.](images/es/12.10.0-block-row-left.png)

![Fila Bloqueo, detalle derecho. El solapamiento con el detalle izquierdo permite reconocer los controles de la misma fila; las imágenes no están unidas ni retocadas. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 444e6938f1d0.](images/es/12.10.0-block-row-right.png)

- **Curvas:** el icono de curva A curvas aparece primero. Le siguen los deslizadores Vecinas, Suavizado y Suavizar. Después está el icono de destino Establecer referencia, seguido de los deslizadores Hacia referencia y Amplificar. A continuación aparecen los iconos de manejador Automático limitado, Vector y Libre. Trayectorias termina la fila.

![Fila Curvas, detalle izquierdo. El detalle derecho procede de la misma captura y comparte controles completos como referencia de solapamiento. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 62f4e09e1572.](images/es/12.10.0-spline-row-left.png)

![Fila Curvas, detalle derecho. El solapamiento con el detalle izquierdo permite reconocer los controles de la misma fila; las imágenes no están unidas ni retocadas. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 0a8bc6b2b3dc.](images/es/12.10.0-spline-row-right.png)

- **Pulido:** la fila comienza con -1f/+1f. Le sigue el deslizador Escala temporal, con marcas en 80, 90, 110 y 120%. Después aparecen dos controles llamados Desplazamiento temporal: el primero desplaza la acción y el segundo mueve las claves posteriores al cabezal. Este último tiene marcas en -1 y 1. Ajustar viene a continuación y redondea los tiempos de las claves. Los iconos Seleccionar opuestos, Reflejar seleccionados, Reflejar activo y Intercambiar terminan la fila.

![Fila Pulido, detalle izquierdo. El detalle derecho procede de la misma captura y comparte controles completos como referencia de solapamiento. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): d602eb74ee7a.](images/es/12.10.0-polish-row-left.png)

![Fila Pulido, detalle derecho. El solapamiento con el detalle izquierdo permite reconocer los controles de la misma fila; las imágenes no están unidas ni retocadas. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 595500145e00.](images/es/12.10.0-polish-row-right.png)

- **Preparación de entrega:** el icono Hornear objeto aparece primero, seguido de Hornear rango de previsualización y Horneado inteligente. A continuación viene Reducir, con marcas en 0.001, 0.01 y 0.05. Después aparece Hornear claves en fotogramas enteros, que conserva una instantánea para Restablecer temporización. Le sigue Proxy y horneado en un clic. Después están los iconos de proxy Posición, Rotación, Global y Padre. Hornear sesión y eliminar proxies sigue a esos iconos. Eliminar todas las sesiones de proxy termina la fila.

![Fila Preparación de entrega, detalle izquierdo. El detalle derecho procede de la misma captura y comparte controles completos como referencia de solapamiento. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 2bb7fecfaef8.](images/es/12.10.0-deliver-row-left.png)

![Fila Preparación de entrega, detalle derecho. El solapamiento con el detalle izquierdo permite reconocer los controles de la misma fila; las imágenes no están unidas ni retocadas. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 43758f4c00bf.](images/es/12.10.0-deliver-row-right.png)

**Buscar** incluye herramientas que no aparecen en la fila. Por ejemplo, **A escalonado** y los botones **25/50/75% Pose intermedia**.

**Copiar** incluye los manejadores. **Pegar** de Anim Assist usa los tiempos copiados. En cambio, el pegado nativo puede alinearse con el cabezal de reproducción. Antes de usar un atajo nativo en lugar de estas herramientas, consulte su descripción emergente.

La vista de la fila completa anterior muestra las ubicaciones de los controles. Los detalles de cada fila se solapan para mantener legibles las etiquetas. Las figuras de las listas de familia muestran comandos adicionales.

<a id="find-and-more"></a>

### Buscar y Más

**Buscar** (la lupa) incluye todas las herramientas.

1. Haga clic en la lupa.

2. Escriba parte del nombre de una herramienta, del nombre de una familia o un término de búsqueda, como «spacing» o «arc».

3. Haga clic en una herramienta para ejecutarla.

Para explorar sin buscar:

1. Deje vacío el campo de búsqueda.

2. Seleccione una pestaña de familia.

Para añadir o quitar una herramienta de la fila actual, haga clic en su chincheta.

Una chincheta iluminada indica que la herramienta está en la fila actual.

La fijación afecta a la fila actual, independientemente de la familia de la herramienta. **Buscar** y **Ajustes de barra de herramientas** comparten una distribución. Los cambios en cualquiera de los dos aparecen en ambos.

Si N herramientas no caben en el ancho de Línea de tiempo, **Más** aparece como **+N** antes de Buscar. Si caben todas, Más desaparece.

Para ejecutar una herramienta desde Más:

1. Haga clic en **+N**.

2. Haga clic en la herramienta.

Para disponer de más espacio, ensanche Línea de tiempo o acorte los deslizadores integrados. También puede mostrar las herramientas menos usadas como deslizadores emergentes o botones.

![Buscar herramientas con la consulta vacía: se muestran siete pestañas de familias y las diez herramientas de la familia Interpolación, junto a sus chinchetas. La pestaña Pose es una familia distinta y no está seleccionada. La captura muestra la búsqueda y los controles de fijación; no se ejecutó ninguna herramienta ni se cambió ninguna chincheta. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 8558d8208bdb.](images/es/12.10.0-find-tools.png)

![Menú Más, parte superior de la presentación actual en una sola columna de cinco herramientas. Se ven los primeros comandos y Hornear transformaciones del objeto, que también aparece completo en el detalle inferior como referencia de solapamiento. Esta geometría sustituye las columnas de la captura histórica. El borde derecho es el límite real de la ventana nativa de 710 píxeles, sin margen externo añadido. No se ejecutó ninguna herramienta. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): ae8b3cbaf99e.](images/es/12.10.0-more-left.png)

![Menú Más, parte inferior de la misma columna de cinco herramientas. Hornear transformaciones del objeto aparece completo en ambos detalles; debajo se ven el control de estelas y Pegar claves en los tiempos copiados, que está desactivado. La imagen conserva el límite derecho real de la ventana, sin añadir margen ni unir capturas. No se ejecutó ninguna herramienta. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): cfdbd04d974a.](images/es/12.10.0-more-middle.png)

![Menú Más completo con sus cinco herramientas en una sola columna y el botón real +5 que lo abre. La ventana nativa tiene 710 píxeles de ancho; su borde derecho limita la imagen y no se añadió margen externo. Pegar claves en los tiempos copiados aparece desactivado. Los detalles superior e inferior proceden de esta misma captura; no son tres columnas ni una composición de imágenes. No se ejecutó ninguna herramienta. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 3c333466e575.](images/es/12.10.0-more-right.png)

<a id="undo-from-find-menus-and-the-toolbar"></a>

### Deshacer desde Buscar, los menús y la barra de herramientas

En 12.11.1, **Buscar** y las acciones de menús nativos usan la entrada de deshacer nativa de la herramienta. No añaden una segunda entrada para la misma edición. Las acciones directas de la barra del área de trabajo conservan su punto de deshacer necesario. La finalización y la cancelación de deslizadores siguen teniendo un tratamiento separado.

1. Termine la acción o el gesto del deslizador.

2. Use **Deshacer** nativo para restaurar el resultado anterior.

3. Examine las claves y el movimiento antes de continuar.

Algunos controles de selección, navegación de ajustes y otras operaciones sin edición no crean una entrada de deshacer de animación. Las entradas del historial difieren según el control.

![Sección superior del menú Editar nativo. Deshacer y Rehacer están desactivados en el estado capturado; Historial de deshacer está disponible como submenú. La imagen no muestra el menú completo ni demuestra la ejecución de estas operaciones. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): be1633d0d454.](images/es/5.2.3-native-undo-menu.png)

<a id="change-what-a-row-shows"></a>

### Cambiar lo que muestra una fila

1. Haga clic en **Ajustes**, a la derecha de la fila.

2. En **Fila**, seleccione **Todo**, **Bloqueo**, **Curvas**, **Pulido** o **Preparación de entrega**.

3. Haga clic en la cabecera de una familia para abrir sus herramientas.

4. Seleccione el modo **Visualización** de cada herramienta.

5. Para las herramientas con icono, seleccione **Etiqueta o Icono**.

6. Para un deslizador integrado, ajuste en su lugar **Ancho** en el segundo campo.

7. Para mover una herramienta dentro de su familia, haga clic en sus **flechas arriba y abajo**.

8. Para abrir Ajustes de herramientas de animación de la herramienta, haga clic en su **engranaje**.

9. Haga clic fuera del panel o pulse **Esc** para cerrarlo.

Las herramientas normales ofrecen los modos Oculto y Botón. Oculto quita la herramienta de la fila. Los deslizadores ofrecen además Deslizador emergente y Deslizador integrado.

El panel **Ajustes de barra de herramientas** se abre en la fila actual. Su selector **Fila** permite previsualizar otra fila durante la edición. Cada cabecera de familia muestra el número de herramientas visibles. Inicialmente, una etapa abre sus familias propias. Para filtrar las herramientas por nombre, use **Buscar herramienta** sobre las familias.

Los cambios aparecen inmediatamente. Cerrar el panel con un clic fuera o con Esc conserva los cambios. El panel no tiene botón OK. **Revertir cambios** restaura todas las filas al estado que tenían al abrir el panel. Cualquier fila puede contener cualquier herramienta. Añadir una herramienta de otra familia también añade a la fila el botón de esa familia.

La visualización de iconos admite tipos de clave, tipos de manejador, ampliación de selección, -1f/+1f, Intercalado, Distribuir, A curvas, A escalonado, Establecer referencia, Copiar y Pegar. También admite Reflejar seleccionados, Reflejar activo, Seleccionar opuestos, Intercambiar, Hornear objeto, los cuatro tipos de proxy y Trayectorias. Las demás herramientas muestran sus nombres.

El engranaje o un clic derecho sobre una herramienta de la fila abre **Ajustes de herramientas de animación**. Este panel configura la visualización, el rango, el valor predeterminado, el ancho, la precisión, la sensibilidad de arrastre, el ajuste, los preajustes y **Preajustes como marcas**. **Rango personalizado / Sobrepaso** permite un rango personalizado dentro de los límites de la herramienta.

Cada etapa guarda su propia visualización, etiqueta, preajustes y marcas. Todas las filas comparten los demás valores. Los ajustes de escena guardan las máscaras, los destinos y los anclajes de poses intermedias. **Opciones de herramientas de escena** abre esos ajustes.

| Ajuste | Límite |
|---|---|
| Ancho del deslizador | 80–240 píxeles lógicos. Las filas estrechas pueden acortar la pista dibujada. |
| Precisión | 0–4 decimales. |
| Sensibilidad | 10–2,000 píxeles para recorrer el rango de un deslizador emergente. |
| Preajustes | Como máximo 12 valores finitos dentro del rango permitido. |
| Rango personalizado de Pose intermedia | De -100% a 200%. |
| Rango personalizado de Escala temporal | Mínimo 1%. |
| Rango personalizado de Desplazamiento temporal | De -500 a 500 fotogramas. |
| Rango personalizado de Reducir | De 0 a 1 unidades de tolerancia. |

El rango estándar mostrado puede ser más estrecho que el rango personalizado permitido. Estos límites de configuración de la barra no son recomendaciones de tolerancia para rigs de producción.

![Parte superior visible de Ajustes de barra de herramientas para la fila Bloqueo. Se ven los controles de disposición y fila, las instrucciones, la búsqueda y las diez entradas de la familia Interpolación, con visualización, ancho, orden y engranajes. La sección inferior de Claves queda fuera de este detalle. Los puntos suspensivos de algunos textos son los que dibuja la interfaz nativa; no se afirma que todas las etiquetas aparezcan completas. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 213d34a516d2.](images/es/12.10.0-toolbar-settings.png)

![Diálogo completo de Ajustes de herramientas de animación para Arrastrar pose intermedia. Se ven los controles de rango, ajuste, preajustes y opciones de escena, además de Aceptar y Cancelar. La interfaz nativa abrevia algunas instrucciones largas con puntos suspensivos; estos se conservan y no son un recorte añadido a la imagen. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 13d723e7c678.](images/es/12.11.1-tool-settings.png)

<a id="save-load-and-reset-layouts"></a>

### Guardar, cargar y restablecer distribuciones

Una distribución contiene todas las filas: Todo y las cuatro etapas.

| Control | Resultado |
|---|---|
| **Guardar como** | Asigna un nombre y guarda la distribución actual. |
| **Cargar** | Restaura una distribución guardada. |
| **Actualizar guardado** | Sustituye la distribución guardada por las filas actuales. |
| **Renombrar** y **Eliminar** | Cambian el nombre o eliminan distribuciones guardadas. |
| **Recomendado** | Identifica la distribución fija incorporada. |
| **Restablecer Bloqueo a los valores predeterminados** | Restaura el conjunto predeterminado de esa etapa. El nombre del control cambia según la fila que se edita. |
| **Restaurar disposición recomendada** | Restaura Todo y todas las etapas. Las distribuciones guardadas siguen disponibles. |

Las preferencias del complemento guardan las distribuciones. Estas se aplican a todos los editores de Línea de tiempo.

Si las preferencias no se guardan automáticamente, haga clic en **Guardar preferencias** en Ajustes de barra de herramientas. Así conservará los cambios después de reiniciar.

Los nombres de distribuciones guardadas contienen entre 1–64 caracteres. La biblioteca admite como máximo 100 distribuciones guardadas. Cargar una distribución sustituye la disposición de trabajo. Antes de sustituir una disposición modificada, lea el control de cambios sin guardar.

Las etapas empiezan con valores predeterminados fijos. Añadir una herramienta a Todo no la añade a una etapa. Añádala por separado a cada etapa necesaria. Las preferencias del complemento no tienen control de etapa. Cada espacio de trabajo usa el botón de etapa de la fila.

La figura **Ajustes de barra de herramientas** anterior muestra los controles de distribuciones guardadas. Use ese mismo panel para configurar filas y administrar distribuciones.

<a id="hover-explanations-and-shortcuts"></a>

### Ayuda al pasar el puntero y atajos

Para ver la explicación de un control, mantenga el puntero sobre él durante aproximadamente medio segundo. **Explicaciones al pasar el puntero** controla la cantidad de texto de ayuda. Se encuentra en Editar > Preferencias > Complementos > Anim Assist > General.

La ayuda emergente, las opciones de etapa y los deslizadores emergentes permanecen sobre los botones de la barra. Línea de tiempo muestra una descripción de Anim Assist bajo el puntero. La ayuda de la barra tiene prioridad sobre Scene Strip Gizmo, situado debajo de la fila.

- **Completo:** el texto explica la función, el alcance, los requisitos y el uso de la herramienta.
- **Breve:** el texto muestra el nombre y una línea de explicación. Para una herramienta desactivada, también indica el motivo.
- **Desactivado:** la fila no muestra texto de ayuda de Anim Assist. Los botones nativos de Bforartists en paneles y menús de Anim Assist siguen mostrando el nombre de la herramienta. Bforartists siempre muestra allí una línea de descripción. Los campos de ajustes conservan su propia descripción de una línea.

Para desactivar todas las descripciones emergentes, use **Editar > Preferencias > Interfaz > Descripciones**.

El texto de ayuda solo muestra atajos si existe una asignación:

- **Atajo:** esta tecla está asignada a esa herramienta exacta de Anim Assist. Las herramientas de la fila no tienen atajos predeterminados. Para mostrar aquí un atajo, asígnelo en **Editar > Preferencias > Mapa de teclado**.
- **Tecla de Bforartists:** esta tecla ejecuta un comando nativo con la misma función. Planilla de tiempos incluye de forma predeterminada **Ctrl C** para copiar y **Ctrl V** para pegar. **A** selecciona todas las claves. **Ctrl Numpad +** amplía la selección en ambos lados. **R** escala los tiempos de las claves. **W** mueve las claves en el tiempo. Los comandos nativos pueden comportarse de forma distinta a las herramientas de Anim Assist. Pegar nativo usa el cabezal de reproducción en vez de los tiempos copiados.

![Explicación completa de Suavizar claves (arrastrar), con el control Suavizar resaltado. La herramienta acerca las claves seleccionadas a la media de sus vecinas inmediatas e indica el alcance de las curvas editables de la acción activa. Arrastre para previsualizar; suelte para aplicar; Esc cancela. Haga clic derecho para abrir los ajustes de la herramienta. Esta captura no muestra ninguna línea de atajo. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 9a589954c606.](images/es/12.10.0-hover-explanation.png)

La figura **Preferencias de Anim Assist integrado**, cerca de la instalación, muestra **Completo**, **Breve** y **Desactivado**. La figura **Ajustes** posterior muestra opciones de atajos y menús.

<a id="dope-sheet-poses-and-key-timing"></a>

## Planilla de tiempos: poses y tiempos de claves

El resumen cuenta los propietarios visibles, las curvas editables y las claves seleccionadas. Incluye controles de selección Todo/Ninguno. **Bloqueo e intercalado** aparece abierto inicialmente. Los demás grupos son **Temporización, Claves y canales, Pose y coincidencia, Hornear y finalizar y Estantería rápida**.

1. Seleccione un objeto animado o huesos de pose.

2. Muestre los canales de la acción.

3. Seleccione las claves que desea editar.

4. Use **Bloqueo e intercalado** para porcentajes de poses intermedias, intercalaciones y herramientas de arrastre.

5. Expanda las opciones de **Bloqueo e intercalado** para acceder a máscaras, preajustes y opciones de muestreo.

6. Use **Temporización** para espaciado, desplazamientos y desplazamiento en cascada.

7. Use **Claves y canales** para selección, administración de claves y metadatos.

8. Use **Pose y coincidencia** para coincidencia y reflejo.

9. Use **Hornear y finalizar** para herramientas de horneado y diagnóstico.

Para seleccionar lados de manejadores, use Editor de curvas. Planilla de tiempos conserva los tipos avanzados de manejador. Propiedades de la escena contiene la creación de macros y la configuración.

![Planilla de tiempos con los canales y las claves reales junto al grupo Bloqueo e intercalado expandido. El resumen indica dos propietarios visibles, 15 claves seleccionadas y seis curvas editables. Los nombres de objetos y acciones se conservan como datos de la escena. Esta vista documenta el contexto y los controles; no demuestra la ejecución de una operación ni una traducción completa del programa. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 51f0d5ce3df2.](images/es/12.8.0-dopesheet-tools.png)

<a id="breakdown-anchors"></a>

### Anclajes de poses intermedias

En un fotograma vacío, las claves circundantes sirven de anclajes para la mezcla. Por ejemplo, los valores 0 y 10 producen 5 al 50%.

Si el cabezal ya tiene una clave, esa clave pasa a ser el anclaje anterior. Un valor actual de 5 y uno siguiente de 10 producen 7.5 al 50%. Repetir la operación puede volver a cambiar la clave existente.

Antes de aplicar una pose intermedia, compruebe el cabezal, las claves y las máscaras.

La figura de Planilla de tiempos anterior muestra las acciones de poses intermedias y sus opciones. Cada ejemplo numérico describe una disposición distinta del cabezal y de las claves.

<a id="graph-editor-curve-shaping"></a>

## Editor de curvas: dar forma a las curvas

**Dar forma a curvas** aparece abierto inicialmente con acciones directas de forma, interpolación y manejadores. Los grupos son **Selección y canales, Dar forma a curvas, Retemporizar, Limpiar, Pose y horneado y Estantería rápida**. **Selección y canales** incluye selección de manejadores. **Limpiar** contiene administración de claves y diagnósticos. **Pose y horneado** incluye coincidencia, reflejo, poses intermedias y horneado. Sus **Opciones de pose intermedia**, inicialmente contraídas, configuran el muestreo de poses intermedias. No configuran la interpolación general de curvas.

1. Seleccione claves de acciones visibles y editables.

2. Aplique la acción de forma o de interpolación.

3. Examine la curva resultante y el visor.

La interpolación de claves seleccionadas solo afecta a claves seleccionadas, editables y visibles. Los comandos de tiempos de Gestor de claves respetan la visibilidad del editor y los bloqueos de canales. **Mover claves** e **Insertar fotogramas** se ejecutan inmediatamente. Para ajustar sus valores, use **Ajustar última operación** nativo.

Los asistentes de selección de acciones admiten **acciones de objetos**. Si el alcance está vacío, no seleccionan desde toda la acción activa. Excluyen las acciones fijadas sin conexión y los orígenes que no son objetos. La barra lateral explica esas exclusiones. Antes de usar herramientas que abarquen toda la acción, consulte sus descripciones.

![Vista del Editor de curvas con Dar forma a curvas expandido y los demás grupos visibles. El resumen indica seis claves seleccionadas y tres curvas editables de un propietario. Las curvas capturadas son en gran parte planas y se superponen cerca de cero; no se muestra una demostración de modelado de curvas. Se conservan los nombres de datos de la escena, el cabezal verde nativo y el elemento Quick del encabezado. No se acredita una interfaz completamente traducida. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 248a6040dbc0.](images/es/12.8.0-graph-tools.png)

<a id="drivers-inspect-and-shape-driver-responses"></a>

## Controladores: examinar y dar forma a las respuestas de controladores

Para usar las herramientas de controladores, cambie Editor de curvas al modo **Controladores**. La barra lateral **Anim Assist** y el menú de la cabecera muestran cuatro secciones específicas de controladores. Volver a las curvas de acciones restaura los grupos de acciones descritos arriba. El modo Controladores usa canales de controladores en vez de herramientas para claves de acciones.

<a id="driver-target"></a>

### Controlador y destino

Esta sección cuenta los controladores visibles seleccionados. Para el controlador activo, también muestra **Propietario**, **Propiedad** y **Valor actual**. Muestra **Índice de matriz** cuando corresponde. Una propiedad que no se puede resolver produce una advertencia.

1. Seleccione un canal de controlador visible en la lista de canales.

2. Examine su propietario y la propiedad controlada en **Controlador y destino**.

3. Haga clic en **Encuadrar selección** para encuadrar las curvas seleccionadas.

4. Para ver toda la vista de controladores, haga clic en **Encuadrar todo**.

**Todos los canales** y **Ninguno** cambian la selección de canales. **Seleccionar propietario** activa el objeto propietario del controlador. Los demás objetos seleccionados siguen seleccionados. El propietario debe pertenecer a la capa de vista actual y permitir la selección de objetos visibles. Los controladores de otros bloques de datos no pueden usar esta acción de selección de objetos.

Si el propietario es editable, **Silenciado** y **Bloqueado** cambian los ajustes nativos del canal del controlador activo. Un único controlador visible seleccionado sigue disponible para examinarlo después de bloquearlo. Para desbloquearlo, desactive **Bloqueado**. Si varios canales seleccionados hacen ambiguo el controlador activo, seleccione explícitamente el canal deseado.

Con una selección vacía, las cuatro secciones permanecen visibles y muestran indicaciones. No crean un controlador.

Antes de usar estas secciones:

1. Cree controladores con el flujo nativo de controladores de Bforartists.

2. Conecte esos controladores.

![Un controlador seleccionado de Empty, propiedad scale con índice 0 (escala X) y valor actual 1, en la barra lateral de Anim Assist. El controlador está desbloqueado; Interpolación y Manejadores aparecen atenuados porque no hay puntos de respuesta seleccionados. Se ven las variables, la expresión y las acciones de diagnóstico. No se editó la respuesta ni se añadió un modificador. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-21 (UTC). SHA-256 de la imagen (prefijo): f940a8d99bc5.](images/es/12.11.0-selected-driver.png)

<a id="variables-expression"></a>

### Variables y expresión

Esta sección cuenta las variables. Los controladores con script muestran **Expresión**. Los demás tipos muestran **Tipo**. La pestaña nativa **Controladores** contiene todos los ajustes editables de variables y expresiones.

1. Desbloquee el canal del controlador deseado.

2. Haga clic en ese canal para convertirlo en el controlador editable activo nativo.

3. Abra **Variables y expresión**.

4. Haga clic en **Abrir ajustes del controlador**.

5. Edite las variables, los destinos, el tipo de controlador o la expresión en la pestaña nativa **Controladores**.

6. Vuelva a **Anim Assist** para las acciones de respuesta y los diagnósticos.

El botón abre la categoría nativa de la barra lateral. No abre una copia separada del diálogo de ajustes. Un controlador bloqueado puede seguir disponible para examinarlo sin permitir la edición de sus ajustes nativos. El orden de las pestañas de la barra lateral nativa puede variar. Identifique **Controladores**, **Modificadores** y **Anim Assist** por sus nombres.

![Categoría nativa Controladores para la escala X de Empty, índice 0. La expresión real es var +1.0; la variable var toma la Posición X de Empty en espacio Global, con entrada 0.0000 y resultado 1.000. Esta vista muestra la categoría nativa traducida; no constituye una prueba de haber pulsado Abrir ajustes del controlador en esta sesión en español. No se modificó la respuesta. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-21 (UTC). SHA-256 de la imagen (prefijo): 78035b494e98.](images/es/12.11.0-native-driver-settings.png)

<a id="response-curve"></a>

### Curva de respuesta

El eje horizontal representa la entrada del controlador. El eje vertical representa la salida controlada. Los puntos de respuesta relacionan entrada y salida. Son distintos de las claves de acciones, que usan tiempo de animación.

1. Seleccione los canales de controladores visibles que desea editar.

2. Desbloquee esos canales.

3. Compruebe que sus propietarios sean editables.

4. Para cambios en puntos, seleccione puntos de respuesta o lados de manejadores.

5. Seleccione **Interpolación** o **Manejadores** en **Curva de respuesta**.

6. Examine la respuesta resultante y la propiedad controlada.

| Control | Alcance y resultado |
|---|---|
| **Interpolación** | Cambia los puntos de respuesta seleccionados en los canales de controladores seleccionados, visibles y editables. Las opciones son Constante, Lineal y Bézier. |
| **Manejadores** | Cambia los lados de manejadores seleccionados en esos canales. Si hay un punto de control seleccionado, la acción cambia ambos manejadores. |
| **Extrapolación** | Cambia los canales de controladores seleccionados, visibles y editables fuera del intervalo delimitado por sus extremos. Constante mantiene la salida. Lineal continúa la pendiente del extremo. |
| **Añadir modificador (activo)** | Añade el modificador de respuesta elegido solo al controlador editable activo. No afecta a todos los canales seleccionados. |
| **Abrir ajustes de modificadores** | Abre la pestaña nativa **Modificadores** del controlador activo. |

Las acciones de puntos requieren puntos o manejadores seleccionados. La extrapolación requiere canales editables seleccionados. Las acciones de modificadores requieren un controlador activo desbloqueado cuyo propietario sea editable. Abrir los ajustes nativos también requiere un controlador editable activo de forma nativa. Si un control está desactivado, pase el puntero para leer su requisito.

La interpolación, los manejadores, la extrapolación y la creación de modificadores admiten **Deshacer** y **Ajustar última operación** nativos. Estas acciones solo afectan a los controladores indicados. Excluyen las claves de acciones y los controladores ajenos. La validación de ejecución no cubre por separado todos los tipos de modificador nativo.

La figura del controlador seleccionado anterior sitúa **Interpolación**, **Manejadores**, **Extrapolación** y **Añadir modificador (activo)**. El destino de los modificadores nativos aparece debajo.

![Categoría nativa Modificadores del mismo controlador de escala X de Empty. La pila está vacía y Agregar modificador está visible; no se añadió ningún modificador. La captura corresponde a la ventana nativa estrecha de 710 píxeles y conserva su geometría real. Muestra el estado de la categoría, sin afirmar una pulsación de Abrir ajustes de modificadores en esta sesión en español. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-21 (UTC). SHA-256 de la imagen (prefijo): 3660aef792e2.](images/es/12.11.0-native-modifier-settings.png)

<a id="diagnostics"></a>

### Diagnósticos

1. Seleccione los canales de controladores visibles que desea examinar.

2. Abra **Diagnóstico**.

3. Haga clic en **Comprobar controladores seleccionados**.

4. Lea la ventana emergente de resultados.

5. Corrija los destinos, rutas, huesos o expresiones indicados en los ajustes nativos correspondientes.

6. Después de corregir una dependencia, haga clic en **Actualizar dependencias**.

**Comprobar controladores seleccionados** comprueba la validez de evaluación, los destinos ausentes, las rutas de propiedades sin resolver y los huesos ausentes. También informa de propietarios vinculados/de solo lectura, canales bloqueados y controladores silenciados. Si un destino de propiedad tiene un valor alternativo activado, la comprobación no comunica un fallo de ruta sin resolver para ese destino.

Las comprobaciones solo examinan controladores visibles seleccionados. No revisan el archivo completo. No demuestran que cada expresión produzca el movimiento deseado. **Actualizar dependencias** actualiza los propietarios de los controladores seleccionados y reevalúa la capa de vista. No repara expresiones, reconecta destinos, cambia puntos de respuesta ni elimina controladores.

![Resultado nativo de Diagnósticos de controladores seleccionados: «No se han encontrado problemas». El resultado corresponde únicamente al controlador seleccionado scale&#91;0&#93; de Empty, con expresión var +1.0, entrada 0 y salida 1. No certifica todos los controladores ni demuestra reparaciones automáticas, eliminaciones u otros procedimientos. La captura conserva el resultado observado; su recibo no acredita una nueva ejecución del operador en español. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-21 (UTC). SHA-256 de la imagen (prefijo): 6c25f179cbd1.](images/es/12.11.0-driver-diagnostics.png)

<a id="nla-arrange-clips-and-blend-corrections"></a>

## NLA: organizar clips y mezclar correcciones

**Organizar y temporizar** y **Mezcla y correcciones** aparecen abiertos inicialmente. **Acciones y pistas, Hornear y finalizar y Estantería rápida** aparecen cerrados. El resumen muestra el propietario, el clip activo, la acción de origen, el número de clips seleccionados, el rango de escena y el rango de origen. Los fotogramas de escena indican la posición del clip. Los de origen indican el intervalo de la acción dentro del clip.

<a id="arrange-clips"></a>

### Organizar clips

1. Seleccione los clips de acciones que desea cambiar.

2. Haga clic en el cuerpo del clip de referencia para activarlo.

3. Compruebe que el clip de referencia siga seleccionado.

4. Haga clic en **-1f/+1f** para desplazar por incrementos, o en **Mover clips seleccionados** para un movimiento nativo.

5. Para alinear los clips con el clip activo seleccionado, use **Align Starts to Active Clip / Align Ends to Active Clip**.

6. Para colocar los clips de forma consecutiva desde el inicio del clip de referencia, use **Secuenciar clips**.

7. Cambie el incremento o la separación de la secuencia en **Ajustar última operación**.

8. Expanda **Opciones de temporización** para acceder a escala, repetición, inversión e inicio/final de escena del clip activo.

Los tiempos usan fotogramas de escena. Las herramientas rechazan los conjuntos bloqueados o solapados sin realizar cambios parciales. La organización se suspende durante la edición del origen. Estas herramientas no pueden editar tiras de transición, meta ni sonido.

![Panel emergente de mezcla de la corrección de transformación seleccionada, con Combinar e Influencia animada activada. El valor 0.500 está registrado mediante una clave en el fotograma 12 y la tira de origen se conserva. Blend Options sigue en inglés y significa «opciones de mezcla». No se muestra una vista completa del editor NLA ni se demuestra aquí la ejecución de una nueva corrección. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 28617bbb5c3d.](images/es/12.8.0-nla-arrange.png)

Antes de usar acciones del clip activo, compruebe que el resumen muestre el propietario del clip, el clip y la acción.

<a id="edit-sources-and-manage-sharing"></a>

### Editar orígenes y administrar recursos compartidos

**Editar acción** entra en el modo de retoque nativo de NLA. **Abrir planilla de tiempos / Abrir editor de gráficas** reutiliza un editor adecuado sin fijar o cambia el área actual. El modo de retoque nativo transforma el tiempo de origen para clips movidos, escalados, repetidos e invertidos.

Para volver a organizar después de editar:

1. En el selector de editor, seleccione **Animación no lineal** para volver a NLA.

2. Haga clic en **Terminar edición**.

Editar una acción compartida puede afectar a otros clips. El resumen advierte del uso compartido e informa de orígenes excluidos. Silenciar y Solo afectan a la evaluación.

| Control | Resultado |
|---|---|
| **Hacer únicos los clips seleccionados** | Separa las acciones de origen de los clips seleccionados. |
| **Duplicar independiente** | Copia la acción. |
| **Duplicar vinculado** | Comparte la acción. |
| **Subir pistas seleccionadas / Bajar pistas seleccionadas** | Reordena pistas. No mueve clips entre pistas. |

**Push Down Active Action/Stash Active Action** operan sobre la acción asignada al propietario activo. Push Down requiere que la evaluación NLA esté activada. Si no hay ningún clip seleccionado, el resumen ofrece **Añadir clip de acción existente** para un objeto activo editable.

![Acciones y pistas del clip seleccionado en la pista Manual Source. Se ven los controles de duplicación, acción, pista, silencio, Solo y orden de pistas. Push Down Active Action significa pasar la acción activa a una pista NLA; Stash Active Action significa guardar la acción activa en reserva. Ambos botones siguen en inglés y están desactivados: el aviso exige una acción activa del propietario. Ninguna de estas operaciones se muestra ejecutada. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 3c2a34aa2ee9.](images/es/12.11.1-nla-actions.png)

<a id="add-a-transform-correction"></a>

### Añadir una corrección de transformación

1. Seleccione un clip de acción de origen compatible.

2. Haga clic en **Nueva corrección de transformación**.

3. Seleccione el nuevo clip de corrección.

4. Haga clic en **Editar corrección**.

5. Edite sus claves de transformación en el modo de retoque nativo.

6. Después de editar, haga clic en **Terminar edición**.

7. Mantenga neutros los canales sin modificar: posición cero, rotación cero/identidad y escala uno.

8. En el cabezal, haga clic en **0%, 50% o 100%** para insertar una clave de influencia del clip activo.

La mezcla nativa **Combinar** aplica la corrección sobre el movimiento de origen. Para usar otro valor de influencia, introdúzcalo en **Ajustar última operación**. Con influencia cero, la corrección no aporta movimiento.

La creación añade una acción de corrección independiente y una pista sobre el origen. Las correcciones admiten transformaciones de objetos y huesos de pose. La creación bloquea rigs con restricciones/controladores, huesos sin resolver y canales de origen que no sean de transformación. Explica el motivo. Estas correcciones son independientes de las herramientas generales Capas de animación de Propiedades de la escena.

Blend y Animated Influence son ajustes nativos de tira. Si Animated Influence está desactivado, la barra lateral identifica la envolvente de mezcla automática. **Blend Options** muestra Automatic Blend, las transiciones de entrada/salida y la extrapolación. Los botones de influencia crean claves de influencia nativas. No crean claves de pose en la acción de origen.

La figura **Controles de organización y corrección NLA** anterior muestra la pista de corrección, **Editar corrección**, la mezcla **Combinar** y los botones de influencia.

<a id="bake-while-retaining-the-source-stack"></a>

### Hornear conservando la pila de origen

1. Seleccione un clip del propietario que desea hornear.

2. Abra **Hornear y finalizar**.

3. Compruebe el propietario y el rango de escena que se muestran.

4. Haga clic en **Hornear en una acción nueva**.

5. Si es necesario, ajuste el rango y el incremento en **Ajustar última operación**.

6. Compruebe el nombre y el rango de la salida.

7. Antes de activar el horneado, silencie o elimine las restricciones activas que se aplicarían de nuevo.

8. Seleccione **Usar último horneado (NLA desactivado)**.

El horneado escribe las transformaciones evaluadas de objeto/pose en una acción nueva y la conserva. La acción nueva queda inicialmente **sin asignar**. Se conservan las acciones, los clips, los padres y las restricciones originales. Activar el horneado es una operación separada. **Usar último horneado (NLA desactivado)** asigna el resultado y desactiva la evaluación de la pila de origen.

Guarde la escena de origen para comparar. Cambiar el nombre no altera la propiedad de la salida. Otro objeto que adopte el nombre anterior no puede recibir esa salida. **Eliminar pistas vacías** elimina pistas vacías de forma separada.

Los atajos de Estantería rápida de NLA hacen únicos los orígenes, editan el origen activo y hornean al propietario. No ejecutan macros generales de edición de claves sobre las tiras.

![Resultado conservado de un horneado NLA de los fotogramas 1 a 24, con incremento 1. La salida Toolkit_Offer_Animated_Cube NLA Bake está sin asignar en el momento de esta captura y los originales se conservan. La prueba nativa vinculada registra que el horneado terminó; no se había ejecutado Usar último horneado. El estado posterior de la figura 38 no modifica este estado capturado. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 86df006f42ee.](images/es/12.11.1-nla-retained-bake.png)

<a id="scene-properties-and-broader-tools"></a>

## Propiedades de la escena y herramientas de alcance más amplio

**Propiedades de la escena > Anim Assist** contiene **Estantería rápida, Esta pose, Animación completa, Esqueleto, Cara, Configuración (una vez por esqueleto), Ajustes y Ayuda y diagnóstico**.

| Grupo | Trabajo |
|---|---|
| **Esta pose** | Desplazamientos de transformación, coincidencia, cambio de espacio y reflejo de poses. |
| **Animación completa** | Desplazamientos de la acción activa, trayectorias de movimiento y Capas de animación. |
| **Esqueleto** | Localizadores, proxies, ajustes de horneado y limpieza de sesiones. |
| **Cara** | Configuración de sincronización labial, conexión de destinos, previsualización y controles de horneado. |
| **Configuración (una vez por esqueleto)** | Configuración inicial y procedimientos de espacio de trabajo/sistema. |
| **Ajustes** | Ajustes compartidos, atajo circular opcional y creación de macros. |
| **Ayuda y diagnóstico** | Ayuda de herramientas, informes de diagnóstico e indicaciones de recuperación. |

**Buscar** busca herramientas existentes. **Recientes** enumera las herramientas completadas, empezando por la más reciente. **Repetir última** usa la entrada más nueva. Los comandos cancelados o sin terminar no se añaden a Recientes. Los archivos antiguos ordenan Recientes por fecha y hora. **Alternar modo de la estantería** recorre los modos de la estantería.

Para configurar macros, abra **Propiedades de la escena > Anim Assist > Ajustes**.

Las figuras **Inicio en Escena** y **Configuración inicial**, cerca de la instalación, muestran los puntos de acceso compartidos. Las figuras siguientes muestran cada panel registrado en un emergente nativo.

![Ajustes de atajos e integración. El menú circular opcional está desactivado y los campos que muestran Mayus Alt D aparecen atenuados. Se ven la comprobación de conflictos, los cuatro interruptores de menús de cabecera y las opciones de ayuda e interfaz. La imagen muestra la configuración, no una prueba de registro del atajo ni de resolución de conflictos. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 95373d744674.](images/es/12.11.1-settings.png)

![Macros predefinidas, lista de macros personalizadas vacía y opciones de procesamiento por lotes. Se muestran las cinco macros predefinidas, Añadir macro y los controles de objetos seleccionados, selección, marcadores e incremento de fotogramas. No se creó ni ejecutó ninguna macro para esta captura. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 116567176ce7.](images/es/12.11.1-macros.png)

<a id="offset-match-and-mirror"></a>

### Desplazar, hacer coincidir y reflejar

1. Seleccione el propietario animado y las claves o los huesos de pose deseados.

2. Abra **Planilla de tiempos > Anim Assist > Bloqueo e intercalado > Desplazamiento de transformación** para desplazar claves.

3. Seleccione la máscara de canales.

4. Seleccione el alcance del desplazamiento.

5. Ajuste las cantidades de desplazamiento.

6. Seleccione el espacio de transformación.

7. Use **Ajustar fotograma actual**, **Desplazar claves seleccionadas** o **Arrastre interactivo** según el alcance deseado.

8. Examine el resultado antes de usar **Reaplicar último** o **Invertir último**.

![Cantidades de desplazamiento y controles de canales, alcance, filtros y preajustes en Planilla de tiempos. Las cantidades visibles son cero; no se ejecutó ningún desplazamiento. Esta captura es posterior a la aplicación real del horneado a la acción del objeto, documentada por pruebas nativas anteriores. El contexto contiene 222 claves seleccionadas. La figura 35 conserva el estado anterior, cuando la salida aún estaba sin asignar. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): f5773a9ca9e2.](images/es/12.11.1-transform-offset.png)

**Propiedades de la escena > Anim Assist > Esta pose > Desplazamiento de pose** desplaza por incrementos los huesos de pose seleccionados o los mueve mediante arrastre interactivo. Desplazamiento de pose requiere **Modo Pose**.

Fotograma actual, Claves seleccionadas y Rango de fotogramas son alcances de desplazamiento separados. La atenuación del rango de fotogramas distribuye el desplazamiento a lo largo del tiempo. La atenuación de aceleración/desaceleración no cambia las tangentes de las curvas. Estas herramientas usan el pivote **Orígenes individuales**. No orbitan alrededor de la mediana ni del cursor.

La coincidencia ofrece acciones Global, Padre, Target, por canal, visuales/evaluadas y de matriz local. La coincidencia con un destino suele necesitar dos objetos seleccionados.

Para la coincidencia con un destino:

1. Seleccione primero el destino.

2. Seleccione el objeto que desea cambiar.

**Alinear objetos seleccionados con el activo** usa el objeto activo como referencia. Estos controles no interpretan automáticamente todos los rigs.

Antes de usar flujos de cambio de espacio compensado o IK/FK:

1. Configure las correspondencias de propiedades de conmutación.

2. Configure las cadenas.

Las herramientas de reflejo requieren un esqueleto en **Modo Pose**. **Seleccionar opuestos** cambia la selección. Las acciones de reflejo de fotograma/rango también pueden insertar claves.

Antes de usar **Reflejar pose**, **Seleccionado** o **Intercambiar**:

1. Compruebe la detección de pares y las excepciones de nombres.

2. Compruebe el espacio y el eje de reflejo.

3. Compruebe los filtros de canales.

4. Lea la descripción de la herramienta.

![Coincidencia rápida con Ajustes expandido en Vista 3D. Global, Destino, Pos., Rot. y Escala están disponibles, mientras que algunos otros comandos aparecen atenuados. Todo (TRS) y los ejes XYZ están activados; Mantener desplazamiento está desactivado y Respetar transformaciones bloqueadas está activado. No se ejecutó ninguna operación de coincidencia. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 066269ed67ef.](images/es/12.11.1-transform-match.png)

Abra **Planilla de tiempos > Anim Assist > Pose y coincidencia** para acceder a todos los ajustes de coincidencia y reflejo.

![Desplazamiento rápido de pose con un hueso seleccionado de HumanArmature en Modo Pose. Se muestran los controles de fotograma actual y arrastre, los valores de empuje y atracción, los ejes con signo y las opciones de espacio, reflejo y ajuste fino. Los controles de reaplicar e invertir están desactivados. No se modificó la pose ni se ejecutó un desplazamiento. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 38e6b2757e18.](images/es/12.11.1-pose-offset.png)

![Reflejo rápido con un hueso seleccionado de HumanArmature en Modo Pose. El panel muestra Reflejar pose, Reflejar seleccionados, Intercambiar poses y los controles de selección del lado opuesto. La imagen muestra los controles; no demuestra la ejecución de un reflejo, intercambio o cambio de selección. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): f95ca355befd.](images/es/12.11.1-pose-mirror.png)

<a id="action-offsets-and-motion-trails"></a>

### Desplazamientos de acciones y trayectorias de movimiento

**Animación completa** incluye desplazamientos de la acción activa y una máscara de rango opcional. Estos desplazamientos pueden afectar a más claves que las seleccionadas.

Antes de activar una edición de toda la acción:

1. Configure la máscara.

2. Configure el rango.

Para usar trayectorias de movimiento:

1. Seleccione los objetos o huesos de pose de destino para los ajustes de trayectorias.

2. Abra **Animación completa > Superposición de trayectorias**.

3. Seleccione el modo de visualización.

4. Seleccione el alcance del muestreo.

5. Ajuste el incremento de muestreo.

6. Haga clic en **Activar superposición** o use el ojo **Trayectorias** de Línea de tiempo.

7. Después de los cambios, actualice las trayectorias cuando sea necesario.

8. Ejecute el diagnóstico de arcos para identificar movimientos que deban examinarse.

9. Examine el movimiento señalado.

Las opciones de trayectorias incluyen marcas de fotogramas/claves, números de fotograma, velocidad, tangente, imágenes fantasma y colores. Los rangos alrededor del fotograma actual y los personalizados limitan el muestreo. **Máximo de muestras** limita la cantidad de muestras. El diagnóstico de arcos identifica movimientos que necesitan revisión. No certifica la calidad de la animación ni resuelve automáticamente un rig.

![Máscara de desplazamiento de acción con Usar máscara activado. Sus límites son 1 y 250, con entrada y salida de mezcla de 5. Estos límites de máscara son distintos del rango real de la escena, de 1 a 24. La captura muestra los ajustes y no la ejecución de un desplazamiento. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): c549058abcab.](images/es/12.11.1-action-offset.png)

![Ajustes de Superposición de trayectorias: visualización, alcance, paleta, muestreo, opciones visuales, acciones rápidas y diagnóstico. La superposición está desactivada en el momento de la captura. No se demuestra una operación de trayectorias ni una superposición activa. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): e06d79c8a9d8.](images/es/12.11.1-motion-trails.png)

<a id="locators-proxies-and-bake-sessions"></a>

### Localizadores, proxies y sesiones de horneado

1. Abra **Esqueleto > Proxy y horneado**.

2. Seleccione el objeto deseado.

3. Seleccione un localizador o un proxy Traslación, Orientación, Espacio global o Espacio del padre.

4. Ajuste el rango de horneado para el comando de horneado seleccionado.

5. Ajuste el incremento de horneado.

6. Seleccione los canales de horneado.

7. Ejecute el comando de horneado.

8. Examine el movimiento horneado.

9. Use la limpieza de sesión solo después de comprobar el resultado del horneado.

Los controles de localizadores crean localizadores en los destinos, los promedios de selección o el cursor. También establecen relaciones de parentesco y restricciones, hacen coincidir y hornean entre localizadores y destinos. Antes de usar controles emparejados, lea el sentido de sus flechas.

**Horneado inteligente** combina el horneado de transformaciones con la reducción de claves. **Reducir claves** simplifica claves existentes según su tolerancia. Los rangos disponibles son escena, acción, personalizado, claves seleccionadas y previsualización. Estos comandos de horneado generales difieren del flujo **Hornear en una acción nueva** de NLA que conserva la salida.

**Proxy y horneado en un clic** registra el movimiento global en su propia sesión de proxy antes de hornear. **Hornear sesión y eliminar proxies** limpia esa sesión. **Eliminar todas las sesiones de proxy** afecta a un alcance mayor. La validación existente no certifica todos los casos con parentesco, restricciones o rigs de producción. Compare el resultado antes de eliminar los auxiliares.

![Panel de localizadores, proxies, horneado y limpieza sin ninguna sesión activa. Se ve el panel completo, desde el aviso superior hasta Recuperar, sin una ayuda emergente que tape los controles. Se conservan los estados desactivados reales. No se crearon proxies ni se ejecutaron operaciones de coincidencia, horneado, limpieza o recuperación. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 15a3481e071a.](images/es/12.11.1-proxy-bake.png)

La figura muestra los controles de configuración antes de crear una sesión. Una sesión activa habilita la limpieza.

<a id="animation-layers"></a>

### Capas de animación

1. Abra **Animación completa > Capas de animación**.

2. Active el sistema de capas.

3. Haga clic en **Crear capa base** para la animación actual.

4. Añada una capa de trabajo.

5. Seleccione la capa de trabajo.

6. Seleccione su modo de mezcla.

7. Ajuste su peso.

8. Configure sus asignaciones de huesos.

9. Antes de insertar claves, seleccione la capa de trabajo deseada.

10. Previsualice con los controles Solo, Silenciar y Bloquear de la capa.

Una lista de asignaciones vacía incluye todos los huesos. En Modo Pose, el panel visible ofrece **Asignar**, **Eliminar** y **Seleccionar** para las asignaciones de huesos. Cada fila de capa contiene peso, Solo, Silenciar, Bloquear y Inserción automática de claves.

Este panel registrado no muestra **Editar solo activo**, **Asignar al insertar clave** ni todos los controles avanzados de capas. La búsqueda nativa de operadores ofrece acciones registradas como **Asignar por patrón**, **Combinar con inferior** y **Fusionar todas las capas**. Examine la pila antes de combinar o aplanar. Estas capas son independientes de los clips de corrección de transformación NLA.

![Pila de Capas de animación inicializada con Base Layer y la capa seleccionada Polish; ambos pesos son 1.00. Polish usa mezcla aditiva (ADDITIVE). Los nombres de las capas se conservan como datos de la escena. La prueba nativa vinculada acredita únicamente la inicialización y la creación de Polish; no se demuestra un horneado de capas. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 05be41a7cf84.](images/es/12.11.1-animation-layers.png)

<a id="lipsync"></a>

### Sincronización labial

1. Abra **Cara > Sincronización labial**.

2. Active la sincronización labial.

3. Añada una capa de sincronización labial con **+**.

4. Seleccione la capa.

5. En **Audio**, vincule un archivo **WAV**.

6. Seleccione **Claves de forma**, **Huesos** o **Ambos** como destino.

7. Seleccione la malla o el esqueleto de destino.

8. Configure **Conexión de claves de forma** o **Conexiones de huesos del esqueleto** para la biblioteca de visemas seleccionada.

9. Verifique los nombres de destino de las entradas de conexión.

10. Compruebe la anticipación, el desplazamiento de fotogramas y el motor de análisis.

11. Haga clic en **Hornear**.

12. Examine el movimiento de la boca.

Antes de **Volver a hornear**, use **Bloquear claves seleccionadas** para conservar el trabajo manual seleccionado.

**Previsualización en vivo / Horneado** muestra el estado de la capa. La salida de claves de forma requiere una malla con claves de forma conectadas. La salida de huesos requiere una capa de animación, un esqueleto y conexiones válidos. **Rellenar automáticamente** proporciona entradas de conexión. **Capturas de visemas > Capturar** guarda una pose personalizada.

Use el control de estado para elegir el flujo de previsualización o de horneado necesario.

El análisis de amplitud no requiere un ejecutable externo de fonemas. El análisis opcional Rhubarb requiere configurar **Ruta de Rhubarb**. Antes de confiar en la salida, lea los informes sobre cambio a un motor alternativo y capas ausentes. Si existe una tira de altavoz, su superposición muestra el audio en Planilla de tiempos/Línea de tiempo.

**Borrar** de la barra lateral elimina la salida automática y conserva el trabajo manual marcado. **Volver a hornear** también conserva las sustituciones manuales. **Resaltar claves manuales** muestra las ediciones protegidas. Cambiar el audio marca la capa como desactualizada. Antes de volver a hornear, resuelva los problemas de WAV, destino y capa indicados.

![Sincronización labial después de la configuración inicial, con manual-example.wav y el modo SHAPE_KEYS para Apertura básica de boca. La configuración creó la tira AA_P12_face_lipsync_1, de tipo SOUND, en el canal 1. Hay 0 señales; la malla y las conexiones de claves de forma y mandíbula siguen sin asignar. Se conservan los nombres de datos y los puntos suspensivos nativos de la ruta de audio. No se realizó análisis de audio, evaluación de visemas ni horneado de movimiento de boca. Candidata local Anim Assist 12.11.2 en Bforartists, distribución oficial 5.2.3; versión informada por la API: 5.3.0 Alpha. Captura del 2026-11-20 (UTC). SHA-256 de la imagen (prefijo): 32bac204ea2a.](images/es/12.11.2-lipsync-setup.png)

<a id="troubleshooting-and-verification-limits"></a>

## Solución de problemas y límites de verificación

Si una operación de claves no hace nada:

1. Compruebe el editor activo.

2. Compruebe las claves editables seleccionadas y los canales visibles.

3. Compruebe los bloqueos, el propietario y la acción.

4. Examine los datos de la acción y los filtros del editor.

La visibilidad de la barra no demuestra por sí sola que una operación haya insertado claves. Insertar clave nativo sigue siendo el flujo normal para insertar claves en mallas/objetos.

Para informar de un problema, incluya la versión del complemento, la compilación de Bforartists, el comando exacto y una escena pequeña que permita reproducirlo.

Si una acción NLA no está disponible:

1. Compruebe los bloqueos de pistas y las exclusiones por Silenciar/Solo.

2. Compruebe si falta una acción, si la evaluación NLA está desactivada o si el modo de retoque está activo.

3. Antes de organizar clips, haga clic en **Terminar edición**.

4. Para crear correcciones, lea la explicación sobre rigs/canales no compatibles.

Después de cambiar tiempos u hornear:

1. Examine el movimiento.

2. Si es necesario, use Deshacer nativo.

3. Guarde la escena.

4. Vuelva a abrirla antes de confiar en el resultado.

Si los ajustes de controladores no están disponibles, seleccione un canal de controlador desbloqueado para activarlo de forma nativa. Un controlador bloqueado puede seguir visible para examinarlo y desbloquearlo. Si varios controladores seleccionados no tienen un destino activo claro, las herramientas no eligen uno. Las acciones de edición de puntos requieren puntos de respuesta seleccionados.

Las [notas de la versión 12.11.1](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.11.1/RELEASE-NOTES.md) describen la corrección del despacho de Deshacer en Línea de tiempo. La [validación de 12.11.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.11.0/qualification.md) registra pruebas específicas de Controladores y observaciones con el cursor nativo en Bforartists 5.2.0. Cubren el alcance de canales, la navegación por ajustes nativos y Deshacer/Rehacer de modificadores. Los registros también cubren el registro de distribuciones y 11 escenarios de regresión de editores de animación. Estos resultados proceden de pruebas anteriores. La actualización del manual no repitió esas pruebas.

La [validación de 12.10.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.10.0/qualification.md) cubre los conjuntos de herramientas por etapa. La [validación de 12.9.1](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.9.1/qualification.md) cubre las correcciones de pestañas de etapas. La [validación de 12.8.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.8.0/qualification.md) registra 16 grupos de interacción nativa, Deshacer/Rehacer y la recarga del espacio de trabajo. También registra 98 registros de paneles y cinco regresiones de distribución de Línea de tiempo. Su evidencia incluye inserción de claves en mallas y capturas de la barra lateral a 220, 280 y 360 px.

Estas pruebas no certifican todos los operadores, modificadores, rigs de producción ni compilaciones del programa. La evidencia antigua de deslizadores y sincronización labial sigue siendo histórica. La revisión documental del 20 de noviembre comprueba el código fuente actual, los enlaces y la presentación del PDF. No proporciona certificación formal del diccionario STE.

**Configurar sincronización labial** de la versión candidata 12.11.2 terminó en Bforartists 5.2.3 oficial, con base Blender 5.3 Alpha. Creó una tira de sonido. La nueva figura muestra la capa resultante antes de conectar los destinos y hornear. No demuestra movimiento de boca horneado.

Si la configuración informa **compiled without Audaspace support**, use una compilación de Bforartists con soporte de audio. La configuración puede terminar sin crear su tira de sonido. La compilación personalizada suministrada, con base Blender 5.4 Alpha, produjo ese resultado.

Use las figuras **Planilla de tiempos**, **Editor de curvas** y **Controlador seleccionado** para localizar los resúmenes de alcance y selección.

<a id="screenshot-sources-and-limits"></a>

## Origen de las capturas y límites

El manual fuente en inglés conserva capturas históricas de Línea de tiempo y de los ajustes de la barra de herramientas, capturas del controlador seleccionado procedentes de la validación de 12.11.0, vistas generales de editores de la validación de 12.8.0 y capturas de tiras separadas de 12.5.0. Esta edición localizada sustituye esas figuras por nuevas capturas nativas de la versión candidata local y no publicada 12.11.2. Cada pie de figura indica qué demuestra la captura y cuáles son los límites de la evidencia; una nueva captura no repite ni amplía las pruebas de las versiones anteriores.

Las capturas nativas de 12.11.1 suministradas por el usuario muestran alcances vacíos. Documentan la distribución visible. No demuestran una edición completada:

- [Barra lateral de Controladores sin controlador seleccionado](../images/12.11.1-native-drivers-empty.png).
- [Barra lateral de gráficas de acciones sin curvas editables dentro del alcance](../images/12.11.1-native-action-graph.png).
