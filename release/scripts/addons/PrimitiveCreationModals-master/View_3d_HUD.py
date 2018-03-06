import bpy
import bgl
import blf

#Add the polygon draw to bgl
def draw_poly(points):
  for i in range(len(points)):
        bgl.glVertex2f(points[i][0],points[i][1])

def draw_callback_px(self, context):
    #init Vars
    seg = self.seg
    
    rh = bpy.context.region.height - 20
    rw = bpy.context.region.width
    
    bgR = 1
    bgG = 1 #0.597
    bgB = 1 #0.133
    bgA = 0.9
    user_preferences = context.user_preferences
    addon_prefs = user_preferences.addons[__package__].preferences   
    
    if addon_prefs.HUD_Center:
        x_loc = rw/2 
    else:
        x_loc = 95
    y_loc = rh - 5
    s = 4
    panel1_points = [[x_loc, y_loc - 1*s],
                   [x_loc + 2*s, y_loc], 
                   [x_loc + 4*s, y_loc - 1*s],  
                   [x_loc + 2*s, y_loc - 2*s], 
                   ]
                   
    panel2_points = [[x_loc, y_loc - 1*s],  
                   [x_loc + 2*s, y_loc - 2*s], 
                   [x_loc + 2*s, y_loc - 5*s],  
                   [x_loc, y_loc - 4*s], 
                   ]
    
    panel3_points = [[x_loc + 2*s, y_loc - 2*s], 
                   [x_loc + 2*s, y_loc - 5*s],  
                   [x_loc + 4*s, y_loc - 4*s],
                   [x_loc + 4*s, y_loc - 1*s], 
                   ]

    font_id = 0  

    #Set font color
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1, 1, 1, .9)
    bgl.glLineWidth(2)

    #Draw segments text
    blf.position(font_id, x_loc + 25, rh - 10, 0)
    blf.size(font_id, 10, 72)
    blf.draw(font_id, str(seg[0]))
    
    blf.position(font_id, x_loc + 25, rh - 20, 0)
    blf.size(font_id, 10, 72)
    blf.draw(font_id, str(seg[1]))
    
    blf.position(font_id, x_loc + 25, rh - 30, 0)
    blf.size(font_id, 10, 72)
    blf.draw(font_id, str(seg[2]))
    bgl.glEnd()

    #Draw outline for drop shadow/outline
    bgl.glColor4f(bgR* 0.2, bgG* 0.2, bgB* 0.2, bgA)
    bgl.glLineWidth(3)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    draw_poly(panel2_points)
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_LOOP)
    draw_poly(panel1_points)
    bgl.glEnd()
    bgl.glLineWidth(2)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    draw_poly(panel3_points)
    bgl.glEnd()

    #Top
    bgl.glColor4f(bgR, bgG, bgB, bgA)    
    bgl.glBegin(bgl.GL_POLYGON)
    draw_poly(panel1_points)
    bgl.glEnd()
    
    #Left
    bgl.glColor4f(bgR - 0.1, bgG - 0.1, bgB - 0.1, bgA)    
    bgl.glBegin(bgl.GL_POLYGON)
    draw_poly(panel2_points)
    bgl.glEnd()
    
    #Right
    bgl.glColor4f(bgR - 0.3, bgG - 0.3, bgB - 0.3, bgA)    
    bgl.glBegin(bgl.GL_POLYGON)
    draw_poly(panel3_points)
    bgl.glEnd()
    
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

