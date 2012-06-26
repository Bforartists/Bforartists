/*
 * Copyright 2011, Blender Foundation.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor: 
 *		Jeroen Bakker 
 *		Monique Dewanchand
 */

#include <string.h>

#include "BKE_node.h"

#include "COM_AlphaOverNode.h"
#include "COM_BilateralBlurNode.h"
#include "COM_BlurNode.h"
#include "COM_BokehBlurNode.h"
#include "COM_BokehImageNode.h"
#include "COM_BoxMaskNode.h"
#include "COM_BrightnessNode.h"
#include "COM_ChannelMatteNode.h"
#include "COM_ChromaMatteNode.h"
#include "COM_ColorBalanceNode.h"
#include "COM_ColorCorrectionNode.h"
#include "COM_ColorCurveNode.h"
#include "COM_ColorMatteNode.h"
#include "COM_ColorNode.h"
#include "COM_ColorRampNode.h"
#include "COM_ColorSpillNode.h"
#include "COM_ColorToBWNode.h"
#include "COM_CombineHSVANode.h"
#include "COM_CombineRGBANode.h"
#include "COM_CombineYCCANode.h"
#include "COM_CombineYUVANode.h"
#include "COM_CompositorNode.h"
#include "COM_ConvertAlphaNode.h"
#include "COM_ConvertColorToVectorOperation.h"
#include "COM_ConvertColourToValueProg.h"
#include "COM_ConvertValueToColourProg.h"
#include "COM_ConvertValueToVectorOperation.h"
#include "COM_ConvertVectorToColorOperation.h"
#include "COM_ConvertVectorToValueOperation.h"
#include "COM_Converter.h"
#include "COM_CropNode.h"
#include "COM_DefocusNode.h"
#include "COM_DifferenceMatteNode.h"
#include "COM_DilateErodeNode.h"
#include "COM_DirectionalBlurNode.h"
#include "COM_DisplaceNode.h"
#include "COM_DistanceMatteNode.h"
#include "COM_DoubleEdgeMaskNode.h"
#include "COM_EllipseMaskNode.h"
#include "COM_ExecutionSystem.h"
#include "COM_ExecutionSystemHelper.h"
#include "COM_FilterNode.h"
#include "COM_FlipNode.h"
#include "COM_GammaNode.h"
#include "COM_GlareNode.h"
#include "COM_GroupNode.h"
#include "COM_HueSaturationValueCorrectNode.h"
#include "COM_HueSaturationValueNode.h"
#include "COM_IDMaskNode.h"
#include "COM_ImageNode.h"
#include "COM_InvertNode.h"
#include "COM_KeyingNode.h"
#include "COM_KeyingScreenNode.h"
#include "COM_LensDistortionNode.h"
#include "COM_LuminanceMatteNode.h"
#include "COM_MapUVNode.h"
#include "COM_MapValueNode.h"
#include "COM_MaskNode.h"
#include "COM_MathNode.h"
#include "COM_MixNode.h"
#include "COM_MovieClipNode.h"
#include "COM_MovieDistortionNode.h"
#include "COM_MuteNode.h"
#include "COM_NormalNode.h"
#include "COM_NormalizeNode.h"
#include "COM_OutputFileNode.h"
#include "COM_RenderLayersNode.h"
#include "COM_RotateNode.h"
#include "COM_ScaleNode.h"
#include "COM_ScaleOperation.h"
#include "COM_SeparateHSVANode.h"
#include "COM_SeparateRGBANode.h"
#include "COM_SeparateYCCANode.h"
#include "COM_SeparateYUVANode.h"
#include "COM_SetAlphaNode.h"
#include "COM_SetValueOperation.h"
#include "COM_SocketConnection.h"
#include "COM_SplitViewerNode.h"
#include "COM_Stabilize2dNode.h"
#include "COM_SwitchNode.h"
#include "COM_TextureNode.h"
#include "COM_TimeNode.h"
#include "COM_TonemapNode.h"
#include "COM_TransformNode.h"
#include "COM_TranslateNode.h"
#include "COM_TranslateOperation.h"
#include "COM_TrackPositionNode.h"
#include "COM_ValueNode.h"
#include "COM_VectorBlurNode.h"
#include "COM_VectorCurveNode.h"
#include "COM_ViewLevelsNode.h"
#include "COM_ViewerNode.h"
#include "COM_ZCombineNode.h"

