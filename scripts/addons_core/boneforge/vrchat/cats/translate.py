"""BoneCraft VRChat — Bone Name Translation.

Translate foreign-language bone names to English. Supports:
  - Japanese  (MMD standard — auto-detected via Unicode)
  - Chinese   (Simplified MMD/VRChat — auto-detected via Unicode)
  - Korean    (Korean VRChat community — auto-detected via Unicode)
  - Portuguese (Brazilian Blender community — matched by dictionary)
  - Spanish   (Latin American/Spanish community — matched by dictionary)
  - French    (French Blender community — matched by dictionary)

AUTO mode detects Japanese, Chinese, or Korean via Unicode.
Latin-based languages (Portuguese, Spanish, French) require explicit selection.

Category: VRChat Cats Tools.
"""

import re
from typing import Dict, List, Optional, Tuple

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator, Panel

from boneforge.core import active_armature
from boneforge.i18n import T


# ─────────────────────────────────────────────────────────────────
# Language Dictionaries — All → English
# ─────────────────────────────────────────────────────────────────

# ── Japanese (MMD standard) ──────────────────────────────────────
JAPANESE_TO_ENGLISH: Dict[str, str] = {
    # Core
    "センター":         "Center",
    "グルーブ":         "Groove",
    "全ての親":         "Master",

    # Torso
    "上半身":           "Upper Body",
    "上半身2":          "Upper Body2",
    "下半身":           "Lower Body",
    "腰":               "Waist",
    "腹":               "Abdomen",
    "胸":               "Chest",
    "肩":               "Shoulder",

    # Head / Neck
    "首":               "Neck",
    "頭":               "Head",

    # Arms — Left
    "左肩":             "Left Shoulder",
    "左腕":             "Left Arm",
    "左腕捩":           "Left Arm Twist",
    "左ひじ":           "Left Elbow",
    "左手捩":           "Left Hand Twist",
    "左手首":           "Left Wrist",
    "左手":             "Left Hand",

    # Arms — Right
    "右肩":             "Right Shoulder",
    "右腕":             "Right Arm",
    "右腕捩":           "Right Arm Twist",
    "右ひじ":           "Right Elbow",
    "右手捩":           "Right Hand Twist",
    "右手首":           "Right Wrist",
    "右手":             "Right Hand",

    # Legs — Left
    "左足":             "Left Leg",
    "左ひざ":           "Left Knee",
    "左足首":           "Left Ankle",
    "左つま先":         "Left Toe",
    "左足D":            "Left Leg D",
    "左ひざD":          "Left Knee D",
    "左足首D":          "Left Ankle D",
    "左足先EX":         "Left Toe EX",

    # Legs — Right
    "右足":             "Right Leg",
    "右ひざ":           "Right Knee",
    "右足首":           "Right Ankle",
    "右つま先":         "Right Toe",
    "右足D":            "Right Leg D",
    "右ひざD":          "Right Knee D",
    "右足首D":          "Right Ankle D",
    "右足先EX":         "Right Toe EX",

    # Fingers — Left
    "左親指0":  "Left Thumb0",   "左親指1":  "Left Thumb1",   "左親指2":  "Left Thumb2",
    "左人指1":  "Left Index1",   "左人指2":  "Left Index2",   "左人指3":  "Left Index3",
    "左中指1":  "Left Middle1",  "左中指2":  "Left Middle2",  "左中指3":  "Left Middle3",
    "左薬指1":  "Left Ring1",    "左薬指2":  "Left Ring2",    "左薬指3":  "Left Ring3",
    "左小指1":  "Left Pinky1",   "左小指2":  "Left Pinky2",   "左小指3":  "Left Pinky3",
    "左親指":   "Left Thumb",    "左人指":   "Left Index",
    "左中指":   "Left Middle",   "左薬指":   "Left Ring",     "左小指":   "Left Pinky",

    # Fingers — Right
    "右親指0":  "Right Thumb0",  "右親指1":  "Right Thumb1",  "右親指2":  "Right Thumb2",
    "右人指1":  "Right Index1",  "右人指2":  "Right Index2",  "右人指3":  "Right Index3",
    "右中指1":  "Right Middle1", "右中指2":  "Right Middle2", "右中指3":  "Right Middle3",
    "右薬指1":  "Right Ring1",   "右薬指2":  "Right Ring2",   "右薬指3":  "Right Ring3",
    "右小指1":  "Right Pinky1",  "右小指2":  "Right Pinky2",  "右小指3":  "Right Pinky3",
    "右親指":   "Right Thumb",   "右人指":   "Right Index",
    "右中指":   "Right Middle",  "右薬指":   "Right Ring",    "右小指":   "Right Pinky",

    # Eyes / Face
    "両目":             "Eyes",
    "左目":             "Left Eye",
    "右目":             "Right Eye",
    "口":               "Mouth",
    "舌1":              "Tongue1",
    "舌2":              "Tongue2",
    "舌3":              "Tongue3",

    # IK
    "左足IK":           "Left Foot IK",
    "右足IK":           "Right Foot IK",
    "左つま先IK":       "Left Toe IK",
    "右つま先IK":       "Right Toe IK",
}


