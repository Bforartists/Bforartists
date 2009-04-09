/* $Id$
-----------------------------------------------------------------------------

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place - Suite 330, Boston, MA 02111-1307, USA, or go to
http://www.gnu.org/copyleft/lesser.txt.

Contributor(s): Dalai Felinto

This code is originally inspired on some of the ideas and codes from Paul Bourke.
Developed as part of a Research and Development project for SAT - La Soci�t� des arts technologiques.
-----------------------------------------------------------------------------
*/

#include "KX_Dome.h"

#include <structmember.h>
#include <float.h>
#include <math.h>

#include "DNA_scene_types.h"
#include "RAS_CameraData.h"
#include "BLI_arithb.h"

#include "GL/glew.h"

// constructor
KX_Dome::KX_Dome (
	RAS_ICanvas* canvas,
    /// rasterizer
    RAS_IRasterizer* rasterizer,
    /// render tools
    RAS_IRenderTools* rendertools,
    /// engine
    KX_KetsjiEngine* engine,
	
	float size,		//size for adjustments
	short res,		//resolution of the mesh
	short mode,		//mode - fisheye, truncated, warped, panoramic, ...
	short angle,
	float resbuf,	//size adjustment of the buffer
	struct Text* warptext

):
	m_canvas(canvas),
	m_rasterizer(rasterizer),
	m_rendertools(rendertools),
	m_engine(engine),
	m_drawingmode(engine->GetDrawType()),
	m_size(size),
	m_resolution(res),
	m_mode(mode),
	m_angle(angle),
	m_resbuffer(resbuf),
	canvaswidth(-1), canvasheight(-1),
	dlistSupported(false)
{
	warp.usemesh = false;

	if (mode >= DOME_NUM_MODES)
		m_mode = DOME_FISHEYE;

	if (warptext) // it there is a text data try to warp it
	{
		char *buf;
		buf = txt_to_buf(warptext);
		if (buf)
		{
			warp.usemesh = ParseWarpMesh(STR_String(buf));
			MEM_freeN(buf);
		}
	}

	//setting the viewport size
	GLuint	viewport[4]={0};
	glGetIntegerv(GL_VIEWPORT,(GLint *)viewport);

	SetViewPort(viewport);

	switch(m_mode){
		case DOME_FISHEYE:
			if (m_angle <= 180){
				cubetop.resize(1);
				cubebottom.resize(1);
				cubeleft.resize(2);
				cuberight.resize(2);

				CreateMeshDome180();
				m_numfaces = 4;
			}else if (m_angle > 180){
				cubetop.resize(2);
				cubebottom.resize(2);
				cubeleft.resize(2);
				cubefront.resize(2);
				cuberight.resize(2);

				CreateMeshDome250();
				m_numfaces = 5;
			} break;
		case DOME_TRUNCATED:
			cubetop.resize(1);
			cubebottom.resize(1);
			cubeleft.resize(2);
			cuberight.resize(2);

			m_angle = 180;
			CreateMeshDome180();
			m_numfaces = 4;
			break;
		case DOME_PANORAM_SPH:
			cubeleft.resize(2);
			cubeleftback.resize(2);
			cuberight.resize(2);
			cuberightback.resize(2);
			cubetop.resize(2);
			cubebottom.resize(2);

			m_angle = 360;
			CreateMeshPanorama();
			m_numfaces = 6;
			break;
	}

	m_numimages =(warp.usemesh?m_numfaces+1:m_numfaces);

	CalculateCameraOrientation();

	CreateGLImages();

	dlistSupported = CreateDL();
}

// destructor
KX_Dome::~KX_Dome (void)
{
	GLuint m_numimages = m_numfaces;

	ClearGLImages();

	if(dlistSupported)
		glDeleteLists(dlistId, (GLsizei) m_numimages);
}

void KX_Dome::SetViewPort(GLuint viewport[4])
{
	if(canvaswidth != m_canvas->GetWidth() || canvasheight != m_canvas->GetHeight())
	{
		m_viewport.SetLeft(viewport[0]); 
		m_viewport.SetBottom(viewport[1]);
		m_viewport.SetRight(viewport[2]);
		m_viewport.SetTop(viewport[3]);

		CalculateImageSize();
	}
}

void KX_Dome::CreateGLImages(void)
{
	glGenTextures(m_numimages, (GLuint*)&domefacesId);

	for (int j=0;j<m_numfaces;j++){
		glBindTexture(GL_TEXTURE_2D, domefacesId[j]);
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, m_imagesize, m_imagesize, 0, GL_RGB8,
				GL_UNSIGNED_BYTE, 0);
		glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 0, 0, m_imagesize, m_imagesize, 0);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
	}
	if(warp.usemesh){
		glBindTexture(GL_TEXTURE_2D, domefacesId[m_numfaces]);
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, warp.imagewidth, warp.imageheight, 0, GL_RGB8,
				GL_UNSIGNED_BYTE, 0);
		glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 0, 0, warp.imagewidth, warp.imageheight, 0);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
	}
}

void KX_Dome::ClearGLImages(void)
{
	glDeleteTextures(m_numimages, (GLuint*)&domefacesId);
/*
	for (int i=0;i<m_numimages;i++)
		if(glIsTexture(domefacesId[i]))
			glDeleteTextures(1, (GLuint*)&domefacesId[i]);
*/
}

void KX_Dome::CalculateImageSize(void)
{
/*
- determine the minimum buffer size
- reduce the buffer for better performace
- create a power of 2 texture bigger than the buffer
*/

	canvaswidth = m_canvas->GetWidth();
	canvasheight = m_canvas->GetHeight();

	m_buffersize = (canvaswidth > canvasheight?canvasheight:canvaswidth);
	m_buffersize *= m_resbuffer; //reduce buffer size for better performance

	int i = 0;
	while ((1 << i) <= m_buffersize)
		i++;
	m_imagesize = (1 << i);

	if (warp.usemesh){
		warp.bufferwidth = canvaswidth;
		warp.bufferheight = canvasheight;

		i = 0;
		while ((1 << i) <= warp.bufferwidth)
			i++;
		warp.imagewidth = (1 << i);

		i = 0;
		while ((1 << i) <= warp.bufferheight)
			i++;
		warp.imageheight = (1 << i);
	}
}

bool KX_Dome::CreateDL(){
	int i,j;

	dlistId = glGenLists((GLsizei) m_numimages);
	if (dlistId != 0) {
		if(m_mode == DOME_FISHEYE || m_mode == DOME_TRUNCATED){
			glNewList(dlistId, GL_COMPILE);
				GLDrawTriangles(cubetop, nfacestop);
			glEndList();

			glNewList(dlistId+1, GL_COMPILE);
				GLDrawTriangles(cubebottom, nfacesbottom);
			glEndList();

			glNewList(dlistId+2, GL_COMPILE);
				GLDrawTriangles(cubeleft, nfacesleft);
			glEndList();

			glNewList(dlistId+3, GL_COMPILE);
				GLDrawTriangles(cuberight, nfacesright);
			glEndList();

			if (m_angle > 180){
				glNewList(dlistId+4, GL_COMPILE);
					GLDrawTriangles(cubefront, nfacesfront);
				glEndList();
			}
		}
		else if (m_mode == DOME_PANORAM_SPH)
		{
			glNewList(dlistId, GL_COMPILE);
				GLDrawTriangles(cubetop, nfacestop);
			glEndList();

			glNewList(dlistId+1, GL_COMPILE);
				GLDrawTriangles(cubebottom, nfacesbottom);
			glEndList();

			glNewList(dlistId+2, GL_COMPILE);
				GLDrawTriangles(cubeleft, nfacesleft);
			glEndList();

			glNewList(dlistId+3, GL_COMPILE);
				GLDrawTriangles(cuberight, nfacesright);
			glEndList();

			glNewList(dlistId+4, GL_COMPILE);
				GLDrawTriangles(cubeleftback, nfacesleftback);
			glEndList();

			glNewList(dlistId+5, GL_COMPILE);
				GLDrawTriangles(cuberightback, nfacesrightback);
			glEndList();
		}

		if(warp.usemesh){
			glNewList((dlistId + m_numfaces), GL_COMPILE);
				GLDrawWarpQuads();
			glEndList();
		}

		//clearing the vectors 
		cubetop.clear();
		cubebottom.clear();
		cuberight.clear();
		cubeleft.clear();
		cubefront.clear();
		cubeleftback.clear();
		cuberightback.clear();
		warp.nodes.clear();

	} else // genList failed
		return false;

	return true;
}