Node *Converter::convert(bNode *b_node)
{
	Node *node;

	if (b_node->flag & NODE_MUTED) {
		node = new MuteNode(b_node);
		return node;
	}

	switch (b_node->type) {
		case CMP_NODE_COMPOSITE:
			node = new CompositorNode(b_node);
			break;
		case CMP_NODE_R_LAYERS:
			node = new RenderLayersNode(b_node);
			break;
		case CMP_NODE_TEXTURE:
			node = new TextureNode(b_node);
			break;
		case CMP_NODE_RGBTOBW:
			node = new ColourToBWNode(b_node);
			break;
		case CMP_NODE_MIX_RGB:
			node = new MixNode(b_node);
			break;
		case CMP_NODE_TRANSLATE:
			node = new TranslateNode(b_node);
			break;
		case CMP_NODE_SCALE:
			node = new ScaleNode(b_node);
			break;
		case CMP_NODE_ROTATE:
			node = new RotateNode(b_node);
			break;
		case CMP_NODE_FLIP:
			node = new FlipNode(b_node);
			break;
		case CMP_NODE_FILTER:
			node = new FilterNode(b_node);
			break;
		case CMP_NODE_ID_MASK:
			node = new IDMaskNode(b_node);
			break;
		case CMP_NODE_BRIGHTCONTRAST:
			node = new BrightnessNode(b_node);
			break;
		case CMP_NODE_SEPRGBA:
			node = new SeparateRGBANode(b_node);
			break;
		case CMP_NODE_COMBRGBA:
			node = new CombineRGBANode(b_node);
			break;
		case CMP_NODE_SEPHSVA:
			node = new SeparateHSVANode(b_node);
			break;
		case CMP_NODE_COMBHSVA:
			node = new CombineHSVANode(b_node);
			break;
		case CMP_NODE_SEPYUVA:
			node = new SeparateYUVANode(b_node);
			break;
		case CMP_NODE_COMBYUVA:
			node = new CombineYUVANode(b_node);
			break;
		case CMP_NODE_SEPYCCA:
			node = new SeparateYCCANode(b_node);
			break;
		case CMP_NODE_COMBYCCA:
			node = new CombineYCCANode(b_node);
			break;
		case CMP_NODE_ALPHAOVER:
			node = new AlphaOverNode(b_node);
			break;
		case CMP_NODE_COLORBALANCE:
			node = new ColorBalanceNode(b_node);
			break;
		case CMP_NODE_VIEWER:
			node = new ViewerNode(b_node);
			break;
		case CMP_NODE_SPLITVIEWER:
			node = new SplitViewerNode(b_node);
			break;
		case CMP_NODE_INVERT:
			node = new InvertNode(b_node);
			break;
		case NODE_GROUP:
			node = new GroupNode(b_node);
			break;
		case CMP_NODE_NORMAL:
			node = new NormalNode(b_node);
			break;
		case CMP_NODE_NORMALIZE:
			node = new NormalizeNode(b_node);
			break;
		case CMP_NODE_IMAGE:
			node = new ImageNode(b_node);
			break;
		case CMP_NODE_SETALPHA:
			node = new SetAlphaNode(b_node);
			break;
		case CMP_NODE_PREMULKEY:
			node = new ConvertAlphaNode(b_node);
			break;
		case CMP_NODE_MATH:
			node = new MathNode(b_node);
			break;
		case CMP_NODE_HUE_SAT:
			node = new HueSaturationValueNode(b_node);
			break;
		case CMP_NODE_COLORCORRECTION:
			node = new ColorCorrectionNode(b_node);
			break;
		case CMP_NODE_MASK_BOX:
			node = new BoxMaskNode(b_node);
			break;
		case CMP_NODE_MASK_ELLIPSE:
			node = new EllipseMaskNode(b_node);
			break;
		case CMP_NODE_GAMMA:
			node = new GammaNode(b_node);
			break;
		case CMP_NODE_CURVE_RGB:
			node = new ColorCurveNode(b_node);
			break;
		case CMP_NODE_CURVE_VEC:
			node = new VectorCurveNode(b_node);
			break;
		case CMP_NODE_HUECORRECT:
			node = new HueSaturationValueCorrectNode(b_node);
			break;
		case CMP_NODE_MAP_UV:
			node = new MapUVNode(b_node);
			break;
		case CMP_NODE_DISPLACE:
			node = new DisplaceNode(b_node);
			break;
		case CMP_NODE_VALTORGB:
			node = new ColorRampNode(b_node);
			break;
		case CMP_NODE_DIFF_MATTE:
			node = new DifferenceMatteNode(b_node);
			break;
		case CMP_NODE_LUMA_MATTE:
			node = new LuminanceMatteNode(b_node);
			break;
		case CMP_NODE_DIST_MATTE:
			node = new DistanceMatteNode(b_node);
			break;
		case CMP_NODE_CHROMA_MATTE:
			node = new ChromaMatteNode(b_node);
			break;
		case CMP_NODE_COLOR_MATTE:
			node = new ColorMatteNode(b_node);
			break;
		case CMP_NODE_CHANNEL_MATTE:
			node = new ChannelMatteNode(b_node);
			break;
		case CMP_NODE_BLUR:
			node = new BlurNode(b_node);
			break;
		case CMP_NODE_BOKEHIMAGE:
			node = new BokehImageNode(b_node);
			break;
		case CMP_NODE_BOKEHBLUR:
			node = new BokehBlurNode(b_node);
			break;
		case CMP_NODE_DILATEERODE:
			node = new DilateErodeNode(b_node);
			break;
		case CMP_NODE_LENSDIST:
			node = new LensDistortionNode(b_node);
			break;
		case CMP_NODE_RGB:
			node = new ColorNode(b_node);
			break;
		case CMP_NODE_VALUE:
			node = new ValueNode(b_node);
			break;
		case CMP_NODE_TIME:
			node = new TimeNode(b_node);
			break;
		case CMP_NODE_DBLUR:
			node = new DirectionalBlurNode(b_node);
			break;
		case CMP_NODE_ZCOMBINE:
			node = new ZCombineNode(b_node);
			break;
		case CMP_NODE_TONEMAP:
			node = new TonemapNode(b_node);
			break;
		case CMP_NODE_SWITCH:
			node = new SwitchNode(b_node);
			break;
		case CMP_NODE_GLARE:
			node = new GlareNode(b_node);
			break;
		case CMP_NODE_MOVIECLIP:
			node = new MovieClipNode(b_node);
			break;
		case CMP_NODE_COLOR_SPILL:
			node = new ColorSpillNode(b_node);
			break;
		case CMP_NODE_OUTPUT_FILE:
			node = new OutputFileNode(b_node);
			break;
		case CMP_NODE_MAP_VALUE:
			node = new MapValueNode(b_node);
			break;
		case CMP_NODE_TRANSFORM:
			node = new TransformNode(b_node);
			break;
		case CMP_NODE_STABILIZE2D:
			node = new Stabilize2dNode(b_node);
			break;
		case CMP_NODE_BILATERALBLUR:
			node = new BilateralBlurNode(b_node);
			break;
		case CMP_NODE_VECBLUR:
			node = new VectorBlurNode(b_node);
			break;
		case CMP_NODE_MOVIEDISTORTION:
			node = new MovieDistortionNode(b_node);
			break;
		case CMP_NODE_VIEW_LEVELS:
			node = new ViewLevelsNode(b_node);
			break;
		case CMP_NODE_DEFOCUS:
			node = new DefocusNode(b_node);
			break;
		case CMP_NODE_DOUBLEEDGEMASK:
			node = new DoubleEdgeMaskNode(b_node);
			break;
		case CMP_NODE_CROP:
			node = new CropNode(b_node);
			break;
		case CMP_NODE_MASK:
			node = new MaskNode(b_node);
			break;
		case CMP_NODE_KEYINGSCREEN:
			node = new KeyingScreenNode(b_node);
			break;
		case CMP_NODE_KEYING:
			node = new KeyingNode(b_node);
			break;
		case CMP_NODE_TRACKPOS:
			node = new TrackPositionNode(b_node);
			break;
		/* not inplemented yet */
		default:
			node = new MuteNode(b_node);
			break;
	}
	return node;
}
void Converter::convertDataType(SocketConnection *connection, ExecutionSystem *system)
{
	OutputSocket *outputSocket = connection->getFromSocket();
	InputSocket *inputSocket = connection->getToSocket();
	DataType fromDatatype = outputSocket->getDataType();
	DataType toDatatype = inputSocket->getDataType();
	NodeOperation *converter = NULL;
	if (fromDatatype == COM_DT_VALUE && toDatatype == COM_DT_COLOR) {
		converter = new ConvertValueToColourProg();
	}
	else if (fromDatatype == COM_DT_VALUE && toDatatype == COM_DT_VECTOR) {
		converter = new ConvertValueToVectorOperation();
	}
	else if (fromDatatype == COM_DT_COLOR && toDatatype == COM_DT_VALUE) {
		converter = new ConvertColourToValueProg();
	}
	else if (fromDatatype == COM_DT_COLOR && toDatatype == COM_DT_VECTOR) {
		converter = new ConvertColorToVectorOperation();
	}
	else if (fromDatatype == COM_DT_VECTOR && toDatatype == COM_DT_VALUE) {
		converter = new ConvertVectorToValueOperation();
	}
	else if (fromDatatype == COM_DT_VECTOR && toDatatype == COM_DT_COLOR) {
		converter = new ConvertVectorToColorOperation();
	}
	if (converter != NULL) {
		inputSocket->relinkConnections(converter->getInputSocket(0));
		ExecutionSystemHelper::addLink(system->getConnections(), converter->getOutputSocket(), inputSocket);
		system->addOperation(converter);
	}
}