# ── Chinese Simplified (MMD / VRChat community) ──────────────────
# Sources: Chinese MMD community naming conventions, VRChat CN creator tools
CHINESE_TO_ENGLISH: Dict[str, str] = {
    # Core
    "中心":             "Center",
    "中心骨":           "Center",
    "主骨":             "Master",
    "根骨":             "Root",

    # Torso
    "脊椎":             "Spine",
    "腰部":             "Waist",
    "腹部":             "Abdomen",
    "胸部":             "Chest",
    "上身":             "Upper Body",
    "下身":             "Lower Body",
    "上半身":           "Upper Body",
    "下半身":           "Lower Body",
    "臀部":             "Hips",

    # Head / Neck
    "颈部":             "Neck",
    "脖子":             "Neck",
    "头部":             "Head",
    "头":               "Head",

    # Arms — Left (左 = Left)
    "左肩":             "Left Shoulder",
    "左上臂":           "Left Arm",
    "左臂":             "Left Arm",
    "左肘":             "Left Elbow",
    "左前臂":           "Left Forearm",
    "左手腕":           "Left Wrist",
    "左手":             "Left Hand",

    # Arms — Right (右 = Right)
    "右肩":             "Right Shoulder",
    "右上臂":           "Right Arm",
    "右臂":             "Right Arm",
    "右肘":             "Right Elbow",
    "右前臂":           "Right Forearm",
    "右手腕":           "Right Wrist",
    "右手":             "Right Hand",

    # Legs — Left
    "左大腿":           "Left Upper Leg",
    "左腿":             "Left Leg",
    "左膝":             "Left Knee",
    "左小腿":           "Left Lower Leg",
    "左脚踝":           "Left Ankle",
    "左脚":             "Left Foot",
    "左趾":             "Left Toe",
    "左脚趾":           "Left Toe",

    # Legs — Right
    "右大腿":           "Right Upper Leg",
    "右腿":             "Right Leg",
    "右膝":             "Right Knee",
    "右小腿":           "Right Lower Leg",
    "右脚踝":           "Right Ankle",
    "右脚":             "Right Foot",
    "右趾":             "Right Toe",
    "右脚趾":           "Right Toe",

    # Fingers — Left
    "左拇指1":  "Left Thumb1",   "左拇指2":  "Left Thumb2",   "左拇指3":  "Left Thumb3",
    "左食指1":  "Left Index1",   "左食指2":  "Left Index2",   "左食指3":  "Left Index3",
    "左中指1":  "Left Middle1",  "左中指2":  "Left Middle2",  "左中指3":  "Left Middle3",
    "左无名指1": "Left Ring1",   "左无名指2": "Left Ring2",   "左无名指3": "Left Ring3",
    "左小指1":  "Left Pinky1",   "左小指2":  "Left Pinky2",   "左小指3":  "Left Pinky3",
    "左拇指":   "Left Thumb",    "左食指":   "Left Index",
    "左中指":   "Left Middle",   "左无名指": "Left Ring",     "左小指":   "Left Pinky",

    # Fingers — Right
    "右拇指1":  "Right Thumb1",  "右拇指2":  "Right Thumb2",  "右拇指3":  "Right Thumb3",
    "右食指1":  "Right Index1",  "右食指2":  "Right Index2",  "右食指3":  "Right Index3",
    "右中指1":  "Right Middle1", "右中指2":  "Right Middle2", "右中指3":  "Right Middle3",
    "右无名指1": "Right Ring1",  "右无名指2": "Right Ring2",  "右无名指3": "Right Ring3",
    "右小指1":  "Right Pinky1",  "右小指2":  "Right Pinky2",  "右小指3":  "Right Pinky3",
    "右拇指":   "Right Thumb",   "右食指":   "Right Index",
    "右中指":   "Right Middle",  "右无名指": "Right Ring",    "右小指":   "Right Pinky",

    # Eyes / Face
    "双眼":             "Eyes",
    "左眼":             "Left Eye",
    "右眼":             "Right Eye",
    "嘴":               "Mouth",
    "舌头":             "Tongue",
}