void KX_Dome::GLDrawTriangles(vector <DomeFace>& face, int nfaces)
{
	int i,j;
	glBegin(GL_TRIANGLES);
		for (i=0;i<nfaces;i++) {
			for (j=0;j<3;j++) {
				glTexCoord2f(face[i].u[j],face[i].v[j]);
				glVertex3f((GLfloat)face[i].verts[j][0],(GLfloat)face[i].verts[j][1],(GLfloat)face[i].verts[j][2]);
			}
		}
	glEnd();
}

void KX_Dome::GLDrawWarpQuads(void)
{
	int i, j, i2;
	float uv_width = (float)(warp.bufferwidth-1) / warp.imagewidth;
	float uv_height = (float)(warp.bufferheight-1) / warp.imageheight;

	if(warp.mode ==2 ){
		glBegin(GL_QUADS);
		for (i=0;i<warp.n_height-1;i++) {
			for (j=0;j<warp.n_width-1;j++) {
				if(warp.nodes[i][j].i < 0 || warp.nodes[i+1][j].i < 0 || warp.nodes[i+1][j+1].i < 0 || warp.nodes[i][j+1].i < 0)
					continue;

				glColor3f(warp.nodes[i][j].i, warp.nodes[i][j].i, warp.nodes[i][j].i);
				glTexCoord2f((warp.nodes[i][j].u * uv_width), (warp.nodes[i][j].v * uv_height));
				glVertex3f(warp.nodes[i][j].x, warp.nodes[i][j].y,0.0);

				glColor3f(warp.nodes[i+1][j].i, warp.nodes[i+1][j].i, warp.nodes[i+1][j].i);
				glTexCoord2f((warp.nodes[i+1][j].u * uv_width), (warp.nodes[i+1][j].v * uv_height));
				glVertex3f(warp.nodes[i+1][j].x, warp.nodes[i+1][j].y,0.0);

				glColor3f(warp.nodes[i+1][j+1].i, warp.nodes[i+1][j+1].i, warp.nodes[i+1][j+1].i);
				glTexCoord2f((warp.nodes[i+1][j+1].u * uv_width), (warp.nodes[i+1][j+1].v * uv_height));
				glVertex3f(warp.nodes[i+1][j+1].x, warp.nodes[i+1][j+1].y,0.0);

				glColor3f(warp.nodes[i][j+1].i, warp.nodes[i][j+1].i, warp.nodes[i][j+1].i);
				glTexCoord2f((warp.nodes[i][j+1].u * uv_width), (warp.nodes[i][j+1].v * uv_height));
				glVertex3f(warp.nodes[i][j+1].x, warp.nodes[i][j+1].y,0.0);
			}
		}
		glEnd();
	}
	else if (warp.mode == 1){
		glBegin(GL_QUADS);
		for (i=0;i<warp.n_height-1;i++) {
			for (j=0;j<warp.n_width-1;j++) {
				i2 = (i+1) % warp.n_width; // Wrap around, i = warp.n_width = 0

				if (warp.nodes[i][j].i < 0 || warp.nodes[i2][j].i < 0 || warp.nodes[i2][j+1].i < 0 || warp.nodes[i][j+1].i < 0)
					continue;

				 glColor3f(warp.nodes[i][j].i,warp.nodes[i][j].i,warp.nodes[i][j].i);
				 glTexCoord2f((warp.nodes[i][j].u * uv_width), (warp.nodes[i][j].v * uv_height));
				 glVertex3f(warp.nodes[i][j].x,warp.nodes[i][j].y,0.0);

				 glColor3f(warp.nodes[i2][j].i,warp.nodes[i2][j].i,warp.nodes[i2][j].i);
				 glTexCoord2f((warp.nodes[i2][j].u * uv_width), (warp.nodes[i2][j].v * uv_height));
				 glVertex3f(warp.nodes[i2][j].x,warp.nodes[i2][j].y,0.0);

				 glColor3f(warp.nodes[i2][j+1].i,warp.nodes[i2][j+1].i,warp.nodes[i2][j+1].i);
				 glTexCoord2f((warp.nodes[i2][j+1].u * uv_width), (warp.nodes[i2][j+1].v * uv_height));
				 glVertex3f(warp.nodes[i2][j+1].x,warp.nodes[i2][j+1].y,0.0);

				 glColor3f(warp.nodes[i2][j+1].i,warp.nodes[i2][j+1].i,warp.nodes[i2][j+1].i);
				 glTexCoord2f((warp.nodes[i2][j+1].u * uv_width), (warp.nodes[i2][j+1].v * uv_height));
				 glVertex3f(warp.nodes[i2][j+1].x,warp.nodes[i2][j+1].y,0.0);

			}
		}
		glEnd();
	} else{
		printf("Error: Warp Mode unsupported. Try 1 for Polar Mesh or 2 for Fisheye.\n");
	}
}


bool KX_Dome::ParseWarpMesh(STR_String text)
{
/*
//Notes about the supported data format:
File example::
	mode
	width height
	n0_x n0_y n0_u n0_v n0_i
	n1_x n1_y n1_u n1_v n1_i
	n2_x n1_y n2_u n2_v n2_i
	n3_x n3_y n3_u n3_v n3_i
	(...)
First line is the image type the mesh is support to be applied to: 2 = fisheye, 1=radial
Tthe next line has the mesh dimensions
Rest of the lines are the nodes of the mesh. Each line has x y u v i
  (x,y) are the normalised screen coordinates
  (u,v) texture coordinates
  i a multiplicative intensity factor

x varies from -screen aspect to screen aspect
y varies from -1 to 1
u and v vary from 0 to 1
i ranges from 0 to 1, if negative don't draw that mesh node
*/
	int i,j,k;
	int nodeX=0, nodeY=0;

	vector<STR_String> columns, lines;

	lines = text.Explode('\n');
	if(lines.size() < 6){
		printf("Error: Warp Mesh File with insufficient data!\n");
		return false;
	}
	columns = lines[1].Explode(' ');

	if(columns.size() !=2){
		printf("Error: Warp Mesh File incorrect. The second line should contain: width height.\n");
		return false;
	}

	warp.mode = atoi(lines[0]);// 1 = radial, 2 = fisheye

	warp.n_width = atoi(columns[0]);
	warp.n_height = atoi(columns[1]);

	if (lines.size() < 2 + (warp.n_width * warp.n_height)){
		printf("Error: Warp Mesh File with insufficient data!\n");
		return false;
	}else{
		warp.nodes = vector<vector<WarpMeshNode> > (warp.n_height, vector<WarpMeshNode>(warp.n_width));

		for(i=2; i-2 < (warp.n_width*warp.n_height); i++){
			columns = lines[i].Explode(' ');

			if (columns.size() == 5){
				nodeX = (i-2)%warp.n_width;
				nodeY = ((i-2) - nodeX) / warp.n_width;

				warp.nodes[nodeY][nodeX].x = atof(columns[0]);
				warp.nodes[nodeY][nodeX].y = atof(columns[1]);
				warp.nodes[nodeY][nodeX].u = atof(columns[2]);
				warp.nodes[nodeY][nodeX].v = atof(columns[3]);
				warp.nodes[nodeY][nodeX].i = atof(columns[4]);
			}
			else{
				warp.nodes.clear();
				printf("Error: Warp Mesh File with wrong number of fields. You should use 5: x y u v i.\n");
				return false;
			}
		}
	}
	return true;
}

