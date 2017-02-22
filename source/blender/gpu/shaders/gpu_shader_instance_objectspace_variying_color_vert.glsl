
uniform mat4 ViewMatrix;
uniform mat4 ViewProjectionMatrix;
uniform mat4 ModelMatrix;

/* ---- Instanciated Attribs ---- */
in vec3 pos;
in vec3 nor;

/* ---- Per instance Attribs ---- */
in mat4 InstanceModelMatrix;
in vec4 color;

out vec3 normal;
flat out vec4 finalColor;

void main()
{
	mat4 FinalModelMatrix = ModelMatrix * InstanceModelMatrix;
	mat4 ModelViewProjectionMatrix = ViewProjectionMatrix * FinalModelMatrix;
	/* This is slow and run per vertex, but it's still faster than
	 * doing it per instance on CPU and sending it on via instance attrib */
	mat3 NormalMatrix = transpose(inverse(mat3(ViewMatrix * FinalModelMatrix)));

	gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
	normal = NormalMatrix * nor;

	finalColor = color;
}