# ── Korean (Korean VRChat / Blender community) ───────────────────
# Sources: Korean VRChat creator Discord naming conventions
KOREAN_TO_ENGLISH: Dict[str, str] = {
    # Core
    "중심":             "Center",
    "루트":             "Root",
    "마스터":           "Master",

    # Torso
    "척추":             "Spine",
    "허리":             "Waist",
    "복부":             "Abdomen",
    "가슴":             "Chest",
    "상체":             "Upper Body",
    "하체":             "Lower Body",
    "엉덩이":           "Hips",
    "골반":             "Pelvis",

    # Head / Neck
    "목":               "Neck",
    "머리":             "Head",

    # Arms — Left (왼 = Left)
    "왼어깨":           "Left Shoulder",
    "왼쪽어깨":         "Left Shoulder",
    "왼팔":             "Left Arm",
    "왼쪽팔":           "Left Arm",
    "왼팔꿈치":         "Left Elbow",
    "왼쪽팔꿈치":       "Left Elbow",
    "왼전완":           "Left Forearm",
    "왼손목":           "Left Wrist",
    "왼쪽손목":         "Left Wrist",
    "왼손":             "Left Hand",
    "왼쪽손":           "Left Hand",

    # Arms — Right (오른 = Right)
    "오른어깨":         "Right Shoulder",
    "오른쪽어깨":       "Right Shoulder",
    "오른팔":           "Right Arm",
    "오른쪽팔":         "Right Arm",
    "오른팔꿈치":       "Right Elbow",
    "오른쪽팔꿈치":     "Right Elbow",
    "오른전완":         "Right Forearm",
    "오른손목":         "Right Wrist",
    "오른쪽손목":       "Right Wrist",
    "오른손":           "Right Hand",
    "오른쪽손":         "Right Hand",

    # Legs — Left
    "왼다리":           "Left Leg",
    "왼쪽다리":         "Left Leg",
    "왼허벅지":         "Left Thigh",
    "왼무릎":           "Left Knee",
    "왼쪽무릎":         "Left Knee",
    "왼정강이":         "Left Shin",
    "왼발목":           "Left Ankle",
    "왼쪽발목":         "Left Ankle",
    "왼발":             "Left Foot",
    "왼발가락":         "Left Toe",

    # Legs — Right
    "오른다리":         "Right Leg",
    "오른쪽다리":       "Right Leg",
    "오른허벅지":       "Right Thigh",
    "오른무릎":         "Right Knee",
    "오른쪽무릎":       "Right Knee",
    "오른정강이":       "Right Shin",
    "오른발목":         "Right Ankle",
    "오른쪽발목":       "Right Ankle",
    "오른발":           "Right Foot",
    "오른발가락":       "Right Toe",

    # Fingers — Left
    "왼엄지1": "Left Thumb1",  "왼엄지2": "Left Thumb2",  "왼엄지3": "Left Thumb3",
    "왼검지1": "Left Index1",  "왼검지2": "Left Index2",  "왼검지3": "Left Index3",
    "왼중지1": "Left Middle1", "왼중지2": "Left Middle2", "왼중지3": "Left Middle3",
    "왼약지1": "Left Ring1",   "왼약지2": "Left Ring2",   "왼약지3": "Left Ring3",
    "왼소지1": "Left Pinky1",  "왼소지2": "Left Pinky2",  "왼소지3": "Left Pinky3",
    "왼엄지":  "Left Thumb",   "왼검지":  "Left Index",
    "왼중지":  "Left Middle",  "왼약지":  "Left Ring",    "왼소지":  "Left Pinky",

    # Fingers — Right
    "오른엄지1": "Right Thumb1",  "오른엄지2": "Right Thumb2",  "오른엄지3": "Right Thumb3",
    "오른검지1": "Right Index1",  "오른검지2": "Right Index2",  "오른검지3": "Right Index3",
    "오른중지1": "Right Middle1", "오른중지2": "Right Middle2", "오른중지3": "Right Middle3",
    "오른약지1": "Right Ring1",   "오른약지2": "Right Ring2",   "오른약지3": "Right Ring3",
    "오른소지1": "Right Pinky1",  "오른소지2": "Right Pinky2",  "오른소지3": "Right Pinky3",
    "오른엄지":  "Right Thumb",   "오른검지":  "Right Index",
    "오른중지":  "Right Middle",  "오른약지":  "Right Ring",    "오른소지":  "Right Pinky",

    # Eyes / Face
    "양쪽눈":           "Eyes",
    "왼눈":             "Left Eye",
    "오른눈":           "Right Eye",
    "입":               "Mouth",
    "혀":               "Tongue",
}