void KX_Dome::CreateMeshDome180(void)
{
/*
1)-  Define the faces of half of a cube 
 - each face is made out of 2 triangles
2) Subdivide the faces
 - more resolution == more curved lines
3) Spherize the cube
 - normalize the verts
4) Flatten onto xz plane
 - transform it onto an equidistant spherical projection techniques to transform the sphere onto a dome image
*/
	int i,j;
	float sqrt_2 = sqrt(2.0);
	float uv_ratio = (float)(m_buffersize-1) / m_imagesize;

	m_radangle = m_angle * M_PI/180.0;//calculates the radians angle, used for flattening

	//creating faces for the env mapcube 180� Dome
	// Top Face - just a triangle
	cubetop[0].verts[0][0] = -sqrt_2 / 2.0;
	cubetop[0].verts[0][1] = 0.0;
	cubetop[0].verts[0][2] = 0.5;
	cubetop[0].u[0] = 0.0;
	cubetop[0].v[0] = uv_ratio;

	cubetop[0].verts[1][0] = 0.0;
	cubetop[0].verts[1][1] = sqrt_2 / 2.0;
	cubetop[0].verts[1][2] = 0.5;
	cubetop[0].u[1] = 0.0;
	cubetop[0].v[1] = 0.0;

	cubetop[0].verts[2][0] = sqrt_2 / 2.0;
	cubetop[0].verts[2][1] = 0.0;
	cubetop[0].verts[2][2] = 0.5;
	cubetop[0].u[2] = uv_ratio;
	cubetop[0].v[2] = 0.0;

	nfacestop = 1;

	/* Bottom face - just a triangle */
	cubebottom[0].verts[0][0] = -sqrt_2 / 2.0;
	cubebottom[0].verts[0][1] = 0.0;
	cubebottom[0].verts[0][2] = -0.5;
	cubebottom[0].u[0] = uv_ratio;
	cubebottom[0].v[0] = 0.0;

	cubebottom[0].verts[1][0] = sqrt_2 / 2.0;
	cubebottom[0].verts[1][1] = 0;
	cubebottom[0].verts[1][2] = -0.5;
	cubebottom[0].u[1] = 0.0;
	cubebottom[0].v[1] = uv_ratio;

	cubebottom[0].verts[2][0] = 0.0;
	cubebottom[0].verts[2][1] = sqrt_2 / 2.0;
	cubebottom[0].verts[2][2] = -0.5;
	cubebottom[0].u[2] = 0.0;
	cubebottom[0].v[2] = 0.0;

	nfacesbottom = 1;	
	
	/* Left face - two triangles */
	
	cubeleft[0].verts[0][0] = -sqrt_2 / 2.0;
	cubeleft[0].verts[0][1] = .0;
	cubeleft[0].verts[0][2] = -0.5;
	cubeleft[0].u[0] = 0.0;
	cubeleft[0].v[0] = 0.0;

	cubeleft[0].verts[1][0] = 0.0;
	cubeleft[0].verts[1][1] = sqrt_2 / 2.0;
	cubeleft[0].verts[1][2] = -0.5;
	cubeleft[0].u[1] = uv_ratio;
	cubeleft[0].v[1] = 0.0;

	cubeleft[0].verts[2][0] = -sqrt_2 / 2.0;
	cubeleft[0].verts[2][1] = 0.0;
	cubeleft[0].verts[2][2] = 0.5;
	cubeleft[0].u[2] = 0.0;
	cubeleft[0].v[2] = uv_ratio;

	//second triangle
	cubeleft[1].verts[0][0] = -sqrt_2 / 2.0;
	cubeleft[1].verts[0][1] = 0.0;
	cubeleft[1].verts[0][2] = 0.5;
	cubeleft[1].u[0] = 0.0;
	cubeleft[1].v[0] = uv_ratio;

	cubeleft[1].verts[1][0] = 0.0;
	cubeleft[1].verts[1][1] = sqrt_2 / 2.0;
	cubeleft[1].verts[1][2] = -0.5;
	cubeleft[1].u[1] = uv_ratio;
	cubeleft[1].v[1] = 0.0;

	cubeleft[1].verts[2][0] = 0.0;
	cubeleft[1].verts[2][1] = sqrt_2 / 2.0;
	cubeleft[1].verts[2][2] = 0.5;
	cubeleft[1].u[2] = uv_ratio;
	cubeleft[1].v[2] = uv_ratio;

	nfacesleft = 2;
	
	/* Right face - two triangles */
	cuberight[0].verts[0][0] = 0.0;
	cuberight[0].verts[0][1] = sqrt_2 / 2.0;
	cuberight[0].verts[0][2] = -0.5;
	cuberight[0].u[0] = 0.0;
	cuberight[0].v[0] = 0.0;

	cuberight[0].verts[1][0] = sqrt_2 / 2.0;
	cuberight[0].verts[1][1] = 0.0;
	cuberight[0].verts[1][2] = -0.5;
	cuberight[0].u[1] = uv_ratio;
	cuberight[0].v[1] = 0.0;

	cuberight[0].verts[2][0] = sqrt_2 / 2.0;
	cuberight[0].verts[2][1] = 0.0;
	cuberight[0].verts[2][2] = 0.5;
	cuberight[0].u[2] = uv_ratio;
	cuberight[0].v[2] = uv_ratio;

	//second triangle
	cuberight[1].verts[0][0] = 0.0;
	cuberight[1].verts[0][1] = sqrt_2 / 2.0;
	cuberight[1].verts[0][2] = -0.5;
	cuberight[1].u[0] = 0.0;
	cuberight[1].v[0] = 0.0;

	cuberight[1].verts[1][0] = sqrt_2 / 2.0;
	cuberight[1].verts[1][1] = 0.0;
	cuberight[1].verts[1][2] = 0.5;
	cuberight[1].u[1] = uv_ratio;
	cuberight[1].v[1] = uv_ratio;

	cuberight[1].verts[2][0] = 0.0;
	cuberight[1].verts[2][1] = sqrt_2 / 2.0;
	cuberight[1].verts[2][2] = 0.5;
	cuberight[1].u[2] = 0.0;
	cuberight[1].v[2] = uv_ratio;

	nfacesright = 2;
	
	//Refine a triangular mesh by bisecting each edge forms 3 new triangles for each existing triangle on each iteration
	//Could be made more efficient for drawing if the triangles were ordered in a fan. Not that important since we are using DisplayLists

	for(i=0;i<m_resolution;i++){
		cubetop.resize(4*nfacestop);
		SplitFace(cubetop,&nfacestop);
		cubebottom.resize(4*nfacesbottom);
		SplitFace(cubebottom,&nfacesbottom);	
		cubeleft.resize(4*nfacesleft);
		SplitFace(cubeleft,&nfacesleft);
		cuberight.resize(4*nfacesright);
		SplitFace(cuberight,&nfacesright);
	}		

	// Turn into a hemisphere
	for(j=0;j<3;j++){
		for(i=0;i<nfacestop;i++)
			cubetop[i].verts[j].normalize();
		for(i=0;i<nfacesbottom;i++)
			cubebottom[i].verts[j].normalize();
		for(i=0;i<nfacesleft;i++)
			cubeleft[i].verts[j].normalize();
		for(i=0;i<nfacesright;i++)
			cuberight[i].verts[j].normalize();
	}

	//flatten onto xz plane
	for(i=0;i<nfacestop;i++)
		FlattenDome(cubetop[i].verts);
	for(i=0;i<nfacesbottom;i++)
		FlattenDome(cubebottom[i].verts);
	for(i=0;i<nfacesleft;i++)
		FlattenDome(cubeleft[i].verts);
	for(i=0;i<nfacesright;i++)
		FlattenDome(cuberight[i].verts);

}

