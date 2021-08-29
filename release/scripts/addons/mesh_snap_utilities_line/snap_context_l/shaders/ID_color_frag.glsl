uniform int offset;
out uint FragColor;

void main()
{
	FragColor = uint(gl_PrimitiveID + offset);
}
