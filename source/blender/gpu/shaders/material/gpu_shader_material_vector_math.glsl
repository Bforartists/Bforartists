void vector_math_add(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = a + b;
}

void vector_math_subtract(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = a - b;
}

void vector_math_multiply(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = a * b;
}

void vector_math_divide(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = safe_divide(a, b);
}

void vector_math_cross(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = cross(a, b);
}

void vector_math_project(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  float lenSquared = dot(b, b);
  outVector = (lenSquared != 0.0) ? (dot(a, b) / lenSquared) * b : vec3(0.0);
}

void vector_math_reflect(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = reflect(a, normalize(b));
}

void vector_math_dot(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outValue = dot(a, b);
}

void vector_math_distance(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outValue = distance(a, b);
}

void vector_math_length(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outValue = length(a);
}

void vector_math_scale(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = a * scale;
}

void vector_math_normalize(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = normalize(a);
}

void vector_math_snap(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = floor(safe_divide(a, b)) * b;
}

void vector_math_floor(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = floor(a);
}

void vector_math_ceil(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = ceil(a);
}

void vector_math_modulo(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = c_mod(a, b);
}

void vector_math_fraction(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = fract(a);
}

void vector_math_absolute(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = abs(a);
}

void vector_math_minimum(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = min(a, b);
}

void vector_math_maximum(vec3 a, vec3 b, float scale, out vec3 outVector, out float outValue)
{
  outVector = max(a, b);
}
