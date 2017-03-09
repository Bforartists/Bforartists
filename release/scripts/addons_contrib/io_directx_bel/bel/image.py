import bpy
import bpy.path

from . import __init__ as bel
from . import fs

debuglevel = 0

def dprint(str,l=2) :
    if l <= debuglevel :
        print(str)

# create or retrieve a bdata image
# given its path 
def new(path, name=False, relative = True) :
    path = fs.clean(path)
    # check file
    if fs.isfile(path) == False :
        dprint('Texture image not found')
        return False

    if relative :
        try :
            path = bpy.path.relpath(path)
            path = fs.clean(path)
        except : 
            print('cant turn path into relative one (.blend and img path drive letters ?) ')
        
    # retrieve paths to image file from existing image slot
    # returns img if paths match
    for img in bpy.data.images :
        if img.filepath != '' :
            if bpy.path.abspath(path) == bpy.path.abspath(fs.clean(img.filepath)) :
                return img

    # create a unique name in image slot
    if name == False : 
        name = bpy.path.basename(path)
    name = bel.bpyname(name,bpy.data.images.keys())

    # finally :
    img = bpy.data.images.load(filepath=path)
    img.name = name
    return img


def applyShader(mat,config) :

    # matslot.link = 'DATA'
    #mat = bpy.data.materials['Female_Body']

    texslot = mat.texture_slots[0]
    tex = texslot.texture
    img = tex.image
    
    #config = shaders[shadername]
    alpha = True if 'alpha' in config else False

    ## MAT

    mat.type = 'SURFACE'
    # diffuse
    mat.diffuse_color = Color((0.6, 0.6, 0.6))
    mat.diffuse_intensity = 0.8
    mat.diffuse_shader = 'LAMBERT'
    mat.use_diffuse_ramp = False

    # specular
    mat.specular_color = Color((1.0, 1.0, 1.0))
    mat.specular_intensity = 0.25
    mat.specular_shader = 'COOKTORR'
    mat.use_specular_ramp = False
    mat.specular_hardness = 1.0

    # shading
    mat.emit = 0.0
    mat.ambient = 0.5
    mat.translucency = 0.0
    mat.use_shadeless = False
    mat.use_tangent_shading = False
    mat.use_cubic = False

    # transparency
    mat.use_transparency = alpha
    mat.transparency_method = 'Z_TRANSPARENCY'
    mat.alpha = not(alpha)
    mat.specular_alpha = not(alpha)
    mat.raytrace_transparency.fresnel = 0.0
    mat.raytrace_transparency.fresnel_factor = 1.25

    # mirror
    mat.raytrace_mirror.use = False

    # subsurface_scattering
    mat.subsurface_scattering.use

    # strand
    # options
    # shadow
    mat.use_shadows = True
    mat.use_transparent_shadows = True
    mat.use_cast_shadows_only = False
    mat.shadow_cast_alpha = 1.0
    mat.use_only_shadow = False
    mat.shadow_only_type = 'SHADOW_ONLY_OLD'
    mat.use_cast_buffer_shadows = True
    mat.shadow_buffer_bias = 0.0
    mat.use_ray_shadow_bias = True
    mat.shadow_ray_bias = 0.0
    mat.use_cast_approximate = True

    # TEXTURE SLOT 0

    # diffuse
    texslot.diffuse_factor = 1.0
    texslot.use_map_diffuse = True
    texslot.diffuse_color_factor = 1.0
    texslot.use_map_color_diffuse = True
    texslot.alpha_factor = 1.0
    texslot.use_map_alpha = alpha
    texslot.translucency_factor = 0.0
    texslot.use_map_translucency = False

    # specular
    texslot.specular_factor = 0.3
    texslot.use_map_specular = True
    texslot.specular_color_factor = 1.0
    texslot.use_map_color_spec = True
    texslot.hardness_factor = 0.1
    texslot.use_map_hardness = True

    # shading
    texslot.ambient_factor = 0.0
    texslot.use_map_ambient = False
    texslot.emit_factor = 0.1
    texslot.use_map_emit = True
    texslot.mirror_factor = 0.0
    texslot.use_map_mirror = False
    texslot.raymir_factor = 0.0
    texslot.use_map_raymir = False

    # geometry
    texslot.normal_factor = 0.0
    texslot.use_map_normal = False
    texslot.warp_factor = 0.1
    texslot.use_map_warp = False
    texslot.displacement_factor = 0.0
    texslot.use_map_displacement = False

    texslot.blend_type = 'MIX'
    texslot.invert = False
    texslot.use_rgb_to_intensity = False
    texslot.color = Color((1.0, 0.0, 1.0)) # default
    texslot.use_stencil = False
    texslot.default_value = 1.0

    # TEXTURE
    tex.use_alpha = alpha
    tex.use_preview_alpha = alpha