void KX_Dome::CreateMeshDome250(void)
{
/*
1)-  Define the faces of a cube without the back face
 - each face is made out of 2 triangles
2) Subdivide the faces
 - more resolution == more curved lines
3) Spherize the cube
 - normalize the verts
4) Flatten onto xz plane
 - transform it onto an equidistant spherical projection techniques to transform the sphere onto a dome image
*/

	int i,j;
	float uv_height, uv_base;
	float verts_height;

	float rad_ang = m_angle * MT_PI / 180.0;
	float uv_ratio = (float)(m_buffersize-1) / m_imagesize;

	m_radangle = m_angle * M_PI/180.0;//calculates the radians angle, used for flattening
/*
verts_height is the exactly needed height of the cube faces (not always 1.0).
When we want some horizontal information (e.g. for horizontal 220� domes) we don't need to create and tesselate the whole cube.
Therefore the lateral cube faces could be small, and the tesselate mesh would be completely used.
(if we always worked with verts_height = 1.0, we would be discarding a lot of the calculated and tesselated geometry).

So I came out with this formula:
verts_height = tan((rad_ang/2) - (MT_PI/2))*sqrt(2.0);

Here we take half the sphere(rad_ang/2) and subtract a quarter of it (MT_PI/2)
Therefore we have the lenght in radians of the dome/sphere over the horizon.
Once we take the tangent of that angle, you have the verts coordinate corresponding to the verts on the side faces.
Then we need to multiply it by sqrt(2.0) to get the coordinate of the verts on the diagonal of the original cube.
*/
	verts_height = tan((rad_ang/2) - (MT_PI/2))*sqrt(2.0);

	uv_height = uv_ratio * ((verts_height/2) + 0.5);
	uv_base = uv_ratio * (1.0 - ((verts_height/2) + 0.5));
	
	//creating faces for the env mapcube 180� Dome
	// Front Face - 2 triangles
	cubefront[0].verts[0][0] =-1.0;
	cubefront[0].verts[0][1] = 1.0;
	cubefront[0].verts[0][2] =-1.0;
	cubefront[0].u[0] = 0.0;
	cubefront[0].v[0] = 0.0;

	cubefront[0].verts[1][0] = 1.0;
	cubefront[0].verts[1][1] = 1.0;
	cubefront[0].verts[1][2] = 1.0;	
	cubefront[0].u[1] = uv_ratio;
	cubefront[0].v[1] = uv_ratio;

	cubefront[0].verts[2][0] =-1.0;
	cubefront[0].verts[2][1] = 1.0;
	cubefront[0].verts[2][2] = 1.0;	
	cubefront[0].u[2] = 0.0;
	cubefront[0].v[2] = uv_ratio;

	//second triangle
	cubefront[1].verts[0][0] = 1.0;
	cubefront[1].verts[0][1] = 1.0;
	cubefront[1].verts[0][2] = 1.0;
	cubefront[1].u[0] = uv_ratio;
	cubefront[1].v[0] = uv_ratio;

	cubefront[1].verts[1][0] =-1.0;
	cubefront[1].verts[1][1] = 1.0;
	cubefront[1].verts[1][2] =-1.0;	
	cubefront[1].u[1] = 0.0;
	cubefront[1].v[1] = 0.0;

	cubefront[1].verts[2][0] = 1.0;
	cubefront[1].verts[2][1] = 1.0;
	cubefront[1].verts[2][2] =-1.0;	
	cubefront[1].u[2] = uv_ratio;
	cubefront[1].v[2] = 0.0;

	nfacesfront = 2;

	// Left Face - 2 triangles
	cubeleft[0].verts[0][0] =-1.0;
	cubeleft[0].verts[0][1] = 1.0;
	cubeleft[0].verts[0][2] =-1.0;
	cubeleft[0].u[0] = uv_ratio;
	cubeleft[0].v[0] = 0.0;

	cubeleft[0].verts[1][0] =-1.0;
	cubeleft[0].verts[1][1] =-verts_height;
	cubeleft[0].verts[1][2] = 1.0;	
	cubeleft[0].u[1] = uv_base;
	cubeleft[0].v[1] = uv_ratio;

	cubeleft[0].verts[2][0] =-1.0;
	cubeleft[0].verts[2][1] =-verts_height;
	cubeleft[0].verts[2][2] =-1.0;	
	cubeleft[0].u[2] = uv_base;
	cubeleft[0].v[2] = 0.0;

	//second triangle
	cubeleft[1].verts[0][0] =-1.0;
	cubeleft[1].verts[0][1] =-verts_height;
	cubeleft[1].verts[0][2] = 1.0;
	cubeleft[1].u[0] = uv_base;
	cubeleft[1].v[0] = uv_ratio;

	cubeleft[1].verts[1][0] =-1.0;
	cubeleft[1].verts[1][1] = 1.0;
	cubeleft[1].verts[1][2] =-1.0;	
	cubeleft[1].u[1] = uv_ratio;
	cubeleft[1].v[1] = 0.0;

	cubeleft[1].verts[2][0] =-1.0;
	cubeleft[1].verts[2][1] = 1.0;
	cubeleft[1].verts[2][2] = 1.0;	
	cubeleft[1].u[2] = uv_ratio;
	cubeleft[1].v[2] = uv_ratio;

	nfacesleft = 2;

	// right Face - 2 triangles
	cuberight[0].verts[0][0] = 1.0;
	cuberight[0].verts[0][1] = 1.0;
	cuberight[0].verts[0][2] = 1.0;
	cuberight[0].u[0] = 0.0;
	cuberight[0].v[0] = uv_ratio;

	cuberight[0].verts[1][0] = 1.0;
	cuberight[0].verts[1][1] =-verts_height;
	cuberight[0].verts[1][2] =-1.0;	
	cuberight[0].u[1] = uv_height;
	cuberight[0].v[1] = 0.0;

	cuberight[0].verts[2][0] = 1.0;
	cuberight[0].verts[2][1] =-verts_height;
	cuberight[0].verts[2][2] = 1.0;	
	cuberight[0].u[2] = uv_height;
	cuberight[0].v[2] = uv_ratio;

	//second triangle
	cuberight[1].verts[0][0] = 1.0;
	cuberight[1].verts[0][1] =-verts_height;
	cuberight[1].verts[0][2] =-1.0;
	cuberight[1].u[0] = uv_height;
	cuberight[1].v[0] = 0.0;

	cuberight[1].verts[1][0] = 1.0;
	cuberight[1].verts[1][1] = 1.0;
	cuberight[1].verts[1][2] = 1.0;	
	cuberight[1].u[1] = 0.0;
	cuberight[1].v[1] = uv_ratio;

	cuberight[1].verts[2][0] = 1.0;
	cuberight[1].verts[2][1] = 1.0;
	cuberight[1].verts[2][2] =-1.0;	
	cuberight[1].u[2] = 0.0;
	cuberight[1].v[2] = 0.0;

	nfacesright = 2;

	// top Face - 2 triangles
	cubetop[0].verts[0][0] =-1.0;
	cubetop[0].verts[0][1] = 1.0;
	cubetop[0].verts[0][2] = 1.0;
	cubetop[0].u[0] = 0.0;
	cubetop[0].v[0] = 0.0;

	cubetop[0].verts[1][0] = 1.0;
	cubetop[0].verts[1][1] =-verts_height;
	cubetop[0].verts[1][2] = 1.0;	
	cubetop[0].u[1] = uv_ratio;
	cubetop[0].v[1] = uv_height;

	cubetop[0].verts[2][0] =-1.0;
	cubetop[0].verts[2][1] =-verts_height;
	cubetop[0].verts[2][2] = 1.0;	
	cubetop[0].u[2] = 0.0;
	cubetop[0].v[2] = uv_height;

	//second triangle
	cubetop[1].verts[0][0] = 1.0;
	cubetop[1].verts[0][1] =-verts_height;
	cubetop[1].verts[0][2] = 1.0;
	cubetop[1].u[0] = uv_ratio;
	cubetop[1].v[0] = uv_height;

	cubetop[1].verts[1][0] =-1.0;
	cubetop[1].verts[1][1] = 1.0;
	cubetop[1].verts[1][2] = 1.0;	
	cubetop[1].u[1] = 0.0;
	cubetop[1].v[1] = 0.0;

	cubetop[1].verts[2][0] = 1.0;
	cubetop[1].verts[2][1] = 1.0;
	cubetop[1].verts[2][2] = 1.0;	
	cubetop[1].u[2] = uv_ratio;
	cubetop[1].v[2] = 0.0;

	nfacestop = 2;

	// bottom Face - 2 triangles
	cubebottom[0].verts[0][0] =-1.0;
	cubebottom[0].verts[0][1] =-verts_height;
	cubebottom[0].verts[0][2] =-1.0;
	cubebottom[0].u[0] = 0.0;
	cubebottom[0].v[0] = uv_base;

	cubebottom[0].verts[1][0] = 1.0;
	cubebottom[0].verts[1][1] = 1.0;
	cubebottom[0].verts[1][2] =-1.0;	
	cubebottom[0].u[1] = uv_ratio;
	cubebottom[0].v[1] = uv_ratio;

	cubebottom[0].verts[2][0] =-1.0;
	cubebottom[0].verts[2][1] = 1.0;
	cubebottom[0].verts[2][2] =-1.0;	
	cubebottom[0].u[2] = 0.0;
	cubebottom[0].v[2] = uv_ratio;

	//second triangle
	cubebottom[1].verts[0][0] = 1.0;
	cubebottom[1].verts[0][1] = 1.0;
	cubebottom[1].verts[0][2] =-1.0;
	cubebottom[1].u[0] = uv_ratio;
	cubebottom[1].v[0] = uv_ratio;

	cubebottom[1].verts[1][0] =-1.0;
	cubebottom[1].verts[1][1] =-verts_height;
	cubebottom[1].verts[1][2] =-1.0;	
	cubebottom[1].u[1] = 0.0;
	cubebottom[1].v[1] = uv_base;

	cubebottom[1].verts[2][0] = 1.0;
	cubebottom[1].verts[2][1] =-verts_height;
	cubebottom[1].verts[2][2] =-1.0;	
	cubebottom[1].u[2] = uv_ratio;
	cubebottom[1].v[2] = uv_base;

	nfacesbottom = 2;

	//Refine a triangular mesh by bisecting each edge forms 3 new triangles for each existing triangle on each iteration
	//It could be made more efficient for drawing if the triangles were ordered in a strip!

	for(i=0;i<m_resolution;i++){
		cubefront.resize(4*nfacesfront);
		SplitFace(cubefront,&nfacesfront);
		cubetop.resize(4*nfacestop);
		SplitFace(cubetop,&nfacestop);
		cubebottom.resize(4*nfacesbottom);
		SplitFace(cubebottom,&nfacesbottom);	
		cubeleft.resize(4*nfacesleft);
		SplitFace(cubeleft,&nfacesleft);
		cuberight.resize(4*nfacesright);
		SplitFace(cuberight,&nfacesright);
	}

	// Turn into a hemisphere/sphere
	for(j=0;j<3;j++){
		for(i=0;i<nfacesfront;i++)
			cubefront[i].verts[j].normalize();
		for(i=0;i<nfacestop;i++)
			cubetop[i].verts[j].normalize();
		for(i=0;i<nfacesbottom;i++)
			cubebottom[i].verts[j].normalize();
		for(i=0;i<nfacesleft;i++)
			cubeleft[i].verts[j].normalize();
		for(i=0;i<nfacesright;i++)
			cuberight[i].verts[j].normalize();
	}

	//flatten onto xz plane
	for(i=0;i<nfacesfront;i++)
		FlattenDome(cubefront[i].verts);	
	for(i=0;i<nfacestop;i++)
		FlattenDome(cubetop[i].verts);
	for(i=0;i<nfacesbottom;i++)
		FlattenDome(cubebottom[i].verts);
	for(i=0;i<nfacesleft;i++)
		FlattenDome(cubeleft[i].verts);		
	for(i=0;i<nfacesright;i++)
		FlattenDome(cuberight[i].verts);
}