# ── Portuguese / Brazilian (Blender BR / VRChat BR community) ────
# Conventions: E = Esquerda (Left), D = Direita (Right)
# Both dot-separated (Braco.E) and underscore (Braco_E) and plain forms included
PORTUGUESE_TO_ENGLISH: Dict[str, str] = {
    # Core
    "Centro":           "Center",
    "Raiz":             "Root",
    "Mestre":           "Master",

    # Torso
    "Quadril":          "Hips",
    "Pelve":            "Pelvis",
    "Coluna":           "Spine",
    "Coluna1":          "Spine1",
    "Coluna2":          "Spine2",
    "Abdomen":          "Abdomen",
    "Peito":            "Chest",
    "CorpoSuperior":    "Upper Body",
    "CorpoInferior":    "Lower Body",
    "Cintura":          "Waist",

    # Head / Neck
    "Pescoco":          "Neck",
    "Pescoço":          "Neck",
    "Cabeca":           "Head",
    "Cabeça":           "Head",

    # Shoulders
    "Ombro.E":          "Left Shoulder",
    "Ombro_E":          "Left Shoulder",
    "OmbroE":           "Left Shoulder",
    "OmbroEsquerdo":    "Left Shoulder",
    "Ombro.D":          "Right Shoulder",
    "Ombro_D":          "Right Shoulder",
    "OmbroD":           "Right Shoulder",
    "OmbroDireito":     "Right Shoulder",

    # Arms — Left
    "Braco.E":          "Left Arm",
    "Braco_E":          "Left Arm",
    "BracoE":           "Left Arm",
    "BracoEsquerdo":    "Left Arm",
    "Cotovelo.E":       "Left Elbow",
    "Cotovelo_E":       "Left Elbow",
    "CotoveloE":        "Left Elbow",
    "Antebraco.E":      "Left Forearm",
    "Antebraco_E":      "Left Forearm",
    "Punho.E":          "Left Wrist",
    "Punho_E":          "Left Wrist",
    "PunhoE":           "Left Wrist",
    "Mao.E":            "Left Hand",
    "Mao_E":            "Left Hand",
    "MaoE":             "Left Hand",
    "Mão.E":            "Left Hand",

    # Arms — Right
    "Braco.D":          "Right Arm",
    "Braco_D":          "Right Arm",
    "BracoD":           "Right Arm",
    "BracoDireito":     "Right Arm",
    "Cotovelo.D":       "Right Elbow",
    "Cotovelo_D":       "Right Elbow",
    "CotoveloD":        "Right Elbow",
    "Antebraco.D":      "Right Forearm",
    "Antebraco_D":      "Right Forearm",
    "Punho.D":          "Right Wrist",
    "Punho_D":          "Right Wrist",
    "PunhoD":           "Right Wrist",
    "Mao.D":            "Right Hand",
    "Mao_D":            "Right Hand",
    "MaoD":             "Right Hand",
    "Mão.D":            "Right Hand",

    # Legs — Left
    "Coxa.E":           "Left Thigh",
    "Coxa_E":           "Left Thigh",
    "Perna.E":          "Left Leg",
    "Perna_E":          "Left Leg",
    "PernaE":           "Left Leg",
    "Joelho.E":         "Left Knee",
    "Joelho_E":         "Left Knee",
    "JoelhoE":          "Left Knee",
    "Tornozelo.E":      "Left Ankle",
    "Tornozelo_E":      "Left Ankle",
    "TornozemE":        "Left Ankle",
    "Pe.E":             "Left Foot",
    "Pe_E":             "Left Foot",
    "Dedao.E":          "Left Toe",
    "Dedao_E":          "Left Toe",

    # Legs — Right
    "Coxa.D":           "Right Thigh",
    "Coxa_D":           "Right Thigh",
    "Perna.D":          "Right Leg",
    "Perna_D":          "Right Leg",
    "PernaD":           "Right Leg",
    "Joelho.D":         "Right Knee",
    "Joelho_D":         "Right Knee",
    "JoelhoD":          "Right Knee",
    "Tornozelo.D":      "Right Ankle",
    "Tornozelo_D":      "Right Ankle",
    "Pe.D":             "Right Foot",
    "Pe_D":             "Right Foot",
    "Dedao.D":          "Right Toe",
    "Dedao_D":          "Right Toe",

    # Fingers — Left
    "Polegar.E": "Left Thumb",  "Polegar1.E": "Left Thumb1", "Polegar2.E": "Left Thumb2",
    "Indicador.E": "Left Index", "Indicador1.E": "Left Index1", "Indicador2.E": "Left Index2",
    "Medio.E": "Left Middle",   "Medio1.E": "Left Middle1",  "Medio2.E": "Left Middle2",
    "Anelar.E": "Left Ring",    "Anelar1.E": "Left Ring1",   "Anelar2.E": "Left Ring2",
    "Mindinho.E": "Left Pinky", "Mindinho1.E": "Left Pinky1","Mindinho2.E": "Left Pinky2",

    # Fingers — Right
    "Polegar.D": "Right Thumb",  "Polegar1.D": "Right Thumb1", "Polegar2.D": "Right Thumb2",
    "Indicador.D": "Right Index","Indicador1.D": "Right Index1","Indicador2.D": "Right Index2",
    "Medio.D": "Right Middle",   "Medio1.D": "Right Middle1",  "Medio2.D": "Right Middle2",
    "Anelar.D": "Right Ring",    "Anelar1.D": "Right Ring1",   "Anelar2.D": "Right Ring2",
    "Mindinho.D": "Right Pinky", "Mindinho1.D": "Right Pinky1","Mindinho2.D": "Right Pinky2",

    # Eyes / Face
    "Olho.E":           "Left Eye",
    "Olho_E":           "Left Eye",
    "Olho.D":           "Right Eye",
    "Olho_D":           "Right Eye",
    "Boca":             "Mouth",
    "Lingua":           "Tongue",
}


