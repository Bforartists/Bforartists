
/* keep in sync with GlobalsUboStorage */
layout(std140) uniform globalsBlock
{
  vec4 colorWire;
  vec4 colorWireEdit;
  vec4 colorActive;
  vec4 colorSelect;
  vec4 colorDupliSelect;
  vec4 colorDupli;
  vec4 colorLibrarySelect;
  vec4 colorLibrary;
  vec4 colorTransform;
  vec4 colorLight;
  vec4 colorSpeaker;
  vec4 colorCamera;
  vec4 colorEmpty;
  vec4 colorVertex;
  vec4 colorVertexSelect;
  vec4 colorVertexUnreferenced;
  vec4 colorVertexMissingData;
  vec4 colorEditMeshActive;
  vec4 colorEdgeSelect;
  vec4 colorEdgeSeam;
  vec4 colorEdgeSharp;
  vec4 colorEdgeCrease;
  vec4 colorEdgeBWeight;
  vec4 colorEdgeFaceSelect;
  vec4 colorEdgeFreestyle;
  vec4 colorFace;
  vec4 colorFaceSelect;
  vec4 colorFaceFreestyle;
  vec4 colorNormal;
  vec4 colorVNormal;
  vec4 colorLNormal;
  vec4 colorFaceDot;
  vec4 colorSkinRoot;
  vec4 colorDeselect;
  vec4 colorOutline;
  vec4 colorLightNoAlpha;

  vec4 colorBackground;
  vec4 colorEditMeshMiddle;

  vec4 colorHandleFree;
  vec4 colorHandleAuto;
  vec4 colorHandleVect;
  vec4 colorHandleAlign;
  vec4 colorHandleAutoclamp;
  vec4 colorHandleSelFree;
  vec4 colorHandleSelAuto;
  vec4 colorHandleSelVect;
  vec4 colorHandleSelAlign;
  vec4 colorHandleSelAutoclamp;
  vec4 colorNurbUline;
  vec4 colorNurbVline;
  vec4 colorNurbSelUline;
  vec4 colorNurbSelVline;
  vec4 colorActiveSpline;

  vec4 colorBonePose;

  vec4 colorCurrentFrame;

  vec4 colorGrid;
  vec4 colorGridEmphasise;
  vec4 colorGridAxisX;
  vec4 colorGridAxisY;
  vec4 colorGridAxisZ;

  float sizeLightCenter;
  float sizeLightCircle;
  float sizeLightCircleShadow;
  float sizeVertex;
  float sizeEdge;
  float sizeEdgeFix;
  float sizeFaceDot;

  float pad_globalsBlock;
};

/* data[0] (1st byte flags) */
#define FACE_ACTIVE (1 << 0)
#define FACE_SELECTED (1 << 1)
#define FACE_FREESTYLE (1 << 2)
#define VERT_UV_SELECT (1 << 3)
#define VERT_UV_PINNED (1 << 4)
#define EDGE_UV_SELECT (1 << 5)
#define FACE_UV_ACTIVE (1 << 6)
#define FACE_UV_SELECT (1 << 7)
/* data[1] (2st byte flags) */
#define VERT_ACTIVE (1 << 0)
#define VERT_SELECTED (1 << 1)
#define EDGE_ACTIVE (1 << 2)
#define EDGE_SELECTED (1 << 3)
#define EDGE_SEAM (1 << 4)
#define EDGE_SHARP (1 << 5)
#define EDGE_FREESTYLE (1 << 6)