void KX_Dome::CreateMeshPanorama(void)
{
/*
1)-  Define the faces of a cube without the top and bottom faces
 - each face is made out of 2 triangles
2) Subdivide the faces
 - more resolution == more curved lines
3) Spherize the cube
 - normalize the verts t
4) Flatten onto xz plane
 - use spherical projection techniques to transform the sphere onto a flat panorama
*/
	int i,j;

	float sqrt_2 = sqrt(2.0);
	float uv_ratio = (float)(m_buffersize-1) / m_imagesize;

	/* Top face - two triangles */
	cubetop[0].verts[0][0] = -sqrt_2;
	cubetop[0].verts[0][1] = 0.0;
	cubetop[0].verts[0][2] = 1.0;
	cubetop[0].u[0] = 0.0;
	cubetop[0].v[0] = uv_ratio;

	cubetop[0].verts[1][0] = 0.0;
	cubetop[0].verts[1][1] = sqrt_2;
	cubetop[0].verts[1][2] = 1.0;
	cubetop[0].u[1] = 0.0;
	cubetop[0].v[1] = 0.0;

	//second triangle
	cubetop[0].verts[2][0] = sqrt_2;
	cubetop[0].verts[2][1] = 0.0;
	cubetop[0].verts[2][2] = 1.0;
	cubetop[0].u[2] = uv_ratio;
	cubetop[0].v[2] = 0.0;

	cubetop[1].verts[0][0] = sqrt_2;
	cubetop[1].verts[0][1] = 0.0;
	cubetop[1].verts[0][2] = 1.0;
	cubetop[1].u[0] = uv_ratio;
	cubetop[1].v[0] = 0.0;

	cubetop[1].verts[1][0] = 0.0;
	cubetop[1].verts[1][1] = -sqrt_2;
	cubetop[1].verts[1][2] = 1.0;
	cubetop[1].u[1] = uv_ratio;
	cubetop[1].v[1] = uv_ratio;

	cubetop[1].verts[2][0] = -sqrt_2;
	cubetop[1].verts[2][1] = 0.0;
	cubetop[1].verts[2][2] = 1.0;
	cubetop[1].u[2] = 0.0;
	cubetop[1].v[2] = uv_ratio;

	nfacestop = 2;

	/* Bottom face - two triangles */
	cubebottom[0].verts[0][0] = -sqrt_2;
	cubebottom[0].verts[0][1] = 0.0;
	cubebottom[0].verts[0][2] = -1.0;
	cubebottom[0].u[0] = uv_ratio;
	cubebottom[0].v[0] = 0.0;

	cubebottom[0].verts[1][0] = sqrt_2;
	cubebottom[0].verts[1][1] = 0.0;
	cubebottom[0].verts[1][2] = -1.0;
	cubebottom[0].u[1] = 0.0;
	cubebottom[0].v[1] = uv_ratio;

	cubebottom[0].verts[2][0] = 0.0;
	cubebottom[0].verts[2][1] = sqrt_2;
	cubebottom[0].verts[2][2] = -1.0;
	cubebottom[0].u[2] = 0.0;
	cubebottom[0].v[2] = 0.0;

	//second triangle
	cubebottom[1].verts[0][0] = sqrt_2;
	cubebottom[1].verts[0][1] = 0.0;
	cubebottom[1].verts[0][2] = -1.0;
	cubebottom[1].u[0] = 0.0;
	cubebottom[1].v[0] = uv_ratio;

	cubebottom[1].verts[1][0] = -sqrt_2;
	cubebottom[1].verts[1][1] = 0.0;
	cubebottom[1].verts[1][2] = -1.0;
	cubebottom[1].u[1] = uv_ratio;
	cubebottom[1].v[1] = 0.0;

	cubebottom[1].verts[2][0] = 0.0;
	cubebottom[1].verts[2][1] = -sqrt_2;
	cubebottom[1].verts[2][2] = -1.0;
	cubebottom[1].u[2] = uv_ratio;
	cubebottom[1].v[2] = uv_ratio;

	nfacesbottom = 2;

	/* Left Back (135�) face - two triangles */

	cubeleftback[0].verts[0][0] = 0;
	cubeleftback[0].verts[0][1] = -sqrt_2;
	cubeleftback[0].verts[0][2] = -1.0;
	cubeleftback[0].u[0] = 0;
	cubeleftback[0].v[0] = 0;

	cubeleftback[0].verts[1][0] = -sqrt_2;
	cubeleftback[0].verts[1][1] = 0;
	cubeleftback[0].verts[1][2] = -1.0;
	cubeleftback[0].u[1] = uv_ratio;
	cubeleftback[0].v[1] = 0;

	cubeleftback[0].verts[2][0] = 0;
	cubeleftback[0].verts[2][1] = -sqrt_2;
	cubeleftback[0].verts[2][2] = 1.0;
	cubeleftback[0].u[2] = 0;
	cubeleftback[0].v[2] = uv_ratio;

	//second triangle
	cubeleftback[1].verts[0][0] = 0;
	cubeleftback[1].verts[0][1] = -sqrt_2;
	cubeleftback[1].verts[0][2] = 1.0;
	cubeleftback[1].u[0] = 0;
	cubeleftback[1].v[0] = uv_ratio;

	cubeleftback[1].verts[1][0] = -sqrt_2;
	cubeleftback[1].verts[1][1] = 0;
	cubeleftback[1].verts[1][2] = -1.0;
	cubeleftback[1].u[1] = uv_ratio;
	cubeleftback[1].v[1] = 0;

	cubeleftback[1].verts[2][0] = -sqrt_2;
	cubeleftback[1].verts[2][1] = 0;
	cubeleftback[1].verts[2][2] = 1.0;
	cubeleftback[1].u[2] = uv_ratio;
	cubeleftback[1].v[2] = uv_ratio;

	nfacesleftback = 2;

	/* Left face - two triangles */
	
	cubeleft[0].verts[0][0] = -sqrt_2;
	cubeleft[0].verts[0][1] = 0;
	cubeleft[0].verts[0][2] = -1.0;
	cubeleft[0].u[0] = 0;
	cubeleft[0].v[0] = 0;

	cubeleft[0].verts[1][0] = 0;
	cubeleft[0].verts[1][1] = sqrt_2;
	cubeleft[0].verts[1][2] = -1.0;
	cubeleft[0].u[1] = uv_ratio;
	cubeleft[0].v[1] = 0;

	cubeleft[0].verts[2][0] = -sqrt_2;
	cubeleft[0].verts[2][1] = 0;
	cubeleft[0].verts[2][2] = 1.0;
	cubeleft[0].u[2] = 0;
	cubeleft[0].v[2] = uv_ratio;

	//second triangle
	cubeleft[1].verts[0][0] = -sqrt_2;
	cubeleft[1].verts[0][1] = 0;
	cubeleft[1].verts[0][2] = 1.0;
	cubeleft[1].u[0] = 0;
	cubeleft[1].v[0] = uv_ratio;

	cubeleft[1].verts[1][0] = 0;
	cubeleft[1].verts[1][1] = sqrt_2;
	cubeleft[1].verts[1][2] = -1.0;
	cubeleft[1].u[1] = uv_ratio;
	cubeleft[1].v[1] = 0;

	cubeleft[1].verts[2][0] = 0;
	cubeleft[1].verts[2][1] = sqrt_2;
	cubeleft[1].verts[2][2] = 1.0;
	cubeleft[1].u[2] = uv_ratio;
	cubeleft[1].v[2] = uv_ratio;

	nfacesleft = 2;
	
	/* Right face - two triangles */
	cuberight[0].verts[0][0] = 0;
	cuberight[0].verts[0][1] = sqrt_2;
	cuberight[0].verts[0][2] = -1.0;
	cuberight[0].u[0] = 0;
	cuberight[0].v[0] = 0;

	cuberight[0].verts[1][0] = sqrt_2;
	cuberight[0].verts[1][1] = 0;
	cuberight[0].verts[1][2] = -1.0;
	cuberight[0].u[1] = uv_ratio;
	cuberight[0].v[1] = 0;

	cuberight[0].verts[2][0] = sqrt_2;
	cuberight[0].verts[2][1] = 0;
	cuberight[0].verts[2][2] = 1.0;
	cuberight[0].u[2] = uv_ratio;
	cuberight[0].v[2] = uv_ratio;

	//second triangle
	cuberight[1].verts[0][0] = 0;
	cuberight[1].verts[0][1] = sqrt_2;
	cuberight[1].verts[0][2] = -1.0;
	cuberight[1].u[0] = 0;
	cuberight[1].v[0] = 0;

	cuberight[1].verts[1][0] = sqrt_2;
	cuberight[1].verts[1][1] = 0;
	cuberight[1].verts[1][2] = 1.0;
	cuberight[1].u[1] = uv_ratio;
	cuberight[1].v[1] = uv_ratio;

	cuberight[1].verts[2][0] = 0;
	cuberight[1].verts[2][1] = sqrt_2;
	cuberight[1].verts[2][2] = 1.0;
	cuberight[1].u[2] = 0;
	cuberight[1].v[2] = uv_ratio;

	nfacesright = 2;
	
	/* Right Back  (-135�) face - two triangles */
	cuberightback[0].verts[0][0] = sqrt_2;
	cuberightback[0].verts[0][1] = 0;
	cuberightback[0].verts[0][2] = -1.0;
	cuberightback[0].u[0] = 0;
	cuberightback[0].v[0] = 0;

	cuberightback[0].verts[1][0] = 0;
	cuberightback[0].verts[1][1] = -sqrt_2;
	cuberightback[0].verts[1][2] = -1.0;
	cuberightback[0].u[1] = uv_ratio;
	cuberightback[0].v[1] = 0;

	cuberightback[0].verts[2][0] = 0;
	cuberightback[0].verts[2][1] = -sqrt_2;
	cuberightback[0].verts[2][2] = 1.0;
	cuberightback[0].u[2] = uv_ratio;
	cuberightback[0].v[2] = uv_ratio;

	//second triangle
	cuberightback[1].verts[0][0] = sqrt_2;
	cuberightback[1].verts[0][1] = 0;
	cuberightback[1].verts[0][2] = -1.0;
	cuberightback[1].u[0] = 0;
	cuberightback[1].v[0] = 0;

	cuberightback[1].verts[1][0] = 0;
	cuberightback[1].verts[1][1] = -sqrt_2;
	cuberightback[1].verts[1][2] = 1.0;
	cuberightback[1].u[1] = uv_ratio;
	cuberightback[1].v[1] = uv_ratio;

	cuberightback[1].verts[2][0] = sqrt_2;
	cuberightback[1].verts[2][1] = 0;
	cuberightback[1].verts[2][2] = 1.0;
	cuberightback[1].u[2] = 0;
	cuberightback[1].v[2] = uv_ratio;

	nfacesrightback = 2;

	// Subdivide the faces
	for(i=0;i<m_resolution;i++)
	{
		cubetop.resize(4*nfacestop);
		SplitFace(cubetop,&nfacestop);

		cubebottom.resize(4*nfacesbottom);
		SplitFace(cubebottom,&nfacesbottom);

		cubeleft.resize(4*nfacesleft);
		SplitFace(cubeleft,&nfacesleft);

		cuberight.resize(4*nfacesright);
		SplitFace(cuberight,&nfacesright);

		cubeleftback.resize(4*nfacesleftback);
		SplitFace(cubeleftback,&nfacesleftback);

		cuberightback.resize(4*nfacesrightback);
		SplitFace(cuberightback,&nfacesrightback);
	}

	// Spherize the cube
	for(j=0;j<3;j++)
	{
		for(i=0;i<nfacestop;i++)
			cubetop[i].verts[j].normalize();

		for(i=0;i<nfacesbottom;i++)
			cubebottom[i].verts[j].normalize();

		for(i=0;i<nfacesleftback;i++)
			cubeleftback[i].verts[j].normalize();

		for(i=0;i<nfacesleft;i++)
			cubeleft[i].verts[j].normalize();

		for(i=0;i<nfacesright;i++)
			cuberight[i].verts[j].normalize();

		for(i=0;i<nfacesrightback;i++)
			cuberightback[i].verts[j].normalize();
	}

	//Flatten onto xz plane
	for(i=0;i<nfacesleftback;i++)
		FlattenPanorama(cubeleftback[i].verts);

	for(i=0;i<nfacesleft;i++)
		FlattenPanorama(cubeleft[i].verts);

	for(i=0;i<nfacesright;i++)
		FlattenPanorama(cuberight[i].verts);

	for(i=0;i<nfacesrightback;i++)
		FlattenPanorama(cuberightback[i].verts);

	for(i=0;i<nfacestop;i++)
		FlattenPanorama(cubetop[i].verts);

	for(i=0;i<nfacesbottom;i++)
		FlattenPanorama(cubebottom[i].verts);
}

