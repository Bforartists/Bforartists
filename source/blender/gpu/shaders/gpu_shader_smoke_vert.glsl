
uniform mat4 ModelViewProjectionMatrix;

#if __VERSION__ == 120
  varying vec3 coords;
#else
  out vec3 coords;
#endif

uniform vec3 min_location;
uniform vec3 invsize;
uniform vec3 ob_sizei;

void main()
{
	gl_Position = ModelViewProjectionMatrix * vec4(gl_Vertex.xyz * ob_sizei, 1.0);
	coords = (gl_Vertex.xyz - min_location) * invsize;
}
