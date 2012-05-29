/*
 * Copyright 2012, Blender Foundation.
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
 *		Sergey Sharybin
 */

#include "COM_KeyingNode.h"

#include "COM_ExecutionSystem.h"

#include "COM_KeyingOperation.h"
#include "COM_KeyingDispillOperation.h"

#include "COM_SeparateChannelOperation.h"
#include "COM_CombineChannelsOperation.h"
#include "COM_ConvertRGBToYCCOperation.h"
#include "COM_ConvertYCCToRGBOperation.h"
#include "COM_FastGaussianBlurOperation.h"
#include "COM_SetValueOperation.h"

#include "COM_DilateErodeOperation.h"

#include "COM_SetAlphaOperation.h"

KeyingNode::KeyingNode(bNode *editorNode): Node(editorNode)
{
}

OutputSocket *KeyingNode::setupPreBlur(ExecutionSystem *graph, InputSocket *inputImage, int size, OutputSocket **originalImage)
{
	memset(&preBlurData, 0, sizeof(preBlurData));
	preBlurData.sizex = size;
	preBlurData.sizey = size;

	ConvertRGBToYCCOperation *convertRGBToYCCOperation = new ConvertRGBToYCCOperation();
	convertRGBToYCCOperation->setMode(0);  /* ITU 601 */

	inputImage->relinkConnections(convertRGBToYCCOperation->getInputSocket(0), 0, graph);
	graph->addOperation(convertRGBToYCCOperation);

	CombineChannelsOperation *combineOperation = new CombineChannelsOperation();
	graph->addOperation(combineOperation);

	for (int channel = 0; channel < 4; channel++) {
		SeparateChannelOperation *separateOperation = new SeparateChannelOperation();
		separateOperation->setChannel(channel);
		addLink(graph, convertRGBToYCCOperation->getOutputSocket(0), separateOperation->getInputSocket(0));
		graph->addOperation(separateOperation);

		if (channel == 0 || channel == 3) {
			addLink(graph, separateOperation->getOutputSocket(0), combineOperation->getInputSocket(channel));
		}
		else {
			SetValueOperation *setValueOperation = new SetValueOperation();
			setValueOperation->setValue(1.0f);
			graph->addOperation(setValueOperation);

			FastGaussianBlurOperation *blurOperation = new FastGaussianBlurOperation();
			blurOperation->setData(&preBlurData);

			addLink(graph, separateOperation->getOutputSocket(0), blurOperation->getInputSocket(0));
			addLink(graph, setValueOperation->getOutputSocket(0), blurOperation->getInputSocket(1));
			addLink(graph, blurOperation->getOutputSocket(0), combineOperation->getInputSocket(channel));
			graph->addOperation(blurOperation);
		}
	}

	ConvertYCCToRGBOperation *convertYCCToRGBOperation = new ConvertYCCToRGBOperation();
	convertYCCToRGBOperation->setMode(0);  /* ITU 601 */
	addLink(graph, combineOperation->getOutputSocket(0), convertYCCToRGBOperation->getInputSocket(0));
	graph->addOperation(convertYCCToRGBOperation);

	*originalImage = convertRGBToYCCOperation->getInputSocket(0)->getConnection()->getFromSocket();

	return convertYCCToRGBOperation->getOutputSocket(0);
}

OutputSocket *KeyingNode::setupPostBlur(ExecutionSystem *graph, OutputSocket *postBLurInput, int size)
{
	memset(&postBlurData, 0, sizeof(postBlurData));

	postBlurData.sizex = size;
	postBlurData.sizey = size;

	SetValueOperation *setValueOperation = new SetValueOperation();

	setValueOperation->setValue(1.0f);
	graph->addOperation(setValueOperation);

	FastGaussianBlurOperation *blurOperation = new FastGaussianBlurOperation();
	blurOperation->setData(&postBlurData);

	addLink(graph, postBLurInput, blurOperation->getInputSocket(0));
	addLink(graph, setValueOperation->getOutputSocket(0), blurOperation->getInputSocket(1));

	graph->addOperation(blurOperation);

	return blurOperation->getOutputSocket();
}