void KX_Dome::FlattenDome(MT_Vector3 verts[3])
{
	double phi, r;

	for (int i=0;i<3;i++){
		r = atan2(sqrt(verts[i][0]*verts[i][0] + verts[i][2]*verts[i][2]), verts[i][1]);
		r /= m_radangle/2;

		phi = atan2(verts[i][2], verts[i][0]);

		verts[i][0] = r * cos(phi);
		verts[i][1] = 0;
		verts[i][2] = r * sin(phi);

		if (r > 1.0){
		//round the border
			verts[i][0] = cos(phi);
			verts[i][1] = -3.0;
			verts[i][2] = sin(phi);
		}
	}
}

void KX_Dome::FlattenPanorama(MT_Vector3 verts[3])
{
// it creates a full spherical panoramic (360�)
	int i;
	double phi;
	bool edge=false;

	for (i=0;i<3;i++){
		phi = atan2(verts[i][1], verts[i][0]);
		phi *= -1.0; //flipping

		if (phi == -MT_PI) //It's on the edge
			edge=true;

		verts[i][0] = phi / MT_PI;
		verts[i][1] = 0;

		verts[i][2] = atan2(verts[i][2], 1.0);
		verts[i][2] /= MT_PI / 2;
	}
	if(edge){
		bool right=false;

		for (i=0;i<3;i++){
			if(fmod(verts[i][0],1.0) > 0.0){
				right=true;
				break;
			}
		}
		if(right){
			for (i=0;i<3;i++){
				if(verts[i][0] < 0.0)
					verts[i][0] *= -1.0;
			}
		}
	}
}