void Converter::convertResolution(SocketConnection *connection, ExecutionSystem *system)
{
	InputSocketResizeMode mode = connection->getToSocket()->getResizeMode();

	NodeOperation *toOperation = (NodeOperation *)connection->getToNode();
	const float toWidth = toOperation->getWidth();
	const float toHeight = toOperation->getHeight();
	NodeOperation *fromOperation = (NodeOperation *)connection->getFromNode();
	const float fromWidth = fromOperation->getWidth();
	const float fromHeight = fromOperation->getHeight();
	bool doCenter = false;
	bool doScale = false;
	float addX = (toWidth - fromWidth) / 2.0f;
	float addY = (toHeight - fromHeight) / 2.0f;
	float scaleX = 0;
	float scaleY = 0;

	switch (mode) {
		case COM_SC_NO_RESIZE:
			break;
		case COM_SC_CENTER:
			doCenter = true;
			break;
		case COM_SC_FIT_WIDTH:
			doCenter = true;
			doScale = true;
			scaleX = scaleY = toWidth / fromWidth;
			break;
		case COM_SC_FIT_HEIGHT:
			doCenter = true;
			doScale = true;
			scaleX = scaleY = toHeight / fromHeight;
			break;
		case COM_SC_FIT:
			doCenter = true;
			doScale = true;
			scaleX = toWidth / fromWidth;
			scaleY = toHeight / fromHeight;
			if (scaleX < scaleY) {
				scaleX = scaleY;
			}
			else {
				scaleY = scaleX;
			}
			break;
		case COM_SC_STRETCH:
			doCenter = true;
			doScale = true;
			scaleX = toWidth / fromWidth;
			scaleY = toHeight / fromHeight;
			break;

	}

	if (doCenter) {
		NodeOperation *first = NULL;
		SocketConnection *c;
		ScaleOperation *scaleOperation = NULL;
		if (doScale) {
			scaleOperation = new ScaleOperation();
			first = scaleOperation;
			SetValueOperation *sxop = new SetValueOperation();
			sxop->setValue(scaleX);
			c = ExecutionSystemHelper::addLink(system->getConnections(), sxop->getOutputSocket(), scaleOperation->getInputSocket(1));
			c->setIgnoreResizeCheck(true);
			SetValueOperation *syop = new SetValueOperation();
			syop->setValue(scaleY);
			c = ExecutionSystemHelper::addLink(system->getConnections(), syop->getOutputSocket(), scaleOperation->getInputSocket(2));
			c->setIgnoreResizeCheck(true);
			system->addOperation(sxop);
			system->addOperation(syop);

			unsigned int resolution[2] = {fromWidth, fromHeight};
			scaleOperation->setResolution(resolution);
			sxop->setResolution(resolution);
			syop->setResolution(resolution);
			system->addOperation(scaleOperation);

			c->setIgnoreResizeCheck(true);
		}

		TranslateOperation *translateOperation = new TranslateOperation();
		if (!first) first = translateOperation;
		SetValueOperation *xop = new SetValueOperation();
		xop->setValue(addX);
		c = ExecutionSystemHelper::addLink(system->getConnections(), xop->getOutputSocket(), translateOperation->getInputSocket(1));
		c->setIgnoreResizeCheck(true);
		SetValueOperation *yop = new SetValueOperation();
		yop->setValue(addY);
		c = ExecutionSystemHelper::addLink(system->getConnections(), yop->getOutputSocket(), translateOperation->getInputSocket(2));
		c->setIgnoreResizeCheck(true);
		system->addOperation(xop);
		system->addOperation(yop);

		unsigned int resolution[2] = {toWidth, toHeight};
		translateOperation->setResolution(resolution);
		xop->setResolution(resolution);
		yop->setResolution(resolution);
		system->addOperation(translateOperation);

		if (doScale) {
			c = ExecutionSystemHelper::addLink(system->getConnections(), scaleOperation->getOutputSocket(), translateOperation->getInputSocket(0));
			c->setIgnoreResizeCheck(true);
		}

		InputSocket *inputSocket = connection->getToSocket();
		inputSocket->relinkConnections(first->getInputSocket(0));
		c = ExecutionSystemHelper::addLink(system->getConnections(), translateOperation->getOutputSocket(), inputSocket);
		c->setIgnoreResizeCheck(true);
	}

	connection->setIgnoreResizeCheck(true);
}
