/*
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * Copyright 2009-2011 Jörg Hermann Müller
 *
 * This file is part of AudaSpace.
 *
 * Audaspace is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * AudaSpace is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Audaspace; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file audaspace/ffmpeg/AUD_FFMPEGWriter.h
 *  \ingroup audffmpeg
 */


#ifndef AUD_FFMPEGWRITER
#define AUD_FFMPEGWRITER

#include "AUD_ConverterFunctions.h"
#include "AUD_Buffer.h"
#include "AUD_IWriter.h"

#include <string>

struct AVCodecContext;
extern "C" {
#include <libavformat/avformat.h>
}

/**
 * This class writes a sound file via ffmpeg.
 */
class AUD_FFMPEGWriter : public AUD_IWriter
{
private:
	/**
	 * The current position in samples.
	 */
	int m_position;

	/**
	 * The specification of the audio data.
	 */
	AUD_DeviceSpecs m_specs;

	/**
	 * The AVFormatContext structure for using ffmpeg.
	 */
	AVFormatContext* m_formatCtx;

	/**
	 * The AVCodecContext structure for using ffmpeg.
	 */
	AVCodecContext* m_codecCtx;

	AVOutputFormat* m_outputFmt;

	AVStream* m_stream;

	AUD_Buffer m_input_buffer;

	AUD_Buffer m_output_buffer;

	unsigned int m_input_samples;

	unsigned int m_input_size;

	/**
	 * Converter function.
	 */
	AUD_convert_f m_convert;

	// hide copy constructor and operator=
	AUD_FFMPEGWriter(const AUD_FFMPEGWriter&);
	AUD_FFMPEGWriter& operator=(const AUD_FFMPEGWriter&);

	void encode(sample_t* data);

public:
	/**
	 * Creates a new writer.
	 * \param filename The path to the file to be read.
	 * \exception AUD_Exception Thrown if the file specified does not exist or
	 *            cannot be read with ffmpeg.
	 */
	AUD_FFMPEGWriter(std::string filename, AUD_DeviceSpecs specs, AUD_Container format, AUD_Codec codec, unsigned int bitrate);

	/**
	 * Destroys the writer and closes the file.
	 */
	virtual ~AUD_FFMPEGWriter();

	virtual int getPosition() const;
	virtual AUD_DeviceSpecs getSpecs() const;
	virtual void write(unsigned int length, sample_t* buffer);
};

#endif //AUD_FFMPEGWRITER