void KX_Dome::SplitFace(vector <DomeFace>& face, int *nfaces)
{
	int i;
	int n1, n2;

	n1 = n2 = *nfaces;

	for(i=0;i<n1;i++){

		face[n2].verts[0] = (face[i].verts[0] + face[i].verts[1]) /2;
		face[n2].verts[1] =  face[i].verts[1];
		face[n2].verts[2] = (face[i].verts[1] + face[i].verts[2]) /2;
		face[n2].u[0]	  = (face[i].u[0] + face[i].u[1]) /2;
		face[n2].u[1]	  =  face[i].u[1];
		face[n2].u[2]	  = (face[i].u[1] + face[i].u[2]) /2;
		face[n2].v[0]	  = (face[i].v[0] + face[i].v[1]) /2;
		face[n2].v[1]	  =  face[i].v[1];
		face[n2].v[2]	  = (face[i].v[1] + face[i].v[2]) /2;

		face[n2+1].verts[0] = (face[i].verts[1] + face[i].verts[2]) /2;
		face[n2+1].verts[1] =  face[i].verts[2];
		face[n2+1].verts[2] = (face[i].verts[2] + face[i].verts[0]) /2;
		face[n2+1].u[0]		= (face[i].u[1] + face[i].u[2]) /2;
		face[n2+1].u[1]		=  face[i].u[2];
		face[n2+1].u[2]		= (face[i].u[2] + face[i].u[0]) /2;
		face[n2+1].v[0]		= (face[i].v[1] + face[i].v[2]) /2;
		face[n2+1].v[1]		=  face[i].v[2];
		face[n2+1].v[2]		= (face[i].v[2] + face[i].v[0]) /2;

		face[n2+2].verts[0] = (face[i].verts[0] + face[i].verts[1]) /2;
		face[n2+2].verts[1] = (face[i].verts[1] + face[i].verts[2]) /2;
		face[n2+2].verts[2] = (face[i].verts[2] + face[i].verts[0]) /2;
		face[n2+2].u[0]	  = (face[i].u[0] + face[i].u[1]) /2;
		face[n2+2].u[1]	  = (face[i].u[1] + face[i].u[2]) /2;
		face[n2+2].u[2]	  = (face[i].u[2] + face[i].u[0]) /2;
		face[n2+2].v[0]	  = (face[i].v[0] + face[i].v[1]) /2;
		face[n2+2].v[1]	  = (face[i].v[1] + face[i].v[2]) /2;
		face[n2+2].v[2]	  = (face[i].v[2] + face[i].v[0]) /2;		

		//face[i].verts[0] = face[i].verts[0] ;
		face[i].verts[1] = (face[i].verts[0] + face[i].verts[1]) /2;
		face[i].verts[2] = (face[i].verts[0] + face[i].verts[2]) /2;
		//face[i].u[0]	 =  face[i].u[0];
		face[i].u[1]	 = (face[i].u[0] + face[i].u[1]) /2;
		face[i].u[2]	 = (face[i].u[0] + face[i].u[2]) /2;
		//face[i].v[0]	 = face[i].v[0] ;
		face[i].v[1]	 = (face[i].v[0] + face[i].v[1]) /2;
		face[i].v[2]	 = (face[i].v[0] + face[i].v[2]) /2;		

		n2 += 3; // number of faces
	}
	*nfaces = n2;
}

void KX_Dome::CalculateFrustum(KX_Camera * cam)
{
	/*
	// manually creating a 90� Field of View Frustum 

	 the original formula:
	top = tan(fov*3.14159/360.0) * near [for fov in degrees]
	fov*0.5 = arctan ((top-bottom)*0.5 / near) [for fov in radians]
	bottom = -top
	left = aspect * bottom
	right = aspect * top

	// the equivalent GLU call is:
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	gluPerspective(90.0,1.0,cam->GetCameraNear(),cam->GetCameraFar());
	*/

	RAS_FrameFrustum m_frustrum; //90 deg. Frustum

	m_frustrum.camnear = cam->GetCameraNear();
	m_frustrum.camfar = cam->GetCameraFar();

//	float top = tan(90.0*MT_PI/360.0) * m_frustrum.camnear;
	float top = m_frustrum.camnear; // for deg = 90�, tan = 1

	m_frustrum.x1 = -top;
	m_frustrum.x2 = top;
	m_frustrum.y1 = -top;
	m_frustrum.y2 = top;
	
	m_projmat = m_rasterizer->GetFrustumMatrix(
	m_frustrum.x1, m_frustrum.x2, m_frustrum.y1, m_frustrum.y2, m_frustrum.camnear, m_frustrum.camfar);

}

void KX_Dome::CalculateCameraOrientation()
{
/*
Uses 4 cameras for angles up to 180�
Uses 5 cameras for angles up to 250�
Uses 6 cameras for angles up to 360�
*/
	float deg45 = MT_PI / 4;
	MT_Scalar c = cos(deg45);
	MT_Scalar s = sin(deg45);

	if ((m_mode == DOME_FISHEYE && m_angle <= 180)|| m_mode == DOME_TRUNCATED){

		m_locRot[0] = MT_Matrix3x3( // 90� - Top
						c, -s, 0.0,
						0.0,0.0, -1.0,
						s, c, 0.0);

		m_locRot[1] = MT_Matrix3x3( // 90� - Bottom
						-s, c, 0.0,
						0.0,0.0, 1.0,
						s, c, 0.0);

		m_locRot[2] = MT_Matrix3x3( // 45� - Left
						c, 0.0, s,
						0, 1.0, 0.0,
						-s, 0.0, c);

		m_locRot[3] = MT_Matrix3x3( // 45� - Right
						c, 0.0, -s,
						0.0, 1.0, 0.0,
						s, 0.0, c);

	} else if ((m_mode == DOME_FISHEYE && m_angle > 180)){

		m_locRot[0] = MT_Matrix3x3( // 90� - Top
						 1.0, 0.0, 0.0,
						 0.0, 0.0,-1.0,
						 0.0, 1.0, 0.0);

		m_locRot[1] = MT_Matrix3x3( // 90� - Bottom
						 1.0, 0.0, 0.0,
						 0.0, 0.0, 1.0,
						 0.0,-1.0, 0.0);

		m_locRot[2] = MT_Matrix3x3( // -90� - Left
						 0.0, 0.0, 1.0,
						 0.0, 1.0, 0.0,
						 -1.0, 0.0, 0.0);

		m_locRot[3] = MT_Matrix3x3( // 90� - Right
						 0.0, 0.0,-1.0,
						 0.0, 1.0, 0.0,
						 1.0, 0.0, 0.0);
						
		m_locRot[4] = MT_Matrix3x3( // 0� - Front
						1.0, 0.0, 0.0,
						0.0, 1.0, 0.0,
						0.0, 0.0, 1.0);

		m_locRot[5] = MT_Matrix3x3( // 180� - Back - NOT USING
						-1.0, 0.0, 0.0,
						 0.0, 1.0, 0.0,
						 0.0, 0.0,-1.0);

	} else if (m_mode == DOME_PANORAM_SPH){

		m_locRot[0] = MT_Matrix3x3( // Top 
						c, s, 0.0,
						0.0,0.0, -1.0,
						-s, c, 0.0);

		m_locRot[1] = MT_Matrix3x3( // Bottom
						c, s, 0.0,
						0.0 ,0.0, 1.0,
						s, -c, 0.0);

		m_locRot[2] = MT_Matrix3x3( // 45� - Left
						-s, 0.0, c,
						0, 1.0, 0.0,
						-c, 0.0, -s);

		m_locRot[3] = MT_Matrix3x3( // 45� - Right
						c, 0.0, s,
						0, 1.0, 0.0,
						-s, 0.0, c);

		m_locRot[4] = MT_Matrix3x3( // 135� - LeftBack
						-s, 0.0, -c,
						0.0, 1.0, 0.0,
						c, 0.0, -s);

		m_locRot[5] = MT_Matrix3x3( // 135� - RightBack
						c, 0.0, -s,
						0.0, 1.0, 0.0,
						s, 0.0, c);
	}
}

void KX_Dome::RotateCamera(KX_Camera* cam, int i)
{
// I'm not using it, I'm doing inline calls for these commands
// but it's nice to have it here in case I need it

	MT_Matrix3x3 camori = cam->GetSGNode()->GetLocalOrientation();

	cam->NodeSetLocalOrientation(camori*m_locRot[i]);
	cam->NodeUpdateGS(0.f);

	MT_Transform camtrans(cam->GetWorldToCamera());
	MT_Matrix4x4 viewmat(camtrans);
	m_rasterizer->SetViewMatrix(viewmat, cam->NodeGetWorldPosition(),
		cam->GetCameraLocation(), cam->GetCameraOrientation());
	cam->SetModelviewMatrix(viewmat);

	// restore the original orientation
	cam->NodeSetLocalOrientation(camori);
	cam->NodeUpdateGS(0.f);
}

void KX_Dome::Draw(void)
{

	switch(m_mode){
		case DOME_FISHEYE:
			DrawDomeFisheye();
			break;
		case DOME_TRUNCATED:
			DrawDomeFisheye();
			break;
		case DOME_PANORAM_SPH:
			DrawPanorama();
			break;
	}

	if(warp.usemesh)
	{
		glBindTexture(GL_TEXTURE_2D, domefacesId[m_numfaces]);
		glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, m_viewport.GetLeft(), m_viewport.GetBottom(), warp.bufferwidth, warp.bufferheight);
		DrawDomeWarped();
	}
}