OutputSocket *KeyingNode::setupDilateErode(ExecutionSystem *graph, OutputSocket *dilateErodeInput, int distance)
{
	DilateStepOperation *dilateErodeOperation;

	if (distance > 0) {
		dilateErodeOperation = new DilateStepOperation();
		dilateErodeOperation->setIterations(distance);
	}
	else {
		dilateErodeOperation = new ErodeStepOperation();
		dilateErodeOperation->setIterations(-distance);
	}

	addLink(graph, dilateErodeInput, dilateErodeOperation->getInputSocket(0));

	graph->addOperation(dilateErodeOperation);

	return dilateErodeOperation->getOutputSocket(0);
}

OutputSocket *KeyingNode::setupDispill(ExecutionSystem *graph, OutputSocket *dispillInput, InputSocket *inputScreen, float factor)
{
	KeyingDispillOperation *dispillOperation = new KeyingDispillOperation();

	dispillOperation->setDispillFactor(factor);

	addLink(graph, dispillInput, dispillOperation->getInputSocket(0));
	inputScreen->relinkConnections(dispillOperation->getInputSocket(1), 1, graph);

	graph->addOperation(dispillOperation);

	return dispillOperation->getOutputSocket(0);
}

void KeyingNode::convertToOperations(ExecutionSystem *graph, CompositorContext *context)
{
	InputSocket *inputImage = this->getInputSocket(0);
	InputSocket *inputScreen = this->getInputSocket(1);
	OutputSocket *outputImage = this->getOutputSocket(0);
	OutputSocket *outputMatte = this->getOutputSocket(1);
	OutputSocket *postprocessedMatte, *postprocessedImage, *originalImage;

	bNode *editorNode = this->getbNode();
	NodeKeyingData *keying_data = (NodeKeyingData *) editorNode->storage;

	/* keying operation */
	KeyingOperation *keyingOperation = new KeyingOperation();

	keyingOperation->setClipBlack(keying_data->clip_black);
	keyingOperation->setClipWhite(keying_data->clip_white);

	inputScreen->relinkConnections(keyingOperation->getInputSocket(1), 1, graph);

	if (keying_data->blur_pre) {
		/* chroma preblur operation for input of keying operation  */
		OutputSocket *preBluredImage = setupPreBlur(graph, inputImage, keying_data->blur_pre, &originalImage);
		addLink(graph, preBluredImage, keyingOperation->getInputSocket(0));
	}
	else {
		inputImage->relinkConnections(keyingOperation->getInputSocket(0), 0, graph);
		originalImage = keyingOperation->getInputSocket(0)->getConnection()->getFromSocket();
	}

	graph->addOperation(keyingOperation);

	/* apply blur on matte if needed */
	if (keying_data->blur_post)
		postprocessedMatte = setupPostBlur(graph, keyingOperation->getOutputSocket(), keying_data->blur_post);
	else
		postprocessedMatte = keyingOperation->getOutputSocket();

	/* matte dilate/erode */
	if (keying_data->dilate_distance != 0) {
		postprocessedMatte = setupDilateErode(graph, postprocessedMatte, keying_data->dilate_distance);
	}

	/* set alpha channel to output image */
	SetAlphaOperation *alphaOperation = new SetAlphaOperation();
	addLink(graph, originalImage, alphaOperation->getInputSocket(0));
	addLink(graph, postprocessedMatte, alphaOperation->getInputSocket(1));

	postprocessedImage = alphaOperation->getOutputSocket();

	/* dispill output image */
	if (keying_data->dispill_factor > 0.0f) {
		postprocessedImage = setupDispill(graph, postprocessedImage, inputScreen, keying_data->dispill_factor);
	}

	/* connect result to output sockets */
	outputImage->relinkConnections(postprocessedImage);
	outputMatte->relinkConnections(postprocessedMatte);

	graph->addOperation(alphaOperation);
}