# ── Spanish (Latin American / Spanish Blender community) ─────────
# Conventions: Izq / _L = Izquierda (Left), Der / _R = Derecha (Right)
SPANISH_TO_ENGLISH: Dict[str, str] = {
    # Core
    "Centro":           "Center",
    "Raiz":             "Root",
    "Maestro":          "Master",

    # Torso
    "Cadera":           "Hips",
    "Pelvis":           "Pelvis",
    "Columna":          "Spine",
    "Columna1":         "Spine1",
    "Columna2":         "Spine2",
    "Abdomen":          "Abdomen",
    "Pecho":            "Chest",
    "CuerpoSuperior":   "Upper Body",
    "CuerpoInferior":   "Lower Body",
    "Cintura":          "Waist",

    # Head / Neck
    "Cuello":           "Neck",
    "Cabeza":           "Head",

    # Shoulders
    "Hombro.Izq":       "Left Shoulder",
    "Hombro_Izq":       "Left Shoulder",
    "HombroIzq":        "Left Shoulder",
    "HombroIzquierdo":  "Left Shoulder",
    "Hombro.Der":       "Right Shoulder",
    "Hombro_Der":       "Right Shoulder",
    "HombroDer":        "Right Shoulder",
    "HombroDerecho":    "Right Shoulder",

    # Arms — Left
    "Brazo.Izq":        "Left Arm",
    "Brazo_Izq":        "Left Arm",
    "BrazoIzq":         "Left Arm",
    "BrazoIzquierdo":   "Left Arm",
    "Codo.Izq":         "Left Elbow",
    "Codo_Izq":         "Left Elbow",
    "CodoIzq":          "Left Elbow",
    "Antebrazo.Izq":    "Left Forearm",
    "Antebrazo_Izq":    "Left Forearm",
    "Muneca.Izq":       "Left Wrist",
    "Muneca_Izq":       "Left Wrist",
    "MunecaIzq":        "Left Wrist",
    "Mano.Izq":         "Left Hand",
    "Mano_Izq":         "Left Hand",
    "ManoIzq":          "Left Hand",
    "ManoIzquierda":    "Left Hand",

    # Arms — Right
    "Brazo.Der":        "Right Arm",
    "Brazo_Der":        "Right Arm",
    "BrazoDer":         "Right Arm",
    "BrazoDerecho":     "Right Arm",
    "Codo.Der":         "Right Elbow",
    "Codo_Der":         "Right Elbow",
    "CodoDer":          "Right Elbow",
    "Antebrazo.Der":    "Right Forearm",
    "Antebrazo_Der":    "Right Forearm",
    "Muneca.Der":       "Right Wrist",
    "Muneca_Der":       "Right Wrist",
    "MunecaDer":        "Right Wrist",
    "Mano.Der":         "Right Hand",
    "Mano_Der":         "Right Hand",
    "ManoDer":          "Right Hand",
    "ManoDerecha":      "Right Hand",

    # Legs — Left
    "Muslo.Izq":        "Left Thigh",
    "Muslo_Izq":        "Left Thigh",
    "Pierna.Izq":       "Left Leg",
    "Pierna_Izq":       "Left Leg",
    "PiernaIzq":        "Left Leg",
    "Rodilla.Izq":      "Left Knee",
    "Rodilla_Izq":      "Left Knee",
    "RodillaIzq":       "Left Knee",
    "Tobillo.Izq":      "Left Ankle",
    "Tobillo_Izq":      "Left Ankle",
    "TobilloIzq":       "Left Ankle",
    "Pie.Izq":          "Left Foot",
    "Pie_Izq":          "Left Foot",
    "Dedo.Izq":         "Left Toe",
    "Dedo_Izq":         "Left Toe",

    # Legs — Right
    "Muslo.Der":        "Right Thigh",
    "Muslo_Der":        "Right Thigh",
    "Pierna.Der":       "Right Leg",
    "Pierna_Der":       "Right Leg",
    "PiernaDer":        "Right Leg",
    "Rodilla.Der":      "Right Knee",
    "Rodilla_Der":      "Right Knee",
    "RodillaDer":       "Right Knee",
    "Tobillo.Der":      "Right Ankle",
    "Tobillo_Der":      "Right Ankle",
    "TobilloDer":       "Right Ankle",
    "Pie.Der":          "Right Foot",
    "Pie_Der":          "Right Foot",
    "Dedo.Der":         "Right Toe",
    "Dedo_Der":         "Right Toe",

    # Fingers — Left
    "Pulgar.Izq": "Left Thumb",   "Pulgar1.Izq": "Left Thumb1",  "Pulgar2.Izq": "Left Thumb2",
    "Indice.Izq": "Left Index",   "Indice1.Izq": "Left Index1",  "Indice2.Izq": "Left Index2",
    "Medio.Izq":  "Left Middle",  "Medio1.Izq":  "Left Middle1", "Medio2.Izq":  "Left Middle2",
    "Anular.Izq": "Left Ring",    "Anular1.Izq": "Left Ring1",   "Anular2.Izq": "Left Ring2",
    "Menique.Izq":"Left Pinky",   "Menique1.Izq":"Left Pinky1",  "Menique2.Izq":"Left Pinky2",

    # Fingers — Right
    "Pulgar.Der": "Right Thumb",  "Pulgar1.Der": "Right Thumb1", "Pulgar2.Der": "Right Thumb2",
    "Indice.Der": "Right Index",  "Indice1.Der": "Right Index1", "Indice2.Der": "Right Index2",
    "Medio.Der":  "Right Middle", "Medio1.Der":  "Right Middle1","Medio2.Der":  "Right Middle2",
    "Anular.Der": "Right Ring",   "Anular1.Der": "Right Ring1",  "Anular2.Der": "Right Ring2",
    "Menique.Der":"Right Pinky",  "Menique1.Der":"Right Pinky1", "Menique2.Der":"Right Pinky2",

    # Eyes / Face
    "Ojo.Izq":          "Left Eye",
    "Ojo_Izq":          "Left Eye",
    "Ojo.Der":          "Right Eye",
    "Ojo_Der":          "Right Eye",
    "Boca":             "Mouth",
    "Lengua":           "Tongue",
}


