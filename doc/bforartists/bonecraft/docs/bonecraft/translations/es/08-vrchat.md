# Herramientas de VRChat {#vrchat-tools}

[← Índice](index.md)

## Herramientas de VRChat {#vrchat-tools-1}

Las herramientas VRChat están en **Avatar Tools** de **CATS**, en la barra lateral derecha. Pulsa **N** para mostrarla. Avatar Tools abarca huesos humanoides, física del cabello y Viseme Library / Lip Sync. La exportación VRChat está en CATS → Import / Export → Unity / VRChat. La sección separada **VRChat Tools**, debajo, agrupa Check Performance, Attach Clothing, Facial y VRChat Naming Extras. Con Preferences → Tabs → Scene Properties → Show activado también aparece en **Scene** del editor **Properties**. Este interruptor no oculta la pestaña CATS de la vista.

---

### Set Up Humanoid Bones {#set-up-humanoid-bones}

Mapea los huesos del esqueleto a las ranuras humanoides VRChat y comprueba la asignación.

Consulta [Guía 5: mapear tu avatar al sistema corporal de VRChat](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system).

Descripción de imagen del original en inglés (imagen omitida): ranuras humanoides obligatorias antes de Auto-Map All. Revisa cada ranura después del mapeo y rellena los huecos restantes.

*Panel emergente nativo, BoneCraft 9.2.18. Ranuras humanoides obligatorias antes de Auto-Map All. Revisa cada ranura después del mapeo y rellena los huecos restantes.*

---

### Add Hair Physics {#add-hair-physics}

Configura cadenas PhysBone en cabello, orejas, colas y accesorios, con colisionadores.

