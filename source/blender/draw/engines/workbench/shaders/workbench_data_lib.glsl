struct LightData {
	vec4 light_direction_vs;
	vec4 specular_color;
};

struct WorldData {
	vec4 diffuse_light_x_pos;
	vec4 diffuse_light_x_neg;
	vec4 diffuse_light_y_pos;
	vec4 diffuse_light_y_neg;
	vec4 diffuse_light_z_pos;
	vec4 diffuse_light_z_neg;
	vec4 background_color_low;
	vec4 background_color_high;
	vec4 object_outline_color;
	vec4 light_direction_vs;
	LightData lights[3];
	int num_lights;
	int matcap_orientation;
	float background_alpha;
	int pad[1];
};

struct MaterialData {
	vec4 diffuse_color;
	vec4 specular_color;
	float roughness;
};