def BSshader(nodes,pointer) :
    tkm = bpy.context.scene.tkm
    typ, nodename = pointer.split(' ')
    RenderShader = nodes[typ][nodename]
    name = BSname(nodename,RenderShader['Object.Name'])
    if name in bpy.data.materials :
        mat = bpy.data.materials[name]
    else :
        mat = bpy.data.materials.new(name=name)
        # Unused
        DepthWriteEnable = RenderShader['DepthWriteEnable'] if 'DepthWriteEnable' in RenderShader else False # an integer
        ShaderTransparency = RenderShader['MultiDrawLayer'] if 'MultiDrawLayer' in RenderShader else False # an integer
        LightEnable = RenderShader['LightEnable'] if 'LightEnable' in RenderShader else False # an integer

        ShaderPhong = BSnode(nodes,RenderShader['Surface'])
        #print('mat : %s'%ShaderPhong['Material'])
        RenderMaterial = BSnode(nodes,ShaderPhong['Material'])
        DiffuseColor = RenderMaterial['DiffuseColor'] if 'DiffuseColor' in RenderMaterial else False
        SpecularColor = RenderMaterial['SpecularColor'] if 'SpecularColor' in RenderMaterial else False
        AmbientColor = RenderMaterial['AmbientColor'] if 'AmbientColor' in RenderMaterial else False
        EmissionColor = RenderMaterial['Shininess'] if 'EmissionColor' in RenderMaterial else False
        Shininess = RenderMaterial['Shininess'] if 'Shininess' in RenderMaterial else False
        Transparency = RenderMaterial['Transparency'] if 'Transparency' in RenderMaterial else False
        for key in RenderMaterial.keys() :
            if key not in ['DiffuseColor','SpecularColor','AmbientColor','EmissionColor','Shininess','Transparency'] :
                print('NEW RENDERMATERIAL PROP ! : %s'%key)
        
        #print(AmbientColor)
        if DiffuseColor : mat.diffuse_color = Color(DiffuseColor) #[0][0],DiffuseColor[0][1],DiffuseColor[0][2])
        if SpecularColor : mat.specular_color = Color(SpecularColor)#[0][0],SpecularColor[0][1],SpecularColor[0][2])
        if AmbientColor : mat.ambient = AmbientColor[0] # source value is a vector3f with x=y=z 
        if EmissionColor : mat.emit = EmissionColor[0] # source value is a vector3f with x=y=z 
        #if Shininess : mat.
        #alpha is a boolean, whereas Transparency is a float or False
        if Transparency :
            mat.use_transparency = True
            mat.transparency_method = 'Z_TRANSPARENCY'
            mat.alpha = Transparency
            mat.specular_alpha = 0
            alpha = True
        else : alpha = False
        texinfluence = False
        if 'Color' in ShaderPhong :
            ShaderTexture = BSnode(nodes,ShaderPhong['Color'])
            texinfluence = 'Color'
        if 'Reflection' in ShaderPhong :
            ShaderTexture = BSnode(nodes,ShaderPhong['Reflection'])
            texinfluence = 'Reflection'
        if texinfluence == False :
            print('neither color nor refl. in ShaderPhong %s'%RenderShader['Surface'])
            print('other props are : %s'%ShaderPhong.keys())
            return mat

        ShaderTextureName = ShaderTexture['Object.Name']

        Texture2D = BSnode(nodes,ShaderTexture['Texture'])
        Texture2DName = Texture2D['Object.Name']

        FileObject = BSnode(nodes,Texture2D['Texture.FileObject'])
        imgpath = FileObject['FileName']
        imgname = imgpath.split('/')[-1]
        imgpath = tkm.path_archives+'/Images/Q=Tex032M/'+imgpath

        if imgname not in bpy.data.images :        
            if os.path.isfile(imgpath+'.png') : ext = '.png'
            elif os.path.isfile(imgpath+'.jp2') : ext = '.jp2'
            else :
                print('Texture image not found ! %s'%Texture2D['Texture.FileObject'])
                print('path : %s.png or .jp2 '%imgpath)
                return mat
            img = bpy.data.images.load(filepath=imgpath+ext)
            img.name = imgname
        else : img = bpy.data.images[imgname]
        
        '''
        texslot = mat.texture_slots[0]
        mat.texture_slots[0]
        tex = texslot.texture
        tex.type = 'IMAGE'
        img = tex.image        
        img.name
        '''
        #img = bpy.data.images.new(name='imgname',width=640, height=512)

        if ShaderTextureName not in bpy.data.textures :
            tex = bpy.data.textures.new(name=ShaderTextureName,type='IMAGE')
            tex.image = img
            tex.use_alpha = alpha
            tex.use_preview_alpha = alpha
        else : tex = bpy.data.textures[ShaderTextureName]

        texslot = mat.texture_slots.create(index=0)
        texslot.texture = tex
        texslot.texture_coords = 'UV'
        texslot.uv_layer = 'UV0'
        texslot.use_map_alpha = alpha
        texslot.alpha_factor = 1.0

    return mat