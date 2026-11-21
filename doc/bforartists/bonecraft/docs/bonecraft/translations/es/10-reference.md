# Soluciones rápidas y glosario {#quick-fixes-and-glossary}

[← Contenido](index.md)

## Índice de soluciones rápidas {#quick-fix-index}

Use este índice para encontrar orientación sobre un problema.

| Problema | Dónde consultar |
|---|---|
| La carga falla: no se reconocen los huesos | [Guía 4](02-guides-a.md#guide-4-fix-your-avatars-bone-names) + [Opciones adicionales de nombres de VRChat](08-vrchat.md#vrchat-naming-extras) |
| El avatar queda en pose T o no sigue el movimiento | [Guía 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system) + [Configurar los huesos humanoides](08-vrchat.md#set-up-humanoid-bones) |
| La malla se deforma de forma extraña o la piel se estira | [Transferencia de pesos](05-rig-tools.md#weight-transfer) + [Reflejo de pesos](05-rig-tools.md#weight-mirror), o recalcule con [Recálculo automático de pesos de huesos](05-rig-tools.md#automatic-bone-weight-recalculation) |
| Un lado del cuerpo tiene pesos diferentes | [Reflejo de pesos](05-rig-tools.md#weight-mirror) |
| El pelo atraviesa la cabeza | [Guía 6, paso 5](02-guides-a.md#step-5--add-colliders-recommended): añada colisionadores |
| La física del pelo no se mueve | [Guía 6](02-guides-a.md#guide-6-add-hair-physics): compruebe la detección de cadenas y el preajuste de PhysBone |
| La ropa atraviesa el cuerpo | [Guía 7](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body): <ol><li>Inspeccione la malla posada.</li><li>Si hay intersecciones, ajuste el encaje o los pesos.</li></ol> **Detect Collisions** solo comprueba los nombres de huesos. |
| La sincronización labial no funciona | [Guía 8](03-guides-b.md#guide-8-set-up-lip-sync) + [Asignación de visemas de VRChat](08-vrchat.md#vrchat-viseme-mapping) |
| El avatar tiene un rendimiento Very Poor | [Guía 9](03-guides-b.md#guide-9-improve-your-avatars-performance) + [Comprobar el rendimiento](08-vrchat.md#check-performance) |
| La importación de VRM falla | [Guía 2, paso 1](02-guides-a.md#step-1--install-the-vrm-add-on): instale el complemento VRM |
| La importación de MMD falla | [Guía 3, paso 1](02-guides-a.md#step-1--install-mmd_tools): instale mmd_tools |
| MMD está instalado, pero su puente está inactivo | Active mmd_tools mediante **Open Add-on Preferences**. Revise el mensaje de instalación en la [Guía 3](02-guides-a.md#step-1--install-mmd_tools). |
| La selección del atlas cambia al actualizar | **Refresh Analysis** reconstruye las opciones. <ol><li>Revise las fuentes.</li><li>Seleccione Bake Checked Sources.</li></ol> Consulte [Combinador de atlas de materiales](09-cats.md#material-atlas-combiner). |
| Select All deja una textura sin marcar | Las texturas ausentes siguen excluidas. La selección en bloque solo cambia su lista en el grupo activo: [selección de fuentes](09-cats.md#analyze-and-choose-sources) |
| El atlas informa de que una fuente ha cambiado | <ol><li>Actualice el análisis.</li><li>Revise las fuentes de nuevo.</li></ol> La comprobación previa rechaza las fuentes analizadas que estén desactualizadas antes de crear la copia de seguridad. |
| El atlas no tiene la opción Revert | **Preserve Backup Duplicate** estaba desactivado, o Accept eliminó la copia de seguridad. Use el punto de control que guardó en un archivo. |
| Se bloquea el horneado del atlas metálico u ORM | Deje desactivadas **Metallic** y **Pack ORM Channels**. Estas pasadas siguen bloqueadas en 9.2.18. |
| La textura del atlas se ve desordenada en el motor | Compruebe UV0. **Keep Source UV Maps** puede dejar `atlas_uv` en UV1: [ajustes UV](09-cats.md#advanced-options) |
| La exportación falla desde Pose Mode o Edit Mode | Use el botón principal actual de Unity o Unreal. Restaura el modo y la selección. Use Object Mode para **Export (Profile)**. |
| Los nombres de exportación presentan un conflicto | Corrija el nombre de destino o la asignación humanoide: [Nombres de huesos para exportación](08-vrchat.md#export-bone-naming) |
| All Actions está bloqueado con un preajuste de nombres | Seleccione **Active Action**, **No Animation** o **Keep Original Names**: [Exportación validada por perfil](08-vrchat.md#validated-profile-export). |
| Las formas antiguas de mecanismos necesitan una versión actual | 9.2.18 lee y aplica las formas anteriores sin volver a guardarlas: [Formas](07-mechanisms.md#forms) |
| El validador de rigs muestra errores | [Validador de rigs](05-rig-tools.md#rig-validator): <ol><li>Ejecute la validación.</li><li>Siga los mensajes.</li></ol> |
| Los huesos han desaparecido o no se ve ninguno | [Colecciones de huesos](05-rig-tools.md#bone-collections) → **Show All Collections** |
| No encuentro los paneles de BoneCraft | BoneCraft y Rig Builder usan Tool Shelf, a la izquierda (**T**). CATS usa la barra lateral derecha (**N**). Consulte [Dónde está cada cosa](01-start.md#where-things-are). |
| Quiero un ejemplo completo de Mechanisms | [Tutorial: Crescent Rose](12-crescent-rose.md): 8 pasos de preparación y 30 pasos de Mechanisms con instrucciones escritas y las descripciones conservadas de las imágenes de la fuente inglesa, y el archivo terminado en `examples/crescent-rose/` |
| Una pestaña está en el lado incorrecto | Preferences → Add-ons → BoneCraft → Tabs → Left o Right |
| Faltan las secciones de BoneCraft en Properties → Scene | Preferences → Add-ons → BoneCraft → Tabs → Scene Properties → Show. El azul indica que está activado. Compruebe también los paquetes de herramientas en Tools. |
| Quiero ocultar BoneCraft en Properties → Scene | Desactive Scene Properties → Show en Preferences → Tabs. Las pestañas de la vista y la pestaña de datos de Armature no cambian. |
| Una herramienta se ejecuta antes de que pueda elegir sus opciones | En 9.1, ajuste sus opciones inmediatamente después en el panel Adjust Last Operation de la vista, antes de ejecutar otra operación |
| Place Rig Markers no coloca un marcador | <ol><li>Inicie Auto-Rig Wizard.</li><li>Avance hasta un paso de marcadores.</li><li>Cambie a Object Mode.</li><li>Haga clic en la malla seleccionada del asistente.</li></ol> Consulte [Rig Builder](06-rig-builder.md#auto-rig-wizard). |
| Build Mechanism no sabe qué piezas usar | <ol><li>Use primero Add Parts from Selection.</li><li>Seleccione el rig del mecanismo o una de sus piezas.</li><li>Seleccione el tipo en el encabezado de la herramienta.</li><li>Haga clic en la primera pieza.</li></ol> Consulte [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each). |
| La exportación se bloquea: indica que faltan huesos humanoides aunque existen | Si un hueso obligatorio no existe, primero debe añadirlo al rig. Si los huesos obligatorios existen: <ol><li>Ejecute Auto-Map All.</li><li>Ejecute Fix Humanoid Map en lint, en VRM / VRoid.</li></ol> Consulte la [Guía 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system). |
| El FBX exportado muestra formas auxiliares o tubos gigantes | Si no necesita mallas de controles ni de formas personalizadas, deje **Helper Meshes** desactivado. |
| Unity o Unreal importa materiales grises | <ol><li>Exporte con Embed Textures activado.</li><li>Use las opciones de importación/extracción de materiales de Unity o la importación de materiales FBX de Unreal.</li></ol> |
| Todos los pesos están en los huesos incorrectos | Vuelva a ejecutar Generate Rig del asistente, use [Transferencia de pesos](05-rig-tools.md#weight-transfer) o **Smart Automatic Weights** en la pestaña CATS |
| Necesito unir dos rigs | [Guía 11: Unir dos rigs](03-guides-b.md#guide-11-merge-two-rigs-together) |
| La forma correctiva no se activa | Compruebe el eje del hueso y el ángulo en [Claves de forma correctivas](05-rig-tools.md#corrective-shape-keys) |
| La animación se ve mal en otro rig | [Retarget](05-rig-tools.md#retarget): compruebe la asignación de huesos |
| Una herramienta CATS avisa «Run Fix Model first» | <ol><li>Revise las opciones de limpieza.</li><li>Decida si el avatar las necesita.</li></ol> El aviso no bloquea las herramientas. Consulte [El flujo de trabajo CATS](04-cats-pipeline.md). |
| La boca se desgarra o se separa al hablar | Inspeccione las claves de boca de origen, la topología de la malla y los modificadores: [CATS: Visemas](09-cats.md#visemes) |
| Los ojos del avatar quedan mirando hacia abajo en VRChat | <ol><li>Compruebe las asignaciones de huesos izquierdo/derecho, la orientación y las restricciones.</li><li>Inspeccione el avatar exportado.</li></ol> Consulte [CATS: Seguimiento ocular](09-cats.md#eye-tracking). |
| Una clave de forma hace que la malla explote al activarla | <ol><li>Pruebe la clave por separado.</li><li>Inspeccione la topología, los valores de las claves de origen y los modificadores.</li></ol> BoneCraft captura una mezcla de claves, no la deformación de huesos. Consulte [CATS: Pose y claves de forma](09-cats.md#pose--shape-keys). |
| El avatar aparece con un tamaño incorrecto en VRChat | Compruebe las transformaciones de la malla y del armature, y los ajustes de escala de exportación/importación. Si necesita restaurar el estado anterior, use Undo o un punto de control guardado. Consulte [Aplicar todas las transformaciones](09-cats.md#apply-all-transforms). |
| Los nombres de huesos están en japonés, chino o coreano | [CATS: Traducir nombres de huesos](09-cats.md#translate-bone-names) |
| El avatar no tiene sincronización labial ni claves de forma de boca | [CATS: Visemas](09-cats.md#visemes): cree primero las formas básicas de boca. CATS genera 15 visemas a partir de tres asignaciones de origen: A, O y CH. |
| Un mecanismo muestra «changed by hand» | [Mechanisms](07-mechanisms.md): use **Keep mine** o **Restore** |

## Glosario {#glossary}

**Adjust Last Operation:** Panel de la vista que permite cambiar las opciones de la última operación. Muchas herramientas de BoneCraft 9.1 se ejecutan primero y muestran aquí sus opciones. Ajústelas antes de realizar otra operación.

**Armature:** Término de Bforartists para un esqueleto: un conjunto de huesos que se pueden posar y animar.

**Blend shape:** Véase Clave de forma.

**Hueso:** Un segmento de un esqueleto. Los huesos forman una jerarquía (padre → hijo) en la que los huesos hijos siguen a sus padres.

**Colección de huesos:** Grupo de huesos con nombre. Puede mostrar u ocultar toda una colección a la vez.

**Bone Names:** Opción de nombres para la exportación. Keep Original Names conserva los nombres. Unity-Preset y Unreal-Preset cambian los nombres de los huesos reconocidos en las copias de exportación.

**Bake Checked Sources:** Acción del atlas que hornea las opciones de grupos y fuentes revisadas sin reconstruir automáticamente el análisis.

**CATS:** Herramientas CATS: preparación de modelos para VRChat con un flujo guiado (limpieza, visemas, seguimiento ocular y transformaciones). Están en la pestaña CATS.

**Flujo de trabajo CATS:** Orden de las seis fases de las herramientas CATS: Fix Model → Material Atlas → Visemes → Eye Tracking → Pose to Shape → Apply Transforms. Las herramientas avisan si no se ha completado una fase anterior de la que dependen.

**Clave de forma correctiva:** Clave de forma que se activa cuando un hueso alcanza un ángulo, para corregir la malla en poses extremas.

**Hueso deformador:** Hueso que mueve la malla. Algunos huesos son solo controles y no deforman la malla.

**Seguimiento ocular:** Herramienta CATS que configura los huesos oculares (`LeftEye`, `RightEye`) y las restricciones de rotación que VRChat usa para mover los ojos.

**FBT (Full Body Tracking):** Función de VRChat que sigue todo el cuerpo, incluidas las caderas y los pies, con hardware adicional, como Vive Trackers. Fix FBT ajusta el hueso raíz para esta función.

**FBX:** Formato de archivo que transporta modelos 3D, esqueletos y animaciones entre programas. Es el formato estándar de VRChat.

**Fix Model:** Operaciones de limpieza CATS seleccionables para vértices duplicados, geometría suelta, normales y otros datos.

1. Revise las opciones.

2. Ejecute solo las operaciones que su avatar necesite.

**FK (Forward Kinematics):** Posado mediante la rotación sucesiva de cada hueso de una cadena: hombro, después codo y después muñeca. Resulta natural para poses amplias del cuerpo.

**IK (Inverse Kinematics):** Posado mediante la colocación del extremo de una cadena, como una mano o un pie. Los huesos intermedios lo siguen. Este método sirve para colocar manos y pies con precisión.

**Humanoide:** Sistema de avatares de VRChat que asigna los huesos a posiciones corporales estándar, de modo que todos los avatares usen los mismos controles de movimiento.

**Mecanismo:** Rig de un accesorio o una máquina construido con huesos y restricciones ordinarios. Puede ser una articulación (Hinge, Slide, Telescope) o un enlace (Piston, Gear Link, Follow). Consulte [Mechanisms](07-mechanisms.md).

**Malla:** Superficie 3D que forma el cuerpo visible del avatar.

**MMD (MikuMikuDance):** Software gratuito de animación 3D popular en Japón y en la comunidad del anime. Usa archivos de modelo `.pmx` y archivos de animación `.vmd`.

**Morph target:** Véase Clave de forma.

**Operation Ledger:** Lista de CATS de todas las operaciones ejecutadas, con su hora y resultado.

**PhysBone:** Componente de VRChat que hace que los huesos oscilen, reboten y colisionen. Se usa para pelo, colas y accesorios colgantes.

**Pipeline Status:** Lista de CATS de las seis fases, con una marca de verificación en cada fase completada.

**PMX:** Principal formato de modelos 3D de MikuMikuDance.

**Pose Mode:** Modo para posar y animar huesos.

1. Seleccione el armature.

2. Pulse Ctrl+Tab.

También puede seleccionar Pose Mode en el desplegable de modos de la esquina superior izquierda de la vista.

**Rig / rigging:** Construcción de un esqueleto dentro de un modelo 3D y conexión de la malla con él para poder posarlo y animarlo.

**Clave de forma:** Versión guardada de una malla en una posición deformada. Las claves de forma se mezclan con distintas intensidades. Controlan expresiones faciales, sincronización labial y cambios de forma del cuerpo.

**SDK (Software Development Kit):** En VRChat, VRChat Creator Companion y sus herramientas de Unity para subir avatares.

**Spline IK:** Cadena de huesos que sigue una curva. Se usa para colas, tentáculos, pelo largo y columnas vertebrales.

**Pose T:** Pose de referencia: de pie, erguido y con los brazos extendidos a los lados.

**Tool Shelf:** Panel izquierdo de la vista 3D (**T**). BoneCraft y Rig Builder usan este panel de forma predeterminada.

**Vértice:** Punto individual en el espacio 3D. Las mallas están compuestas por muchos vértices unidos mediante aristas y caras.

**Grupo de vértices:** Conjunto de vértices con nombre que define qué vértices mueve un hueso.

**Visema:** Forma de boca correspondiente a un sonido del habla. VRChat usa 15 visemas para la sincronización labial.

**Peso / pintura de pesos:** Valores de 0.0 a 1.0 que indican con qué intensidad mueve cada hueso a cada vértice. La pintura de pesos es la forma visual de ajustarlos.

**Asistente:** Auto-Rig Wizard de Rig Builder: coloca marcadores en la malla y construye el rig a partir de ellos.

**Hueso sin peso:** Hueso que no mueve ningún vértice. Reduce el rendimiento sin cambiar el aspecto del avatar. Fix Model y el optimizador de rendimiento eliminan estos huesos.

Siguiente: [Novedades](11-whats-new.md)
