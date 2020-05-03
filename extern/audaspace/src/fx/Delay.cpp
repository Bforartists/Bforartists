/*******************************************************************************
 * Copyright 2009-2016 Jörg Müller
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

#include "fx/Delay.h"
#include "fx/DelayReader.h"

AUD_NAMESPACE_BEGIN

Delay::Delay(std::shared_ptr<ISound> sound, double delay) :
	Effect(sound),
	m_delay(delay)
{
}

double Delay::getDelay() const
{
	return m_delay;
}

std::shared_ptr<IReader> Delay::createReader()
{
	return std::shared_ptr<IReader>(new DelayReader(getReader(), m_delay));
}

AUD_NAMESPACE_END