# ── French (French Blender / VRChat community) ───────────────────
# Conventions: G / .G / _G = Gauche (Left), D / .D / _D = Droite (Right)
FRENCH_TO_ENGLISH: Dict[str, str] = {
    # Core
    "Centre":           "Center",
    "Racine":           "Root",
    "Maitre":           "Master",

    # Torso
    "Bassin":           "Hips",
    "Hanches":          "Hips",
    "Pelvis":           "Pelvis",
    "Colonne":          "Spine",
    "Colonne1":         "Spine1",
    "Colonne2":         "Spine2",
    "Abdomen":          "Abdomen",
    "Poitrine":         "Chest",
    "CorpsSuperieur":   "Upper Body",
    "CorpsInferieur":   "Lower Body",
    "Taille":           "Waist",

    # Head / Neck
    "Cou":              "Neck",
    "Tete":             "Head",
    "Tête":             "Head",

    # Shoulders
    "Epaule.G":         "Left Shoulder",
    "Epaule_G":         "Left Shoulder",
    "EpauleG":          "Left Shoulder",
    "EpauleGauche":     "Left Shoulder",
    "Épaule.G":         "Left Shoulder",
    "Epaule.D":         "Right Shoulder",
    "Epaule_D":         "Right Shoulder",
    "EpauleD":          "Right Shoulder",
    "EpauleDroite":     "Right Shoulder",
    "Épaule.D":         "Right Shoulder",

    # Arms — Left
    "Bras.G":           "Left Arm",
    "Bras_G":           "Left Arm",
    "BrasG":            "Left Arm",
    "BrasGauche":       "Left Arm",
    "Coude.G":          "Left Elbow",
    "Coude_G":          "Left Elbow",
    "CoudeG":           "Left Elbow",
    "AvantBras.G":      "Left Forearm",
    "AvantBras_G":      "Left Forearm",
    "Poignet.G":        "Left Wrist",
    "Poignet_G":        "Left Wrist",
    "PoignetG":         "Left Wrist",
    "Main.G":           "Left Hand",
    "Main_G":           "Left Hand",
    "MainG":            "Left Hand",
    "MainGauche":       "Left Hand",

    # Arms — Right
    "Bras.D":           "Right Arm",
    "Bras_D":           "Right Arm",
    "BrasD":            "Right Arm",
    "BrasDroit":        "Right Arm",
    "Coude.D":          "Right Elbow",
    "Coude_D":          "Right Elbow",
    "CoudeD":           "Right Elbow",
    "AvantBras.D":      "Right Forearm",
    "AvantBras_D":      "Right Forearm",
    "Poignet.D":        "Right Wrist",
    "Poignet_D":        "Right Wrist",
    "PoignetD":         "Right Wrist",
    "Main.D":           "Right Hand",
    "Main_D":           "Right Hand",
    "MainD":            "Right Hand",
    "MainDroite":       "Right Hand",

    # Legs — Left
    "Cuisse.G":         "Left Thigh",
    "Cuisse_G":         "Left Thigh",
    "Jambe.G":          "Left Leg",
    "Jambe_G":          "Left Leg",
    "JambeG":           "Left Leg",
    "Genou.G":          "Left Knee",
    "Genou_G":          "Left Knee",
    "GenouG":           "Left Knee",
    "Cheville.G":       "Left Ankle",
    "Cheville_G":       "Left Ankle",
    "ChevilleG":        "Left Ankle",
    "Pied.G":           "Left Foot",
    "Pied_G":           "Left Foot",
    "Orteil.G":         "Left Toe",
    "Orteil_G":         "Left Toe",

    # Legs — Right
    "Cuisse.D":         "Right Thigh",
    "Cuisse_D":         "Right Thigh",
    "Jambe.D":          "Right Leg",
    "Jambe_D":          "Right Leg",
    "JambeD":           "Right Leg",
    "Genou.D":          "Right Knee",
    "Genou_D":          "Right Knee",
    "GenouD":           "Right Knee",
    "Cheville.D":       "Right Ankle",
    "Cheville_D":       "Right Ankle",
    "ChevilleD":        "Right Ankle",
    "Pied.D":           "Right Foot",
    "Pied_D":           "Right Foot",
    "Orteil.D":         "Right Toe",
    "Orteil_D":         "Right Toe",

    # Fingers — Left
    "Pouce.G":  "Left Thumb",   "Pouce1.G":  "Left Thumb1",  "Pouce2.G":  "Left Thumb2",
    "Index.G":  "Left Index",   "Index1.G":  "Left Index1",  "Index2.G":  "Left Index2",
    "Majeur.G": "Left Middle",  "Majeur1.G": "Left Middle1", "Majeur2.G": "Left Middle2",
    "Annulaire.G":"Left Ring",  "Annulaire1.G":"Left Ring1", "Annulaire2.G":"Left Ring2",
    "Auriculaire.G":"Left Pinky","Auriculaire1.G":"Left Pinky1","Auriculaire2.G":"Left Pinky2",

    # Fingers — Right
    "Pouce.D":  "Right Thumb",  "Pouce1.D":  "Right Thumb1", "Pouce2.D":  "Right Thumb2",
    "Index.D":  "Right Index",  "Index1.D":  "Right Index1", "Index2.D":  "Right Index2",
    "Majeur.D": "Right Middle", "Majeur1.D": "Right Middle1","Majeur2.D": "Right Middle2",
    "Annulaire.D":"Right Ring", "Annulaire1.D":"Right Ring1","Annulaire2.D":"Right Ring2",
    "Auriculaire.D":"Right Pinky","Auriculaire1.D":"Right Pinky1","Auriculaire2.D":"Right Pinky2",

    # Eyes / Face
    "Oeil.G":           "Left Eye",
    "Oeil_G":           "Left Eye",
    "Oeil.D":           "Right Eye",
    "Oeil_D":           "Right Eye",
    "Bouche":           "Mouth",
    "Langue":           "Tongue",
}