void KX_Dome::DrawDomeFisheye(void)
{
	int i,j;

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();

	// Making the viewport always square 

	int can_width = m_viewport.GetRight();
	int can_height = m_viewport.GetTop();

	float ortho_width, ortho_height;

	if (warp.usemesh)
		glOrtho((-1.0), 1.0, (-1.0), 1.0, -20.0, 10.0); //stretch the image to reduce resolution lost

	else if(m_mode == DOME_TRUNCATED){
		ortho_width = 1.0;
		ortho_height = 2 * ((float)can_height/can_width) - 1.0 ;
		
		ortho_width /= m_size;
		ortho_height /= m_size;

		glOrtho((-ortho_width), ortho_width, (-ortho_height), ortho_width, -20.0, 10.0);
	} else {
		if (can_width < can_height){
			ortho_width = 1.0;
			ortho_height = (float)can_height/can_width;
		}else{
			ortho_width = (float)can_width/can_height;
			ortho_height = 1.0;
		}
		
		ortho_width /= m_size;
		ortho_height /= m_size;
		
		glOrtho((-ortho_width), ortho_width, (-ortho_height), ortho_height, -20.0, 10.0);
	}

	glMatrixMode(GL_TEXTURE);
	glLoadIdentity();
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	gluLookAt(0.0,-1.0,0.0, 0.0,0.0,0.0, 0.0,0.0,1.0);

	if(m_drawingmode == RAS_IRasterizer::KX_WIREFRAME)
		glPolygonMode(GL_FRONT, GL_LINE);
	else
		glPolygonMode(GL_FRONT, GL_FILL);

	glShadeModel(GL_SMOOTH);
	glDisable(GL_LIGHTING);
	glDisable(GL_DEPTH_TEST);

	glEnable(GL_TEXTURE_2D);
	glColor3f(1.0,1.0,1.0);

	if (dlistSupported){
		for(i=0;i<m_numfaces;i++){
			glBindTexture(GL_TEXTURE_2D, domefacesId[i]);
			glCallList(dlistId+i);
		}
	}
	else { // DisplayLists not supported
		// top triangle
		glBindTexture(GL_TEXTURE_2D, domefacesId[0]);
		GLDrawTriangles(cubetop, nfacestop);

		// bottom triangle	
		glBindTexture(GL_TEXTURE_2D, domefacesId[1]);
		GLDrawTriangles(cubebottom, nfacesbottom);

		// left triangle
		glBindTexture(GL_TEXTURE_2D, domefacesId[2]);
		GLDrawTriangles(cubeleft, nfacesleft);

		// right triangle
		glBindTexture(GL_TEXTURE_2D, domefacesId[3]);
		GLDrawTriangles(cuberight, nfacesright);

		if (m_angle > 180){
			// front triangle
			glBindTexture(GL_TEXTURE_2D, domefacesId[4]);
			GLDrawTriangles(cubefront, nfacesfront);
		}
	}
	glDisable(GL_TEXTURE_2D);
	glEnable(GL_DEPTH_TEST);
}

void KX_Dome::DrawPanorama(void)
{
	int i,j;
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();

	// Making the viewport always square 

	int can_width = m_viewport.GetRight();
	int can_height = m_viewport.GetTop();

	float ortho_height = 1.0;
	float ortho_width = 1.0;

	if (warp.usemesh)
		glOrtho((-1.0), 1.0, (-0.5), 0.5, -20.0, 10.0); //stretch the image to reduce resolution lost

	else {
		//using all the screen
		if ((can_width / 2) <= (can_height)){
			ortho_width = 1.0;
			ortho_height = (float)can_height/can_width;
		}else{
			ortho_width = (float)can_width/can_height * 0.5;
			ortho_height = 0.5;
		}

		ortho_width /= m_size;
		ortho_height /= m_size;
		
		glOrtho((-ortho_width), ortho_width, (-ortho_height), ortho_height, -20.0, 10.0);
	}

	glMatrixMode(GL_TEXTURE);
	glLoadIdentity();
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	gluLookAt(0.0,-1.0,0.0, 0.0,0.0,0.0, 0.0,0.0,1.0);

	if(m_drawingmode == RAS_IRasterizer::KX_WIREFRAME)
		glPolygonMode(GL_FRONT, GL_LINE);
	else
		glPolygonMode(GL_FRONT, GL_FILL);

	glShadeModel(GL_SMOOTH);
	glDisable(GL_LIGHTING);
	glDisable(GL_DEPTH_TEST);

	glEnable(GL_TEXTURE_2D);
	glColor3f(1.0,1.0,1.0);

	if (dlistSupported){
		for(i=0;i<m_numfaces;i++){
			glBindTexture(GL_TEXTURE_2D, domefacesId[i]);
			glCallList(dlistId+i);
		}
	}
	else {
		// domefacesId[4] =>  (top)
		glBindTexture(GL_TEXTURE_2D, domefacesId[0]);
			GLDrawTriangles(cubetop, nfacestop);

		// domefacesId[5] =>  (bottom)
		glBindTexture(GL_TEXTURE_2D, domefacesId[1]);
			GLDrawTriangles(cubebottom, nfacesbottom);

		// domefacesId[1] => -45� (left)
		glBindTexture(GL_TEXTURE_2D, domefacesId[2]);
			GLDrawTriangles(cubeleft, nfacesleft);

		// domefacesId[2] => 45� (right)
		glBindTexture(GL_TEXTURE_2D, domefacesId[3]);
			GLDrawTriangles(cuberight, nfacesright);

		// domefacesId[0] => -135� (leftback)
		glBindTexture(GL_TEXTURE_2D, domefacesId[4]);
			GLDrawTriangles(cubeleftback, nfacesleftback);

		// domefacesId[3] => 135� (rightback)
		glBindTexture(GL_TEXTURE_2D, domefacesId[5]);
			GLDrawTriangles(cuberightback, nfacesrightback);
	}
	glDisable(GL_TEXTURE_2D);
	glEnable(GL_DEPTH_TEST);
}

void KX_Dome::DrawDomeWarped(void)
{
	int i,j;

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();

	// Making the viewport always square 
	int can_width = m_viewport.GetRight();
	int can_height = m_viewport.GetTop();

	double screen_ratio = can_width/ (double) can_height;	
	screen_ratio /= m_size;

    glOrtho(-screen_ratio,screen_ratio,-1.0,1.0,-20.0,10.0);


	glMatrixMode(GL_TEXTURE);
	glLoadIdentity();
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	gluLookAt(0.0, 0.0, 1.0, 0.0,0.0,0.0, 0.0,1.0,0.0);

	if(m_drawingmode == RAS_IRasterizer::KX_WIREFRAME)
		glPolygonMode(GL_FRONT, GL_LINE);
	else
		glPolygonMode(GL_FRONT, GL_FILL);

	glShadeModel(GL_SMOOTH);
	glDisable(GL_LIGHTING);
	glDisable(GL_DEPTH_TEST);

	glEnable(GL_TEXTURE_2D);
	glColor3f(1.0,1.0,1.0);


	float uv_width = (float)(warp.bufferwidth-1) / warp.imagewidth;
	float uv_height = (float)(warp.bufferheight-1) / warp.imageheight;

	if (dlistSupported){
		glBindTexture(GL_TEXTURE_2D, domefacesId[m_numfaces]);
		glCallList(dlistId + m_numfaces);
	}
	else{
		glBindTexture(GL_TEXTURE_2D, domefacesId[m_numfaces]);
		GLDrawWarpQuads();
	}
	glDisable(GL_TEXTURE_2D);
	glEnable(GL_DEPTH_TEST);
}

void KX_Dome::BindImages(int i)
{
	glBindTexture(GL_TEXTURE_2D, domefacesId[i]);
	glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, m_viewport.GetLeft(), m_viewport.GetBottom(), m_buffersize, m_buffersize);
}

void KX_Dome::RenderDomeFrame(KX_Scene* scene, KX_Camera* cam, int i)
{
	if (!cam)
		return;

	m_canvas->SetViewPort(0,0,m_buffersize-1,m_buffersize-1);

//	m_rasterizer->SetAmbient();
	m_rasterizer->DisplayFog();

	CalculateFrustum(cam); //calculates m_projmat
	cam->SetProjectionMatrix(m_projmat);
	m_rasterizer->SetProjectionMatrix(cam->GetProjectionMatrix());
//	Dome_RotateCamera(cam,i);

	MT_Matrix3x3 camori = cam->GetSGNode()->GetLocalOrientation();

	cam->NodeSetLocalOrientation(camori*m_locRot[i]);
	cam->NodeUpdateGS(0.f);

	MT_Transform camtrans(cam->GetWorldToCamera());
	MT_Matrix4x4 viewmat(camtrans);
	m_rasterizer->SetViewMatrix(viewmat, cam->NodeGetWorldPosition(),
		cam->GetCameraLocation(), cam->GetCameraOrientation());
	cam->SetModelviewMatrix(viewmat);

	scene->CalculateVisibleMeshes(m_rasterizer,cam);
	scene->RenderBuckets(camtrans, m_rasterizer, m_rendertools);
	
	// restore the original orientation
	cam->NodeSetLocalOrientation(camori);
	cam->NodeUpdateGS(0.f);
}