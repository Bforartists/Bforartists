/*
 * Copyright 2011-2016 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "testing/testing.h"

#include "util/util_string.h"

CCL_NAMESPACE_BEGIN

/* ******** Tests for string_printf() ******** */

TEST(util_string_printf, no_format)
{
	string str = string_printf("foo bar");
	EXPECT_EQ(str, "foo bar");
}

TEST(util_string_printf, int_number)
{
	string str = string_printf("foo %d bar", 314);
	EXPECT_EQ(str, "foo 314 bar");
}

TEST(util_string_printf, float_number_default_precision)
{
	string str = string_printf("foo %f bar", 3.1415);
	EXPECT_EQ(str, "foo 3.141500 bar");
}

TEST(util_string_printf, float_number_custom_precision)
{
	string str = string_printf("foo %.1f bar", 3.1415);
	EXPECT_EQ(str, "foo 3.1 bar");
}

/* ******** Tests for string_printf() ******** */

TEST(util_string_iequals, empty_a)
{
	bool equals = string_iequals("", "foo");
	EXPECT_FALSE(equals);
}

TEST(util_string_iequals, empty_b)
{
	bool equals = string_iequals("foo", "");
	EXPECT_FALSE(equals);
}

TEST(util_string_iequals, same_register)
{
	bool equals = string_iequals("foo", "foo");
	EXPECT_TRUE(equals);
}

TEST(util_string_iequals, different_register)
{
	bool equals = string_iequals("XFoo", "XfoO");
	EXPECT_TRUE(equals);
}

/* ******** Tests for string_split() ******** */

TEST(util_string_split, empty)
{
	vector<string> tokens;
	string_split(tokens, "");
	EXPECT_EQ(0, tokens.size());
}

TEST(util_string_split, only_spaces)
{
	vector<string> tokens;
	string_split(tokens, "   \t\t \t");
	EXPECT_EQ(0, tokens.size());
}

TEST(util_string_split, single)
{
	vector<string> tokens;
	string_split(tokens, "foo");
	EXPECT_EQ(1, tokens.size());
	EXPECT_EQ("foo", tokens[0]);
}

TEST(util_string_split, simple)
{
	vector<string> tokens;
	string_split(tokens, "foo a bar b");
	EXPECT_EQ(4, tokens.size());
	EXPECT_EQ("foo", tokens[0]);
	EXPECT_EQ("a", tokens[1]);
	EXPECT_EQ("bar", tokens[2]);
	EXPECT_EQ("b", tokens[3]);
}

TEST(util_string_split, multiple_spaces)
{
	vector<string> tokens;
	string_split(tokens, " \t foo \ta bar b\t  ");
	EXPECT_EQ(4, tokens.size());
	EXPECT_EQ("foo", tokens[0]);
	EXPECT_EQ("a", tokens[1]);
	EXPECT_EQ("bar", tokens[2]);
	EXPECT_EQ("b", tokens[3]);
}

/* ******** Tests for string_replace() ******** */

TEST(util_string_replace, empty_haystack_and_other)
{
	string str = "";
	string_replace(str, "x", "");
	EXPECT_EQ("", str);
}

TEST(util_string_replace, empty_haystack)
{
	string str = "";
	string_replace(str, "x", "y");
	EXPECT_EQ("", str);
}

TEST(util_string_replace, empty_other)
{
	string str = "x";
	string_replace(str, "x", "");
	EXPECT_EQ("", str);
}

TEST(util_string_replace, long_haystack_empty_other)
{
	string str = "a x b xxc";
	string_replace(str, "x", "");
	EXPECT_EQ("a  b c", str);
}

TEST(util_string_replace, long_haystack)
{
	string str = "a x b xxc";
	string_replace(str, "x", "FOO");
	EXPECT_EQ("a FOO b FOOFOOc", str);
}

/* ******** Tests for string_endswith() ******** */

TEST(util_string_endswith, empty_both)
{
	bool endswith = string_endswith("", "");
	EXPECT_TRUE(endswith);
}

TEST(util_string_endswith, empty_string)
{
	bool endswith = string_endswith("", "foo");
	EXPECT_FALSE(endswith);
}

TEST(util_string_endswith, empty_end)
{
	bool endswith = string_endswith("foo", "");
	EXPECT_TRUE(endswith);
}

TEST(util_string_endswith, simple_true)
{
	bool endswith = string_endswith("foo bar", "bar");
	EXPECT_TRUE(endswith);
}

TEST(util_string_endswith, simple_false)
{
	bool endswith = string_endswith("foo bar", "foo");
	EXPECT_FALSE(endswith);
}

/* ******** Tests for string_strip() ******** */

TEST(util_string_strip, empty)
{
	string str = string_strip("");
	EXPECT_EQ("", str);
}

TEST(util_string_strip, only_spaces)
{
	string str = string_strip("      ");
	EXPECT_EQ("", str);
}

TEST(util_string_strip, no_spaces)
{
	string str = string_strip("foo bar");
	EXPECT_EQ("foo bar", str);
}

TEST(util_string_strip, with_spaces)
{
	string str = string_strip("    foo bar ");
	EXPECT_EQ("foo bar", str);
}

/* ******** Tests for string_remove_trademark() ******** */

TEST(util_string_remove_trademark, empty)
{
	string str = string_remove_trademark("");
	EXPECT_EQ("", str);
}

TEST(util_string_remove_trademark, no_trademark)
{
	string str = string_remove_trademark("foo bar");
	EXPECT_EQ("foo bar", str);
}

TEST(util_string_remove_trademark, only_tm)
{
	string str = string_remove_trademark("foo bar(TM) zzz");
	EXPECT_EQ("foo bar zzz", str);
}

TEST(util_string_remove_trademark, only_r)
{
	string str = string_remove_trademark("foo bar(R) zzz");
	EXPECT_EQ("foo bar zzz", str);
}

TEST(util_string_remove_trademark, both)
{
	string str = string_remove_trademark("foo bar(TM)(R) zzz");
	EXPECT_EQ("foo bar zzz", str);
}

CCL_NAMESPACE_END
