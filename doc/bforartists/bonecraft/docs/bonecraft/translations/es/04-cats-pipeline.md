# El pipeline de CATS {#the-cats-pipeline}

[← Índice](index.md)

**Lee esto antes de usar cualquier herramienta CATS por primera vez.**

Las herramientas CATS proporcionan un flujo de preparación recomendado. Revisa las fases en este orden. Omite las que no necesite tu avatar. Antes de cambiar datos de malla o rig, guarda un punto de control del archivo. Examina cada resultado. Las herramientas siguen disponibles si una fase anterior está incompleta.

---

## Las seis fases, en orden {#the-six-phases-in-order}

Pipeline Status de la pestaña CATS enumera las fases y marca cada una cuando termina:

1. **Fix Model** — Revisa las opciones de limpieza, como eliminar duplicados y corregir normales. Examina la malla después de la operación.

2. **Material Atlas** — Combina los materiales del avatar en una hoja de texturas (opcional, para mejorar el rendimiento).

    1. Mantén **Preserve Backup Duplicate** activado hasta revisar el resultado.

    2. Selecciona **Analyze Materials**.

    3. Selecciona las fuentes.

    4. Selecciona **Bake Checked Sources**.

    5. Revisa el resultado.

    6. Usa Accept o Revert antes de otro horneado.

    Consulta [Material Atlas Combiner](09-cats.md#material-atlas-combiner).

3. **Visemes** — Genera las 15 formas de boca de sincronización labial VRChat a partir de tus tres formas base (A, O, CH).

4. **Eye Tracking** — Configura el movimiento ocular de VRChat con los huesos de ojos del avatar.

5. **Pose to Shape Key** — Captura la mezcla actual de claves de forma de la malla como una nueva clave. Este botón no hornea la deformación de los huesos del esqueleto. Consulta el [flujo nativo de pose de huesos](09-cats.md#save-a-bone-deformed-pose) para esa tarea.

6. **Apply All Transforms** — Aplica posición, rotación y escala a la malla y al esqueleto. Compara el resultado antes de exportar.

---

## Pipeline Status y Operation Ledger {#pipeline-status-and-the-operation-ledger}

Pipeline Status muestra una línea por fase. Cuando termina una fase, su línea muestra una marca de verificación. La escena guarda ese estado con el archivo.

Operation Ledger enumera cada operación CATS, con la más reciente al final, su hora y resultado. Changed indica que la operación cambió el modelo. Clean indica que no fueron necesarios cambios. Failed indica que la operación falló. **Copy** copia el registro al portapapeles para solicitar asistencia. **Clear** lo vacía.

El orden es orientativo. Si una fase anterior está incompleta, las herramientas siguen funcionando con un aviso como «Run Fix Model first for best results». Revisa el aviso antes de continuar.

Descripción de imagen del original en inglés (imagen omitida): Pipeline Status enumera las seis fases en el orden recomendado.

*Panel emergente nativo, BoneCraft 9.2.18. Pipeline Status enumera las seis fases en el orden recomendado.*

Descripción de imagen del original en inglés (imagen omitida): Operation Ledger antes de que existan entradas. Copy y Clear actúan sobre las entradas registradas.

*Panel emergente nativo, BoneCraft 9.2.18. Operation Ledger antes de que existan entradas. Copy y Clear actúan sobre las entradas registradas.*

---

## Por qué este orden {#why-this-order}

Este orden facilita revisar un tipo de cambio cada vez:

- **Revisa primero la limpieza.** Fix Model puede cambiar geometría o eliminar datos, según sus opciones. Comprueba la malla y sus claves de forma existentes antes de generar más datos.

- **Revisa las formas de boca y después los ojos.** Prueba los visemas generados o mapeados. Eye Auto-Detect busca nombres de huesos. Comprueba las asignaciones Left Eye y Right Eye por separado de la orientación de huesos y las restricciones.

- **Revisa después la captura de expresiones.** Pose to Shape Key captura una mezcla de claves de forma, no una deformación de huesos.

    1. Restablece los valores de las claves originales a 0.

    2. Prueba la nueva clave con valor 1.

    Para guardar una pose deformada por huesos, usa el flujo nativo enlazado arriba.

- **Revisa las transformaciones antes de exportar.** Aplicar transformaciones cambia los datos de objetos y restablece los canales de transformación. Las herramientas anteriores siguen disponibles. Compara el resultado y los ajustes de exportación. Para restaurar el estado anterior, usa Undo o un punto de control guardado.

---

## Antes de omitir una fase {#before-skipping-a-phase}

**Omitir Fix Model:**
Examina la geometría importada, las normales, los pesos, los modificadores y las claves de forma existentes. Selecciona las operaciones de limpieza que necesita tu avatar. Comprueba por separado los problemas de formas de boca y movimiento ocular. Una fase sin marcar no identifica por sí sola su causa.

**Omitir Visemes:**
Sin visemas generados o mapeados, el avatar no tiene sincronización labial. Si ya existen claves de forma de visemas, asígnalas en VRChat Viseme Mapping (guía 8). No generes sustitutos innecesariamente. Pipeline Status dejará Visemes sin marcar. Es lo esperado.

**Omitir Eye Tracking:**
El avatar no tendrá movimiento ocular en VRChat y mirará al frente. Es aceptable si no tiene huesos de ojos.

**Omitir Pose to Shape:**
Es opcional: omítelo si no necesitas una instantánea de la mezcla actual de claves de forma. Puedes revisar y usar las expresiones existentes sin crear otra clave.

Siguiente: [Herramientas de rig](05-rig-tools.md)