# ── Master lookup ────────────────────────────────────────────────

_LANG_DICTS: Dict[str, Dict[str, str]] = {
    "JAPANESE":     JAPANESE_TO_ENGLISH,
    "CHINESE":      CHINESE_TO_ENGLISH,
    "KOREAN":       KOREAN_TO_ENGLISH,
    "PORTUGUESE":   PORTUGUESE_TO_ENGLISH,
    "SPANISH":      SPANISH_TO_ENGLISH,
    "FRENCH":       FRENCH_TO_ENGLISH,
}


# ─────────────────────────────────────────────────────────────────
# Detection helpers
# ─────────────────────────────────────────────────────────────────

def _contains_japanese(text: str) -> bool:
    """True if text contains hiragana or katakana (kana-only check, avoids CJK ambiguity)."""
    return bool(re.search(r'[぀-ゟ゠-ヿ]', text))


def _contains_cjk(text: str) -> bool:
    """True if text contains CJK unified ideographs (Chinese or Japanese kanji)."""
    return bool(re.search(r'[一-鿿㐀-䶿]', text))


def _contains_korean(text: str) -> bool:
    """True if text contains Hangul syllables."""
    return bool(re.search(r'[가-힣ᄀ-ᇿ㄰-㆏]', text))


def _auto_detect_language(armature) -> Optional[str]:
    """
    Detect the language of bone names via Unicode ranges.
    Returns a language key or None if only ASCII/Latin found.
    Japanese takes priority over Chinese (kana is unambiguous).
    """
    has_jp = False
    has_cjk = False
    has_kr = False

    for bone in armature.data.bones:
        name = bone.name
        if _contains_japanese(name):
            has_jp = True
        if _contains_cjk(name):
            has_cjk = True
        if _contains_korean(name):
            has_kr = True

    if has_jp:
        return "JAPANESE"
    if has_kr:
        return "KOREAN"
    if has_cjk:
        # CJK without kana → treat as Chinese
        return "CHINESE"
    return None


# ─────────────────────────────────────────────────────────────────
# Translation core
# ─────────────────────────────────────────────────────────────────