Consulta [Guía 6: añadir física del cabello](02-guides-a.md#guide-6-add-hair-physics).

Descripción de imagen del original en inglés (imagen omitida): cadenas Hair Physics, acciones de generación, preajustes y controles de colisionadores. Revisa las cadenas detectadas antes de aplicar física.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Cadenas Hair Physics, acciones de generación, preajustes y controles de colisionadores. Revisa las cadenas detectadas antes de aplicar física.*

---

### Attach Clothing {#attach-clothing}

**Dónde encontrarla:** pestaña CATS → VRChat Tools → Clothing

Combina ropa con el esqueleto del avatar y transfiere sus pesos.

Consulta [Guía 7: adjuntar ropa que se mueva con tu cuerpo](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body).

Descripción de imagen del original en inglés (imagen omitida): controles de ropa y orden de selección Pre-Merge. Antes de combinar, empareja huesos y comprueba conflictos de nombres.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Controles de ropa y orden de selección Pre-Merge. Antes de combinar, empareja huesos y comprueba conflictos de nombres.*

---

### VRChat Naming Extras {#vrchat-naming-extras}

**Dónde encontrarla:** pestaña CATS → VRChat Tools → Naming

**Qué hace:** detecta el estilo de nombres del esqueleto y renombra huesos por lotes.

Consulta [Guía 4: corregir los nombres de huesos de tu avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names).

**Herramientas por lotes:** **Find and Replace**, **Add Prefix**, **Remove Prefix**, **Add Suffix**, **Remove Suffix** y **Regex Replace**

Descripción de imagen del original en inglés (imagen omitida): Naming detecta Unity Humanoid con confianza 16/24 en este ejemplo. Revisa los nombres antes de las acciones por lotes.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Naming detecta Unity Humanoid con confianza 16/24 en este ejemplo. Revisa los nombres antes de las acciones por lotes.*

---

### VRChat Viseme Mapping {#vrchat-viseme-mapping}

**Dónde encontrarla:** CATS → VRChat Tools → Facial. Face Tracking está en la misma sección.

**Qué hace:** asigna las claves de forma de la malla a los 15 visemas de sincronización labial VRChat.

Consulta [Guía 8: configurar la sincronización labial](03-guides-b.md#guide-8-set-up-lip-sync). Para crear visemas que aún no tenga el avatar, consulta [Herramientas CATS: Visemes](09-cats.md#visemes).

**Las 15 ranuras de visemas VRChat:** `sil`, `PP`, `FF`, `TH`, `DD`, `kk`, `CH`, `SS`, `nn`, `RR`, `aa`, `E`, `I`, `O`, `U`

Descripción de imagen del original en inglés (imagen omitida): ranuras de visemas y Face Tracking antes del mapeo. El ejemplo tiene visemas sin asignar y 0 de 55 expresiones mapeadas.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Ranuras de visemas y Face Tracking antes del mapeo. El ejemplo tiene visemas sin asignar y 0 de 55 expresiones mapeadas.*

---

### Check Performance {#check-performance}

**Dónde encontrarla:** pestaña CATS → VRChat Tools → Performance

**Qué hace:** mide la clasificación de rendimiento VRChat del avatar y ofrece correcciones.

Consulta [Guía 9: mejorar el rendimiento de tu avatar](03-guides-b.md#guide-9-improve-your-avatars-performance).

**Niveles de rendimiento (de mejor a peor):** Excellent → Good → Medium → Poor → Very Poor

**Herramientas:**

- **Calculate Performance Rank** — clasificación actual y desglose por polígonos, mallas deformables, ranuras de material, huesos, PhysBones y contactos
- El optimizador ofrece **Remove Zero-Weight Bones**, **Merge Same-Material Meshes**, **Remove Unused Shape Keys** y **Remove Unused Vertex Groups**. **What-If Mode** muestra qué cambiarían
- VRChat Decimation — reduce polígonos mediante una proporción, protegiendo claves de forma

Para VRChat Decimation:

1. Selecciona la malla del avatar.
2. Selecciona **Preview**.
3. Selecciona **Apply**.

Descripción de imagen del original en inglés (imagen omitida): métricas de Performance y controles What-If. Selecciona una malla de avatar para usar la limpieza de mallas.

*Panel emergente nativo, BoneCraft 9.2.18. Métricas de Performance y controles What-If. Selecciona una malla de avatar para usar la limpieza de mallas.*

Descripción de imagen del original en inglés (imagen omitida): ajustes Decimation antes de Preview o Apply. El ejemplo usa Ratio 0.50 y Shape Key Safety. What-If Mode está activado para las acciones de limpieza inferiores.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Ajustes Decimation antes de Preview o Apply. El ejemplo usa Ratio 0.50 y Shape Key Safety. What-If Mode está activado para las acciones de limpieza inferiores.*

---

### Export to VRChat {#export-to-vrchat}

**Qué hace:** exporta el avatar terminado como FBX para VRChat SDK en Unity. Conserva las claves de forma (blend shapes) salvo que **Remove Shape Keys** esté activado.

**Ajustes:**

- **Folder** — carpeta de destino
- **Avatar** — nombre del archivo exportado
- **Sidecar** — también escribe un archivo de ajustes `.bfvrc` para el importador Unity de BoneCraft
- **Merge Meshes** — une las mallas de la copia de exportación en una
- **Separate Clothing** — mantiene la ropa como mallas separadas
- **Remove Shape Keys** — aplica las claves de forma a Basis de la copia de exportación
- **Embed Textures** — empaqueta las texturas en el FBX para que Unity las encuentre
- **Helper Meshes** — incluye mallas ocultas o auxiliares. Déjalo desactivado para avatares normales
- **Bone Names** — **Keep Original Names**, **Unity-Preset** o **Unreal-Preset**, aplicados a copias de exportación

**Ubicación:** CATS → Import / Export → Game Engine Export → Unity / VRChat.

Antes de exportar:

1. Si faltan ranuras obligatorias, ejecuta **Auto-Map Humanoid** aquí.
2. Revisa las ranuras.

Para comprobar el rendimiento antes de exportar, selecciona **Check Performance Rank**. Antes de un preajuste **Bone Names**, corrige conflictos de mapeo o nombres. La sección **Export bone naming** siguiente explica esos conflictos. Convierte los objetos vinculados en locales antes de exportar. Para escribir el FBX, selecciona **Export to VRChat (Unity)**.

**Normalize Names** renombra el rig de trabajo. Los preajustes **Bone Names** renombran copias de exportación.

El exportador Unity/VRChat escribe la pose de reposo sin animación. Los botones principales Unity y Unreal aceptan modos Objeto, Pose y Edición. Usan temporalmente Modo Objeto y restauran después modo y selección anteriores.

Descripción de imagen del original en inglés (imagen omitida): ajustes Unity / VRChat antes de configurar carpeta y mapeo humanoide. El ejemplo muestra 0 de 15 ranuras obligatorias mapeadas.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Ajustes Unity / VRChat antes de configurar carpeta y mapeo humanoide. El ejemplo muestra 0 de 15 ranuras obligatorias mapeadas.*

---

### Limpieza {#cleanup}

La limpieza de mallas previa a la exportación está en CATS: **Fix Model**, **Join Meshes** y **Apply All Transforms**. Consulta [Herramientas de CATS](09-cats.md).

---

## Puente VRM {#vrm-bridge}

Las herramientas VRM están en **CATS** → **Import / Export** → **VRM / VRoid**. Necesitan el complemento VRM. Un puente inactivo ofrece **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** y **Show Manual Instructions**.

Para un paquete sin conexión, usa las preferencias nativas. Un ZIP de complemento clásico usa **Add-ons → Install from Disk…**. Una extensión moderna usa el menú nativo de instalación Extensions.

1. Instala el paquete mediante el menú nativo correspondiente.
2. Activa la dependencia.
3. Confirma que el puente indica **Active**.

La tarjeta inactiva del centro no tiene botón de instalación ZIP.

Descripción de imagen del original en inglés (imagen omitida): el ejemplo no tiene activado ninguno de los dos puentes de formatos. Instala el requerido para que aparezcan sus controles de importación y exportación.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. El ejemplo no tiene activado ninguno de los dos puentes de formatos. Instala el requerido para que aparezcan sus controles de importación y exportación.*

---

### Importación VRM y VRoid {#vrm-and-vroid-import}

**Qué hace:** importa avatares `.vrm` (VRoid Studio, Virtual Cast y otros) con materiales, esqueleto y claves de forma.

- **Import VRM…** — archivo `.vrm`
- **Import VRoid (.vroid / .zip)…** — descarga VRoid Hub (`.zip`). Un proyecto VRoid Studio (`.vroid`) muestra una tarjeta que explica cómo exportarlo primero a VRM.

---

### Exportación VRM {#vrm-export}

**Qué hace:** exporta el personaje con rig a VRM o al formato de una aplicación de destino.

**Ajustes:**

- **Folder** y **File** — destino y nombre de archivo. La extensión depende del destino
- **Target** — VRM 1.0, VRM 0.x, VRChat FBX, VSeeFace, Warudo o Resonite
- **Scope** — esqueleto activo o todos los esqueletos con datos VRM
- Skip lint — exporta sin comprobar el destino. Úsalo solo si entiendes el riesgo indicado

Haz clic en **Export…**.

---

### VRM Lint {#vrm-lint}

**Qué hace:** comprueba el esqueleto respecto al destino seleccionado antes de exportar. Abarca mapeo humanoide, metadatos VRM, visemas y requisitos de la aplicación de destino.

**Lint Now** comprueba sin cambiar nada. Salvo que omitas lint, los errores bloquean la exportación. Los avisos identifican contenido que la aplicación puede importar con rendimiento reducido.

Si lint informa de huesos humanoides ausentes que sí existen, haz clic en **Fix Humanoid Map**. BoneCraft vuelve a detectar las ranuras y guarda el mapeo. No renombra huesos.

**También aquí:** **Convert SpringBones → PhysBones** (física del cabello VRoid a VRChat) y **Map VRoid Visemes**.

---

## Puente MMD {#mmd-bridge}

Las herramientas MMD están en **CATS → Import / Export → MMD / PMX**. Necesitan **mmd_tools** instalado y activado. BoneCraft reconoce paquetes clásicos y extensiones modernas Blender.

Un puente inactivo ofrece **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** y **Show Manual Instructions**. El contenido independiente del puente también ofrece **Install from .zip on Disk...** cuando se muestra. Consulta la [guía 3](02-guides-a.md#step-1--install-mmd_tools) para instalación y comprobaciones de repositorio local.

---

### Importación MMD {#mmd-import}

- **Import PMX / PMD...** — modelos MMD
- **Import VMD Motion...** — animaciones MMD
- **Import VPD Pose...** — poses MMD

Confirma que la importación termina correctamente. Una importación PMX cancelada o un error de instalación dejan la tarea incompleta. Los modelos importados pueden necesitar revisar materiales y mapeo de huesos antes de convertir.

---

### Exportación MMD {#mmd-export}

**Ajustes:** **Folder** establece el destino. Cada formato tiene ajustes de nombre y alcance:

- **PMX File** y **PMX Scope**.
- **VMD File** y **VMD Scope**.
- **VPD File** y **VPD Scope**.

Cada alcance selecciona el modelo activo o todos los modelos MMD de la escena.

**Botones:** **Export PMX...**, **Export VMD Motion...** y **Export VPD Pose...**

**También aquí:** **Convert Bone Names -> Unity** y **Convert Physics -> PhysBones**.

---

## Game Engine Export {#game-engine-export}

**Game Engine Export** es el área integrada en **CATS → Import / Export**. Contiene **Unity / VRChat** y **Unreal Engine 5**. El panel hijo separado **Game Export** ofrece exportación por perfiles validados.

### Unreal Engine 5 {#unreal-engine-5}

Con **Bake Anim** activado, el exportador hornea la acción activa. No necesita una tira NLA separada. No exporta todas las acciones ajenas.

Antes de un preajuste **Bone Names**, corrige conflictos de mapeo o nombres. La sección **Export bone naming** siguiente explica esos conflictos. Convierte los objetos vinculados en locales antes de exportar.

1. Selecciona el esqueleto y sus mallas.
2. Abre **CATS → Import / Export → Game Engine Export → Unreal Engine 5**.
3. Configura **Folder**.
4. Configura **File** con el nombre FBX.
5. Revisa **Bone Names** y su vista previa.
6. Si necesitas la animación activa, activa **Bake Anim**.
7. Haz clic en **Export to Unreal (FBX)**.

**Selected Only** empieza activado. Incluye el esqueleto con sus mallas. **Unit Scale** empieza activado, **Leaf Bones** desactivado y **Embed Textures** activado. El panel abrevia **Bake Animation** como **Bake Anim**.

**Import from Unreal (FBX)** abre el explorador de archivos de importación.

Descripción de imagen del original en inglés (imagen omitida): ajustes Unreal Engine 5 antes de elegir carpeta de salida. Revisa Bone Names, Selected Only y Bake Anim antes de exportar.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Ajustes Unreal Engine 5 antes de elegir carpeta de salida. Revisa Bone Names, Selected Only y Bake Anim antes de exportar.*

### Nombres de huesos al exportar {#export-bone-naming}

Ambas secciones de motores ofrecen las mismas opciones **Bone Names**:

| Opción | Resultado exportado |
| --- | --- |
| Keep Original Names | Conserva los nombres existentes. Es el valor predeterminado. |
| Unity-Preset | Usa nombres Unity Humanoid reconocidos, incluidos `Hips`, `LeftUpperArm` y `LeftIndexProximal`. |
| Unreal-Preset | Usa nombres humanoides Unreal reconocidos, incluidos `pelvis`, `spine_01`, `upperarm_l`, `index_01_l` y `ball_l`. |

Selecciona un esqueleto para ver la vista previa. Muestra cantidades **Recognized / renamed** y hasta tres cambios propuestos. Los huesos no reconocidos conservan sus nombres.

Los mapeos humanoides guardados tienen prioridad sobre la detección de nombres. También participan los huesos opcionales reconocidos de pecho, cuello, hombros, ojos, mandíbula, dedos de manos y pies. Un `Root` reconocido separado se convierte en `root` con **Unreal-Preset**.

Los nombres de destino en conflicto, huesos ambiguos y ranuras humanoides reutilizadas bloquean el cambio de nombres. Corrige el conflicto antes de exportar. BoneCraft no añade sufijos `.001` para resolverlo.

Convierte los objetos vinculados en locales antes de exportar. Los preajustes renombran copias temporales de exportación. El rig de trabajo conserva los nombres. Los grupos de vértices, canales de animación y referencias de huesos del archivo auxiliar Unity exportados siguen los nombres seleccionados. La limpieza elimina datos temporales tanto en caso de éxito como de fallo.

Estos preajustes solo cambian nombres. Conservan jerarquía, orientación de huesos y pose de reposo. No añaden articulaciones ausentes ni construyen un esqueleto Manny/Quinn completo. Aún pueden hacer falta el mapeo Unity Avatar o la readaptación de animación en Unreal.

### Exportación por perfil validado {#validated-profile-export}

**Qué hace:** exporta con un perfil validado: humanoide o universal Unreal, humanoide Unity, humanoide Godot, FBX genérico o GLB. La lista de resultados muestra las correcciones disponibles. Requieren una acción explícita tuya.

Usa Modo Objeto para este flujo. La garantía de restaurar Objeto/Pose/Edición se aplica a los dos botones principales de exportación a motores.

Antes de un preajuste **Bone Names**, corrige conflictos de mapeo o nombres. La sección **Export bone naming** anterior explica esos conflictos. Convierte objetos vinculados en locales antes de exportar.

**Ajustes del explorador de archivos:** **Profile**, **Animation**, **Bone Names**, **Root Motion**, **Interpolation** y **T-Pose**. **Bone Names** sigue inicialmente la selección de Unreal. El perfil de formato de exportación sigue siendo una opción separada.

Para un preajuste de nombres, selecciona **Active Action** o **No Animation**. **All Actions** necesita **Keep Original Names**, porque puede incluir acciones de otros rigs.

**T-Pose** sigue el perfil de forma predeterminada. Los perfiles humanoides Unity y VRChat usan pose en T. Exportar pose en T incluye la pose de reposo sin animación. Para la pose de reposo modelada, selecciona **Export as modelled**.

1. Selecciona el esqueleto y sus mallas.
2. Abre **CATS → Import / Export → Game Export**.
3. Haz clic en **Check for Export**.
4. Revisa los resultados y las correcciones explícitas.
5. Haz clic en **Export (Profile)**.
6. Selecciona ajustes en el explorador.
7. Selecciona el archivo de salida.
8. Confirma la exportación.

Descripción de imagen del original en inglés (imagen omitida): opciones de exportación por perfil antes de confirmar. El ejemplo usa Generic FBX, Active Action y Keep Original Names.

*Versión preliminar local, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Opciones de exportación por perfil antes de confirmar. El ejemplo usa Generic FBX, Active Action y Keep Original Names.*

**Botones:**

- **Check for Export** — comprueba el rig respecto al perfil y enumera resultados
- **Apply Transforms (Fix)** — una corrección explícita que puede ofrecer la comprobación
- **Export (Profile)** — exporta con el perfil

**Dónde encontrarla:** **CATS** → **Import / Export** → **Game Export**

Consulta la [guía independiente de nombres de exportación](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/export-bone-naming.md) para más detalles y comprobaciones históricas del host.

Descripción de imagen del original en inglés (imagen omitida): Check for Export, correcciones explícitas y Export (Profile). El ejemplo aún no tiene resultados de comprobación por perfil.

*Panel emergente nativo, BoneCraft 9.2.18. Check for Export, correcciones explícitas y Export (Profile). El ejemplo aún no tiene resultados de comprobación por perfil.*

---

## Task Board {#task-board}

**Qué hace:** resume el rig actual con una puntuación de salud, tareas rápidas y tareas agrupadas por categoría. Incluye huesos humanoides ausentes, nombres sin resolver, visemas ausentes y avisos del validador. **Quick Wins** muestra hasta tres tareas recomendadas. **Remaining Tasks** contiene solo las demás. **Open Health Check** ejecuta la validación y abre resultados. **Refresh Task Board** vuelve a comprobar.

**Dónde encontrarla:** **BoneCraft** → **Overview** → **Task Board**

Descripción de imagen del original en inglés (imagen omitida): Task Board enumera los problemas detectados y las acciones rápidas del rig activo de ejemplo.

*Panel emergente nativo, BoneCraft 9.2.18. Task Board enumera los problemas detectados y las acciones rápidas del rig activo de ejemplo.*

---

### Bone Inspector {#bone-inspector}

**Qué hace:** muestra las dimensiones de reposo, padre, restricciones, datos personalizados, controladores y pesos de piel del hueso de pose activo.

La información es de solo lectura. Abre el panel con un hueso activo en Modo Pose. Para copiar el nombre, selecciona **Copy Name** en la cabecera.

**Dónde encontrarla:** **BoneCraft** → **Review** → **Bone Inspector**

Descripción de imagen del original en inglés (imagen omitida): Bone Inspector muestra datos del hueso en reposo, restricciones, datos personalizados, controladores y pesos de piel. La cabecera incluye Copy Name.

*Panel emergente nativo de prueba, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Bone Inspector muestra datos del hueso en reposo, restricciones, datos personalizados, controladores y pesos de piel. La cabecera incluye Copy Name.*

Siguiente: [Herramientas de CATS](09-cats.md)
