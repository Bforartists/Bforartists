
uniform mat4 gpModelMatrix;

in vec3 pos;
in vec4 color;
in vec2 texCoord;

out vec4 finalColor;
out vec2 texCoord_interp;

void main(void)
{
  gl_Position = point_world_to_ndc((gpModelMatrix * vec4(pos, 1.0)).xyz);
  finalColor = color;
  texCoord_interp = texCoord;
}