def translate_bone_names(
    armature,
    language: str,
) -> List[Tuple[str, str]]:
    """
    Scan armature bones and return (old_name, new_name) pairs for all
    bones that have a known translation in the given language dictionary.

    For AUTO: detects Japanese / Chinese / Korean via Unicode.
    Latin languages (Portuguese, Spanish, French) must be selected explicitly.
    """
    if language == "AUTO":
        detected = _auto_detect_language(armature)
        if detected is None:
            return []
        lang_dict = _LANG_DICTS[detected]
    else:
        lang_dict = _LANG_DICTS.get(language, {})

    results = []
    for bone in armature.data.bones:
        translation = lang_dict.get(bone.name)
        if translation:
            results.append((bone.name, translation))
        elif language == "AUTO" and (
            _contains_japanese(bone.name)
            or _contains_korean(bone.name)
            or _contains_cjk(bone.name)
        ):
            # Flag untranslated non-ASCII bones
            results.append((bone.name, f"[UNKNOWN] {bone.name}"))

    return results


# ─────────────────────────────────────────────────────────────────
# Scene property for language selection
# ─────────────────────────────────────────────────────────────────

_LANGUAGE_ITEMS = [
    ("AUTO",        "Auto-Detect",  "Auto-detect Japanese, Chinese, or Korean via Unicode"),
    ("JAPANESE",    "Japanese",     "MMD standard Japanese bone names (センター, 左腕, etc.)"),
    ("CHINESE",     "Chinese",      "Simplified Chinese MMD/VRChat bone names (左肩, 胸部, etc.)"),
    ("KOREAN",      "Korean",       "Korean VRChat community bone names (왼팔, 머리, etc.)"),
    ("PORTUGUESE",  "Portuguese",   "Brazilian/Portuguese Blender community (Braco.E, Joelho.D, etc.)"),
    ("SPANISH",     "Spanish",      "Spanish/Latin American Blender community (Brazo.Izq, Rodilla.Der, etc.)"),
    ("FRENCH",      "French",       "French Blender community (Bras.G, Genou.D, etc.)"),
]


# ─────────────────────────────────────────────────────────────────
# Operator
# ─────────────────────────────────────────────────────────────────

class BF_OT_VRC_TranslateBoneNames(Operator):
    """Translate foreign-language bone names to English"""

    bl_idname = "boneforge.vrc_translate_bone_names"
    bl_label = "Translate Bone Names"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        language = getattr(context.scene, "boneforge_translate_language", "AUTO")
        pairs = translate_bone_names(arm, language)

        if not pairs:
            lang_label = dict(_LANGUAGE_ITEMS).get(language, language)
            self.report({'INFO'}, f"No {lang_label} bone names found")
            return {'FINISHED'}

        renamed = 0
        for old_name, new_name in pairs:
            if new_name.startswith("[UNKNOWN]"):
                continue
            bone = arm.data.bones.get(old_name)
            if bone:
                bone.name = new_name
                renamed += 1

        lang_label = dict(_LANGUAGE_ITEMS).get(language, language)
        self.report({'INFO'}, f"Renamed {renamed} bones ({lang_label} → English)")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────
# Panel (Properties editor — full preview table)
# ─────────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_translate(Panel):
    """VRChat Bone Translation panel"""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_translate"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    def draw_header(self, context):
        self.layout.label(text=T("Translate Bone Names"))

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        if arm is None:
            layout.label(text=T("No active armature"), icon='INFO')
            return

        layout.prop(context.scene, "boneforge_translate_language", text=T("Language"))
        layout.separator()

        language = getattr(context.scene, "boneforge_translate_language", "AUTO")
        pairs = translate_bone_names(arm, language)

        if not pairs:
            layout.label(text=T("No matching bone names found"), icon='INFO')
            layout.operator("boneforge.vrc_translate_bone_names", icon='WORLD')
            return

        translatable = [(o, n) for o, n in pairs if not n.startswith("[UNKNOWN]")]
        unknown = [(o, n) for o, n in pairs if n.startswith("[UNKNOWN]")]

        layout.label(text=f"Found {len(translatable)} translatable, {len(unknown)} unknown:")
        layout.separator()

        for old_name, new_name in translatable:
            row = layout.row()
            row.label(text=old_name, icon='BONE_DATA')
            row.label(text=T("→"))
            row.label(text=new_name)

        if unknown:
            layout.separator()
            layout.label(text=T("Unknown (will be skipped):"), icon='ERROR')
            for old_name, _ in unknown:
                layout.label(text=f"  {old_name}", icon='QUESTION')

        layout.separator()
        layout.operator("boneforge.vrc_translate_bone_names", icon='WORLD')


# ─────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────

def register():
    bpy.utils.register_class(BF_OT_VRC_TranslateBoneNames)

    bpy.types.Scene.boneforge_translate_language = bpy.props.EnumProperty(
        name="Translate From",
        description="Source language for bone name translation",
        items=_LANGUAGE_ITEMS,
        default="AUTO",
    )


def unregister():
    if hasattr(bpy.types.Scene, "boneforge_translate_language"):
        del bpy.types.Scene.boneforge_translate_language

    bpy.utils.unregister_class(BF_OT_VRC_TranslateBoneNames)
