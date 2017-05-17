
uniform mat4 ModelViewProjectionMatrix;

out vec4 v_position;

void main()
{
	gl_Position = ModelViewProjectionMatrix * gl_Vertex;
	v_position = gl_Position;
}
