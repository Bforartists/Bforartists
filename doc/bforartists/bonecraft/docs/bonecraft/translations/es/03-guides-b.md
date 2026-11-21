# Guías 8–13 {#guides-813}

[← Índice](index.md)

## Guía 8: configurar la sincronización labial {#guide-8-set-up-lip-sync}

> **Tiempo:** unos 10–20 minutos
> **Resultado:** la boca de tu avatar se mueve correctamente al hablar en VRChat

**Antes de empezar, comprueba esto:**

- [ ] La malla de la cabeza de tu avatar tiene claves de forma de boca (también llamadas blend shapes o morph targets: las distintas posiciones de boca al hablar)
- [ ] Conoces aproximadamente sus nombres (consulta Shape Keys en las propiedades Object Data de la malla)

> Un visema es la forma de boca de un sonido. `aa` es el sonido «ahh», `O` es «ohh», etc. VRChat usa 15 visemas para controlar la sincronización labial del avatar.
>
> Una clave de forma (blend shape) es una versión guardada de la malla en otra posición. La clave de boca abierta es tu malla con la boca abierta.

---

### Paso 1 — Abrir VRChat Viseme Mapping {#step-1--open-vrchat-viseme-mapping}

Consulta los [controles de Viseme Mapping y Face Tracking](08-vrchat.md#vrchat-viseme-mapping).

Abre **CATS → VRChat Tools → Facial → VRChat Viseme Mapping**.

---

### Paso 2 — Mapear visemas automáticamente {#step-2--auto-map-visemes}

Haz clic en **Auto-Map All Visemes**. BoneCraft lee las claves de forma de tu malla y las relaciona por nombre con las 15 ranuras de visemas de VRChat.

**Deberías ver:** la lista de visemas, con una clave de forma asignada en la mayoría de las ranuras.

---

### Paso 3 — Rellenar las ranuras vacías {#step-3--fill-in-missing-slots}

Una ranura vacía muestra «(unmapped)».

1. Selecciona su botón para abrir la lista de búsqueda de claves de forma de la malla.

2. Escribe para filtrar la lista.

3. Selecciona la clave de forma más parecida.

Para vaciar una ranura, selecciona «(unmapped)». Coincidencias habituales:

| Visema VRChat | Sonido | Clave de forma que buscar |
|---|---|---|
| `aa` | «ahh» | mouth_open, A, aa |
| `O` | «ohh» | mouth_o, OH, oh |
| `CH` | «ch» / «sh» | mouth_ch, CH |
| `PP` | labios juntos (P, B, M) | mouth_m, MM, lips_together |
| `SS` | «sss» / «zzz» | mouth_s, SS |

**Faltan claves de forma de visemas:** CATS → **Visemes** crea las 15 claves a partir de tres formas base: A, O y CH. Si la malla no tiene formas de boca, crea primero esas tres. Consulta la [guía 13, fase 2](#phase-2--viseme-generation).

---

### Paso 4 — Comprobar una forma de boca {#step-4--check-a-mouth-shape}

1. En **Properties → Object Data → Shape Keys**, configura el valor de la clave asignada como 1.0.

2. Examina la forma de la boca.

3. Restablece el valor a 0.

---

### Paso 5 — Seguimiento facial (opcional) {#step-5--face-tracking-optional}

Bajo la lista de visemas, **Face Tracking (SteamVR)** prepara formas de expresión para hardware de seguimiento facial. Es opcional; la mayoría de los usuarios no lo necesita.

**Lo que esto permite:** la boca del avatar se mueve al hablar en VRChat. Las expresiones usan las claves de forma que acabas de mapear.

---

## Guía 9: mejorar el rendimiento de tu avatar {#guide-9-improve-your-avatars-performance}

> **Tiempo:** unos 15–25 minutos
> **Resultado:** una clasificación de rendimiento VRChat mejor y cargas más rápidas para otros jugadores

**Antes de empezar, comprueba esto:**

- [ ] Tu avatar está completo (con rig, ropa y sincronización labial configurados)
- [ ] Conoces la clasificación deseada (Good o Excellent para la mayoría)

> La clasificación de rendimiento indica cuántos recursos exige el avatar en VRChat. Otros jugadores pueden ocultar los avatares Very Poor. Los avatares Good y Excellent cargan rápido y siempre se muestran.

---

### Paso 1 — Comprobar la clasificación actual {#step-1--check-the-current-rank}

1. Abre **CATS → VRChat Tools**.

2. En Performance, selecciona **Calculate Performance Rank**.

BoneCraft indica la clasificación global y cuánto le falta a cada métrica para el siguiente nivel. Las métricas incluyen polígonos, mallas deformables, ranuras de material, huesos, PhysBones y contactos.

Consulta los [controles de Performance](08-vrchat.md#check-performance).

---

### Paso 2 — Limpiar {#step-2--clean-up}

VRChat Optimizer, en la misma sección, enumera herramientas de limpieza. **What-If Mode** empieza activado. Cada corrección informa de los cambios propuestos sin aplicarlos.

1. Ejecuta la corrección necesaria en What-If Mode.

2. Revisa el informe.

3. Para aplicar esos cambios, desactiva What-If Mode.

4. Ejecuta de nuevo la corrección.

Correcciones disponibles:

1. **Remove Zero-Weight Bones** — elimina huesos que no mueven ninguna parte de la malla
2. **Merge Same-Material Meshes** — une mallas que comparten material
3. **Remove Unused Shape Keys** — elimina claves de forma vacías cuya deformación coincide con Basis. No comprueba referencias de otras herramientas.
4. **Remove Unused Vertex Groups** — elimina grupos de pesos vacíos

---

### Paso 3 — Reducir polígonos (si hace falta) {#step-3--reduce-the-polygon-count-if-needed}

Consulta los [controles de Performance y Decimation](08-vrchat.md#check-performance).

Si la cantidad de polígonos es excesiva:

1. Selecciona la malla.

2. En VRChat Decimation, configura la proporción objetivo.

3. Selecciona **Preview**.

4. Examina el resultado.

5. Para conservarlo, selecciona **Apply**.

Una proporción de 0.5 reduce los polígonos a la mitad. Una de 0.8 elimina el 20%. La reducción protege las claves de forma.

> Empieza en 0.8. Reduce la proporción gradualmente mientras compruebas el aspecto del avatar. Reducciones pequeñas pueden mejorar el rendimiento con pocos cambios visibles.

---

### Paso 4 — Combinar materiales (opcional) {#step-4--merge-materials-optional}

Si tu avatar usa muchos materiales, combínalos en una hoja de texturas (atlas). En **CATS** → **CATS** → **Material Atlas**:

1. Guarda una copia del archivo.
2. Configura **Target** con las mallas que quieres procesar.
3. Mantén **Preserve Backup Duplicate** activado.
4. Haz clic en **Analyze Materials**.
5. Selecciona un grupo de atlas.
6. Marca al menos dos materiales de ese grupo activado.
7. Marca las imágenes de textura que incluir.
8. Usa **Select All** o **Deselect All** sobre cualquiera de las listas si hace falta.
9. Haz clic en **Bake Checked Sources**.
10. Revisa el resumen previo antes de confirmar el horneado.
11. Examina los materiales horneados, la transparencia y las UV.
12. Haz clic en **Accept — Delete Backup** para conservar el resultado.

Usa **Revert — Restore Originals** si el resultado necesita cambios. Accept elimina la copia de seguridad. Desactivar **Preserve Backup Duplicate** quita la opción Revert.

La selección masiva afecta solo a su lista de fuentes del grupo activo. Las texturas ausentes permanecen sin marcar. La otra lista y los demás grupos no cambian.

**Refresh Analysis** reconstruye las listas de fuentes y sus selecciones. Usa **Bake Checked Sources** después de revisar las selecciones. **Smart Combine Materials** es el acceso automático inicial.

[Herramientas CATS: Material Atlas Combiner](09-cats.md#material-atlas-combiner) explica todos los ajustes.

---

### Paso 5 — Comprobar de nuevo la clasificación {#step-5--check-the-rank-again}

Haz clic otra vez en **Calculate Performance Rank** para ver la mejora.

**Lo que esto permite:** una clasificación mejor hace que más jugadores vean tu avatar. Un avatar Good o Excellent carga rápido, usa menos GPU y se muestra a otros jugadores de forma predeterminada.

---

## Guía 10: guardar y reutilizar poses {#guide-10-save-and-reuse-poses}

> **Tiempo:** unos 5–10 minutos
> **Resultado:** una biblioteca guardada de poses aplicables con un clic

**Antes de empezar, comprueba esto:**

- [ ] Tu avatar tiene un esqueleto terminado
- [ ] Estás en **Pose Mode**

Para entrar en Modo Pose:

1. Selecciona el esqueleto.

2. Pulsa Ctrl+Tab.

También puedes seleccionar **Pose Mode** en el desplegable de modo superior izquierdo de la vista.

---

### Paso 1 — Abrir Pose Library {#step-1--open-the-pose-library}

En **BoneCraft**, en la Tool Shelf izquierda, despliega **Review** → **Pose Library**.

Consulta los [controles de Pose Library](05-rig-tools.md#pose-library).

---

### Paso 2 — Colocar tu avatar en una pose {#step-2--pose-your-avatar}

Mueve los huesos a la pose que quieras guardar. Una pose puede combinar rotaciones de brazos, inclinación de cabeza y otras posiciones de huesos.

---

### Paso 3 — Guardar la pose {#step-3--save-the-pose}

1. Selecciona **Save**.

2. Introduce un nombre de pose, como «Peace Sign» o «Thinking».

**Category** agrupa las poses bajo nombres como «Greetings». **Filter** muestra una categoría cada vez. La pose guardada incluye una miniatura de la vista.

---

### Paso 4 — Aplicar una pose guardada {#step-4--apply-a-saved-pose}

1. Selecciona una pose.

2. Selecciona **Apply**.

- **Blend** — aplica la pose con intensidad parcial para mezclar dos poses
- **Mirror** — aplica la pose reflejada de izquierda a derecha

**Rename** y **Delete** administran la lista.

---

### Paso 5 — Exportar e importar poses {#step-5--export-and-import-poses}

**Export** guarda la biblioteca de poses en un archivo `.bfpose` que puedes guardar con el proyecto o compartir. **Import** carga poses de un archivo `.bfpose`.

**Lo que esto permite:** una biblioteca personal reutilizable entre proyectos, mezclable para claves de animación y compartible con otros usuarios de BoneCraft.

---

## Guía 11: combinar dos rigs {#guide-11-merge-two-rigs-together}

> **Tiempo:** unos 25–40 minutos según la complejidad
> **Resultado:** dos esqueletos combinados en uno, conservando todos los pesos

**Antes de empezar, comprueba esto:**

- [ ] El avatar base y el segundo rig (de ropa o accesorio) están en el mismo archivo
- [ ] Ambos tienen rig y pesos

> Combinar rigs significa absorber un esqueleto en otro para obtener uno combinado. Sirve cuando un rig corporal y otro de cabello o ropa deben convertirse en uno.

---

### Paso 1 — Abrir Bone Merge {#step-1--open-bone-merge}

Abre **BoneCraft → Setup Rigging → Bone Merge**. Sus tres etapas se abren en orden al completarlas.

Consulta los [controles por etapas de Bone Merge](06-rig-builder.md#bone-merge).

---

### Paso 2 — Etapa 1: alcance {#step-2--stage-1-scope}

1. Selecciona el esqueleto **Base**, el esqueleto corporal que se conservará.

2. Selecciona el esqueleto entrante de ropa o cabello.

3. Selecciona **Analyze**.

En la combinación final, el esqueleto entrante se integra en el base y después queda oculto.

Analyze compara los dos esqueletos y enumera:

- ✓ Matched — huesos presentes en ambos y alineados
- \+ Source only — huesos del rig entrante sin coincidencia en el base
- − Target only — huesos del base que el rig entrante no tiene

Cuando hayas leído la lista, haz clic en **Acknowledge Scope — Proceed to Rename**.

---

### Paso 3 — Etapa 2: nombres {#step-3--stage-2-rename}

Para cada hueso exclusivo del origen, elige la alternativa aplicable.

Si tiene un equivalente en el base:

1. Introduce el nombre de ese hueso del base.

2. Selecciona **Apply Rename**.

Si no tiene equivalente, selecciona **Mark as Unique**. Se incorpora al base sin cambiar de nombre.

**Normalize Both Armatures** renombra huesos estándar reconocidos, como columna, brazos y piernas, en ambos rigs. **Auto-Propose Renames** sugiere nombres para otros huesos a partir de sus posiciones. **Apply Batch Pattern** renombra varios huesos con un patrón.

Cuando todos los huesos exclusivos del origen estén resueltos, haz clic en **Verify Rename — Proceed to Merge**.

---

### Paso 4 — Etapa 3: combinación {#step-4--stage-3-merge}

Haz clic primero en **Run Merge Preview**: informa de lo que hará la combinación sin cambiar nada.

Si el informe es correcto, haz clic en **Merge Armatures**. BoneCraft hace copias de seguridad de ambos esqueletos y después los combina.

**Deberías ver:** un esqueleto con todos los huesos de ambos, con todas las mallas vinculadas a él mediante pesos.

**Lo que esto permite:** un rig único más fácil de exportar y editar. Es necesario para cualquier avatar con rigs de ropa o accesorios separados.

---

## Guía 12: resolver problemas de subida {#guide-12-fix-upload-problems}

> **Tiempo:** unos 5–15 minutos según el problema

**Antes de empezar:** busca tu problema en la lista y ve a esa sección.

---

### «La subida falló: huesos no reconocidos» {#upload-failed--bones-not-recognized}

Los huesos tienen nombres que VRChat no entiende. → [Guía 4: corregir los nombres de huesos de tu avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

---

### «El avatar está en pose en T / no se mueve conmigo en VRChat» {#avatar-is-in-t-pose--not-moving-with-me-in-vrchat}

El mapeo humanoide falta o es incorrecto. → [Guía 5: mapear tu avatar al sistema corporal de VRChat](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)

---

### «La malla se deforma de forma extraña / la piel se estira mal» {#mesh-is-deforming-weirdly--skin-stretching-wrong}

Hay que ajustar los pesos de huesos. → Consulta Weight Transfer y Weight Mirror en [Herramientas de rig](05-rig-tools.md), o ejecuta **Smart Automatic Weights** en CATS.

---

### «El cabello atraviesa la cabeza» {#hair-is-clipping-through-the-head}

Faltan colisionadores del cabello o son demasiado pequeños. → [Guía 6: añadir física del cabello](02-guides-a.md#guide-6-add-hair-physics), paso 5.

---

### «El avatar tiene rendimiento Very Poor y otros jugadores lo bloquean» {#avatar-is-very-poor-performance-and-being-blocked-by-other-players}

→ [Guía 9: mejorar el rendimiento de tu avatar](#guide-9-improve-your-avatars-performance)

---

### «La sincronización labial no funciona» {#lip-sync-not-working}

Los visemas no están bien mapeados. → [Guía 8: configurar la sincronización labial](#guide-8-set-up-lip-sync)

---

### «El validador del rig muestra errores» {#rig-validator-shows-errors}

1. Abre **BoneCraft → Review → Rig Validator**.

2. Selecciona **Run Validation**.

3. Sigue la sugerencia del resultado o consulta el [Índice de soluciones rápidas](10-reference.md#quick-fix-index).

Cada resultado identifica el problema y el hueso. **Export Report** guarda los resultados en un archivo.

---

### «La importación VRM no funciona» {#vrm-import-not-working}

Es posible que el complemento VRM no esté instalado. → [Guía 2](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat), paso 1.

---

### «La importación MMD no funciona» {#mmd-import-not-working}

Comprueba si **mmd_tools** está instalado y activado. El puente admite extensiones modernas y paquetes clásicos. Revisa el mensaje de instalación antes de reintentar. Consulta la [guía 3](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat), paso 1.

---

## Guía 13: preparar tu avatar para VRChat con CATS {#guide-13-get-your-avatar-vrchat-ready-with-cats}

> **Tiempo:** unos 20–35 minutos para ejecutar el pipeline completo
> **Resultado:** un avatar limpio y optimizado, con sincronización labial, seguimiento ocular y transformaciones correctas, listo para subir a VRChat

**Antes de empezar, lee esto:**

Las herramientas CATS tienen un pipeline recomendado. Pipeline Status marca las fases terminadas: Fix Model, Material Atlas, Visemes, Eye Tracking, Pose To Shape y Apply Transforms. Operation Ledger registra cada operación CATS.

Las herramientas siguen funcionando si una fase anterior está incompleta. Muestran un aviso como «Run Fix Model first for best results».

Empieza revisando las opciones de limpieza de Fix Model. Guarda un punto de control del archivo antes de cambiar el avatar.

Antes de continuar, lee [El pipeline de CATS](04-cats-pipeline.md).

**Antes de empezar, comprueba esto:**

- [ ] Tu avatar está importado y visible en la Vista 3D
- [ ] La pestaña CATS está abierta en la barra lateral derecha (pulsa N si está oculta)
- [ ] Tu avatar está seleccionado (haz clic en la vista o en el esquema de la escena)

---

### Fase 1 — Fix Model {#phase-1--fix-model}

Fix Model es la fase de limpieza recomendada. Revisa sus opciones para el avatar importado y examina el resultado antes de continuar.

**Qué hace Fix Model** (cada parte puede desactivarse en sus opciones):

- Aplica modificadores
- Elimina vértices duplicados y geometría suelta (triángulos que flotan separados del cuerpo)
- Recalcula normales (las direcciones que determinan qué lado de la malla mira hacia fuera)
- Elimina grupos de vértices vacíos y huesos de peso cero
- Elimina restricciones y cuerpos rígidos que VRChat no puede usar

**Pasos:**

1. Abre **CATS → CATS → Fix Model**.

2. Selecciona la malla del avatar.

3. Selecciona **Fix Model**.

4. Espera a que termine la operación.

5. Comprueba que Pipeline Status marca Fix Model con ✓.

Las mallas grandes pueden tardar unos segundos.

**Deberías ver:** tu avatar igual o algo más limpio. Pipeline Status marca Fix Model y Operation Ledger enumera la ejecución.

**Si el modelo desaparece o parece del revés después de Fix Model:**

El síntoma por sí solo no identifica la causa.

1. Examina las opciones de limpieza activadas, la visibilidad del objeto, la geometría y las normales.

2. Si necesitas restaurar, usa Undo o un punto de control guardado para recuperar el estado anterior.

3. Antes de reintentar, corrige el problema identificado.

Consulta los [controles de Fix Model](09-cats.md#fix-model).

---

### Fase 2 — Generación de visemas {#phase-2--viseme-generation}

Ejecutar después de: Fix Model ✓

Visemes crea las 15 formas de boca para sincronización labial VRChat a partir de tres formas base existentes. Si tu avatar ya tiene claves de forma completas de visemas, puedes omitir esta fase, pero compruébalas en VRChat Viseme Mapping (guía 8).

VRChat necesita 15 formas de boca (visemas) para controlar los labios al hablar. La mayoría de los avatares solo tienen unas pocas formas básicas. CATS combina tus formas base para crear las demás.

Las tres formas base:

- **A Shape** — boca muy abierta (la forma «ahh»)
- **O Shape** — boca redondeada (la forma «ohh»)
- **CH Shape** — boca estrecha y abierta con dientes visibles (la forma «ch» / «sh»)

**Si tu avatar no tiene claves de forma de boca:** esculpe o edita primero A, O y CH como claves de forma. CATS las usa para generar las restantes. Consulta Shape Key en el glosario.

**Pasos:**

1. Abre **CATS → CATS → Visemes**.

2. Elige selección automática o manual de fuentes a continuación.

   Para selección automática, selecciona **Auto-Detect** para rellenar las tres formas fuente.

   Para selección manual, elige la coincidencia más próxima para cada una de las tres formas fuente.

   Algunos nombres de ejemplo son `mouth_open`, `vrc.v_O` y `mouth_wide`.

3. Selecciona **Generate Visemes**.

4. Comprueba que Pipeline Status muestra Visemes ✓.

CATS crea 15 claves de forma con nombres VRChat, incluidos `vrc.v_aa`, `vrc.v_O` y `vrc.v_CH`.

**Deberías ver:** 15 claves de forma nuevas en Shape Keys de la malla (Properties → Object Data → Shape Keys).

Consulta los [controles de CATS Visemes](09-cats.md#visemes).

---

### Fase 3 — Seguimiento ocular {#phase-3--eye-tracking}

Ejecutar después de: Fix Model ✓

Eye Tracking configura los huesos de ojos para el seguimiento ocular integrado de VRChat. Los ojos pueden moverse y mirar a otros jugadores.

**Qué hace:**

- Encuentra los huesos de ojo izquierdo y derecho
- Les asigna los nombres requeridos por VRChat (`LeftEye` y `RightEye`)
- Añade las restricciones de rotación necesarias para moverlos en VRChat
- Limita su rotación a un rango natural (arriba, abajo y hacia los lados)

Auto-Detect busca nombres habituales de huesos de ojos. No examina la geometría de la malla ni las posiciones de los huesos.

Si renombras los huesos:

1. Ejecuta de nuevo la detección.

2. Comprueba ambas asignaciones de huesos de ojos.

Si el movimiento ocular es incorrecto, examina la orientación de huesos, las restricciones y el avatar exportado.

**Pasos:**

1. Abre **CATS → CATS → Eye Tracking**.

2. Selecciona **Auto-Detect** para buscar nombres comunes de huesos de ojo izquierdo y derecho.

3. Comprueba los campos **Left Eye** y **Right Eye**.

4. Si una asignación es incorrecta, selecciona manualmente el hueso correcto.

5. Si hace falta, configura **Up Limit**, **Down Limit** y **Side Limit**.

6. Selecciona **Create Eye Tracking**.

7. Comprueba que Pipeline Status muestra Eye Tracking ✓.

**Deberías ver:** ambos huesos de ojos renombrados, con restricciones de rotación en Bone Constraints.

> **Si CATS no encuentra huesos de ojos:** puede que tu esqueleto no tenga ninguno. Algunos formatos, especialmente modelos MMD antiguos, parpadean con claves de forma en lugar de huesos. Omite esta fase: VRChat usa animación ocular mediante claves de forma cuando no hay huesos de ojos.

---

### Fase 4 — Pose to Shape Key {#phase-4--pose-to-shape-key}

Ejecutar después de: Fix Model ✓

El botón actual **Pose to Shape Key** captura la mezcla de claves de forma actual de la malla seleccionada. No hornea la deformación de los huesos del esqueleto. Para una pose deformada por huesos, usa el [flujo nativo comprobado Save as Shape Key](09-cats.md#save-a-bone-deformed-pose).

**Pasos:**

1. Cambia a Object Mode.

2. Selecciona la malla de destino.

3. Configura los valores de sus claves de forma existentes para obtener la mezcla que quieres capturar.

4. Mantén activa la malla.

5. Abre **CATS → CATS → Pose & Shape Keys**.

6. Selecciona **Pose to Shape Key**.

7. Introduce el nombre de la nueva clave de forma.

8. Confirma la operación.

9. Restablece los valores de las claves originales a 0.

10. Examina la nueva clave sola.

11. Comprueba que Pipeline Status muestra Pose To Shape ✓.

La herramienta ya asigna el valor 1 a la nueva clave.

**Deberías ver:** una clave de forma nueva que reproduce la mezcla capturada. Dejar activas las claves originales vuelve a sumar su deformación.

> **Shape Key to Basis:** convierte la clave activa que no sea Basis en la nueva Basis. Ajusta las demás claves respecto a esa Basis. Guarda un punto de control antes de esta operación. Después, revisa las claves restantes.

Consulta los [controles de Pose to Shape Key](09-cats.md#pose-to-shape-key).

---

### Fase 5 — Aplicar transformaciones {#phase-5--apply-transforms}

Ejecutar después de: todas las fases anteriores que necesites

Apply Transforms es la fase final recomendada de preparación. Aplica posición, rotación y escala a la malla y al esqueleto. Los canales se restablecen a 0, 0 y 1, respectivamente.

Guarda un punto de control antes de esta operación. Compara el avatar antes y después. Las herramientas anteriores siguen disponibles.

Si el avatar exportado tiene un tamaño incorrecto, examina las transformaciones de malla y esqueleto y los ajustes de escala de exportación e importación. Usa Undo o un punto de control guardado si necesitas restaurar un estado anterior.

**Herramientas de Transforms & FBT:**

- **Apply All Transforms** — aplica conjuntamente posición, rotación y escala a malla y esqueleto
- **Fix FBT** — corrección de transformaciones para Full Body Tracking (mueve el hueso raíz al nivel del suelo)
- **Remove FBT** — elimina esa corrección

Material Atlas y Pose To Shape son opcionales. Si mapeaste visemas existentes, Visemes permanece sin marcar.

**Pasos:**

1. En Pipeline Status, confirma que las fases que necesita tu avatar están marcadas.

2. Abre **CATS → CATS → Transforms & FBT**.

3. Selecciona **Apply All Transforms**.

4. Comprueba que Pipeline Status muestra Apply Transforms ✓.

5. Exporta mediante **CATS → Import / Export → Game Engine Export → Unity / VRChat** (guía 1, paso 9).

**Deberías ver:** Apply Transforms marcado después de las fases que necesitabas. Revisa el avatar exportado en VRChat Creator Companion.

Consulta los [controles de transformaciones y FBT](09-cats.md#apply-all-transforms).

---

**Lo que esto permite:** un avatar preparado para comprobar la exportación, con la limpieza, las formas de boca, el seguimiento ocular y las expresiones que elegiste. Valídalo en la aplicación de destino antes de subirlo.

Siguiente: [El pipeline de CATS](04-cats-pipeline.md)
