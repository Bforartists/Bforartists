/* Apache License, Version 2.0 */

#include "testing/testing.h"

extern "C" {
#include "BLI_utildefines.h"
#include "BLI_string.h"
#include "BLI_string_utf8.h"
}

/* -------------------------------------------------------------------- */
/* stubs */

extern "C" {

int mk_wcwidth(wchar_t ucs);
int mk_wcswidth(const wchar_t *pwcs, size_t n);

int mk_wcwidth(wchar_t ucs)
{
	return 0;
}

int mk_wcswidth(const wchar_t *pwcs, size_t n)
{
	return 0;
}

}


/* -------------------------------------------------------------------- */
/* tests */

/* BLI_str_partition */
TEST(string, StrPartition)
{
	const char delim[] = {'-', '.', '_', '~', '\\', '\0'};
	const char *sep, *suf;
	size_t pre_ln;

	{
		const char *str = "mat.e-r_ial";

		/* "mat.e-r_ial" -> "mat", '.', "e-r_ial", 3 */
		pre_ln = BLI_str_partition(str, delim, &sep, &suf);
		EXPECT_EQ(3, pre_ln);
		EXPECT_EQ(&str[3], sep);
		EXPECT_STREQ("e-r_ial", suf);
	}

	/* Corner cases. */
	{
		const char *str = ".mate-rial--";

		/* ".mate-rial--" -> "", '.', "mate-rial--", 0 */
		pre_ln = BLI_str_partition(str, delim, &sep, &suf);
		EXPECT_EQ(0, pre_ln);
		EXPECT_EQ(&str[0], sep);
		EXPECT_STREQ("mate-rial--", suf);
	}

	{
		const char *str = ".__.--_";

		/* ".__.--_" -> "", '.', "__.--_", 0 */
		pre_ln = BLI_str_partition(str, delim, &sep, &suf);
		EXPECT_EQ(0, pre_ln);
		EXPECT_EQ(&str[0], sep);
		EXPECT_STREQ("__.--_", suf);
	}

	{
		const char *str = "";

		/* "" -> "", NULL, NULL, 0 */
		pre_ln = BLI_str_partition(str, delim, &sep, &suf);
		EXPECT_EQ(0, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}

	{
		const char *str = "material";

		/* "material" -> "material", NULL, NULL, 8 */
		pre_ln = BLI_str_partition(str, delim, &sep, &suf);
		EXPECT_EQ(8, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}
}

/* BLI_str_rpartition */
TEST(string, StrRPartition)
{
	const char delim[] = {'-', '.', '_', '~', '\\', '\0'};
	const char *sep, *suf;
	size_t pre_ln;

	{
		const char *str = "mat.e-r_ial";

		/* "mat.e-r_ial" -> "mat.e-r", '_', "ial", 7 */
		pre_ln = BLI_str_rpartition(str, delim, &sep, &suf);
		EXPECT_EQ(7, pre_ln);
		EXPECT_EQ(&str[7], sep);
		EXPECT_STREQ("ial", suf);
	}

	/* Corner cases. */
	{
		const char *str = ".mate-rial--";

		/* ".mate-rial--" -> ".mate-rial-", '-', "", 11 */
		pre_ln = BLI_str_rpartition(str, delim, &sep, &suf);
		EXPECT_EQ(11, pre_ln);
		EXPECT_EQ(&str[11], sep);
		EXPECT_STREQ("", suf);
	}

	{
		const char *str = ".__.--_";

		/* ".__.--_" -> ".__.--", '_', "", 6 */
		pre_ln = BLI_str_rpartition(str, delim, &sep, &suf);
		EXPECT_EQ(6, pre_ln);
		EXPECT_EQ(&str[6], sep);
		EXPECT_STREQ("", suf);
	}

	{
		const char *str = "";

		/* "" -> "", NULL, NULL, 0 */
		pre_ln = BLI_str_rpartition(str, delim, &sep, &suf);
		EXPECT_EQ(0, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}

	{
		const char *str = "material";

		/* "material" -> "material", NULL, NULL, 8 */
		pre_ln = BLI_str_rpartition(str, delim, &sep, &suf);
		EXPECT_EQ(8, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}
}

/* BLI_str_partition_ex */
TEST(string, StrPartitionEx)
{
	const char delim[] = {'-', '.', '_', '~', '\\', '\0'};
	const char *sep, *suf;
	size_t pre_ln;

	/* Only considering 'from_right' cases here. */

	{
		const char *str = "mat.e-r_ia.l";

		/* "mat.e-r_ia.l" over "mat.e-r" -> "mat.e", '.', "r_ia.l", 3 */
		pre_ln = BLI_str_partition_ex(str, str + 6, delim, &sep, &suf, true);
		EXPECT_EQ(5, pre_ln);
		EXPECT_EQ(&str[5], sep);
		EXPECT_STREQ("r_ia.l", suf);
	}

	/* Corner cases. */
	{
		const char *str = "mate.rial";

		/* "mate.rial" over "mate" -> "mate.rial", NULL, NULL, 4 */
		pre_ln = BLI_str_partition_ex(str, str + 4, delim, &sep, &suf, true);
		EXPECT_EQ(4, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}
}

/* BLI_str_partition_utf8 */
TEST(string, StrPartitionUtf8)
{
	const unsigned int delim[] = {'-', '.', '_', 0x00F1 /* n tilde */, 0x262F /* ying-yang */, '\0'};
	const char *sep, *suf;
	size_t pre_ln;

	{
		const char *str = "ma\xc3\xb1te-r\xe2\x98\xafial";

		/* "ma\xc3\xb1te-r\xe2\x98\xafial" -> "ma", '\xc3\xb1', "te-r\xe2\x98\xafial", 2 */
		pre_ln = BLI_str_partition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(2, pre_ln);
		EXPECT_EQ(&str[2], sep);
		EXPECT_STREQ("te-r\xe2\x98\xafial", suf);
	}

	/* Corner cases. */
	{
		const char *str = "\xe2\x98\xafmate-rial-\xc3\xb1";

		/* "\xe2\x98\xafmate-rial-\xc3\xb1" -> "", '\xe2\x98\xaf', "mate-rial-\xc3\xb1", 0 */
		pre_ln = BLI_str_partition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(0, pre_ln);
		EXPECT_EQ(&str[0], sep);
		EXPECT_STREQ("mate-rial-\xc3\xb1", suf);
	}

	{
		const char *str = "\xe2\x98\xaf.\xc3\xb1_.--\xc3\xb1";

		/* "\xe2\x98\xaf.\xc3\xb1_.--\xc3\xb1" -> "", '\xe2\x98\xaf', ".\xc3\xb1_.--\xc3\xb1", 0 */
		pre_ln = BLI_str_partition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(0, pre_ln);
		EXPECT_EQ(&str[0], sep);
		EXPECT_STREQ(".\xc3\xb1_.--\xc3\xb1", suf);
	}

	{
		const char *str = "";

		/* "" -> "", NULL, NULL, 0 */
		pre_ln = BLI_str_partition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(0, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}

	{
		const char *str = "material";

		/* "material" -> "material", NULL, NULL, 8 */
		pre_ln = BLI_str_partition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(8, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}
}

/* BLI_str_rpartition_utf8 */
TEST(string, StrRPartitionUtf8)
{
	const unsigned int delim[] = {'-', '.', '_', 0x00F1 /* n tilde */, 0x262F /* ying-yang */, '\0'};
	const char *sep, *suf;
	size_t pre_ln;

	{
		const char *str = "ma\xc3\xb1te-r\xe2\x98\xafial";

		/* "ma\xc3\xb1te-r\xe2\x98\xafial" -> "mat\xc3\xb1te-r", '\xe2\x98\xaf', "ial", 8 */
		pre_ln = BLI_str_rpartition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(8, pre_ln);
		EXPECT_EQ(&str[8], sep);
		EXPECT_STREQ("ial", suf);
	}

	/* Corner cases. */
	{
		const char *str = "\xe2\x98\xafmate-rial-\xc3\xb1";

		/* "\xe2\x98\xafmate-rial-\xc3\xb1" -> "\xe2\x98\xafmate-rial-", '\xc3\xb1', "", 13 */
		pre_ln = BLI_str_rpartition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(13, pre_ln);
		EXPECT_EQ(&str[13], sep);
		EXPECT_STREQ("", suf);
	}

	{
		const char *str = "\xe2\x98\xaf.\xc3\xb1_.--\xc3\xb1";

		/* "\xe2\x98\xaf.\xc3\xb1_.--\xc3\xb1" -> "\xe2\x98\xaf.\xc3\xb1_.--", '\xc3\xb1', "", 10 */
		pre_ln = BLI_str_rpartition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(10, pre_ln);
		EXPECT_EQ(&str[10], sep);
		EXPECT_STREQ("", suf);
	}

	{
		const char *str = "";

		/* "" -> "", NULL, NULL, 0 */
		pre_ln = BLI_str_rpartition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(0, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}

	{
		const char *str = "material";

		/* "material" -> "material", NULL, NULL, 8 */
		pre_ln = BLI_str_rpartition_utf8(str, delim, &sep, &suf);
		EXPECT_EQ(8, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}
}

/* BLI_str_partition_ex_utf8 */
TEST(string, StrPartitionExUtf8)
{
	const unsigned int delim[] = {'-', '.', '_', 0x00F1 /* n tilde */, 0x262F /* ying-yang */, '\0'};
	const char *sep, *suf;
	size_t pre_ln;

	/* Only considering 'from_right' cases here. */

	{
		const char *str = "ma\xc3\xb1te-r\xe2\x98\xafial";

		/* "ma\xc3\xb1te-r\xe2\x98\xafial" over "ma\xc3\xb1te" -> "ma", '\xc3\xb1', "te-r\xe2\x98\xafial", 2 */
		pre_ln = BLI_str_partition_ex_utf8(str, str + 6, delim, &sep, &suf, true);
		EXPECT_EQ(2, pre_ln);
		EXPECT_EQ(&str[2], sep);
		EXPECT_STREQ("te-r\xe2\x98\xafial", suf);
	}

	/* Corner cases. */
	{
		const char *str = "mate\xe2\x98\xafrial";

		/* "mate\xe2\x98\xafrial" over "mate" -> "mate\xe2\x98\xafrial", NULL, NULL, 4 */
		pre_ln = BLI_str_partition_ex_utf8(str, str + 4, delim, &sep, &suf, true);
		EXPECT_EQ(4, pre_ln);
		EXPECT_EQ(NULL, sep);
		EXPECT_EQ(NULL, suf);
	}
}

/* BLI_str_format_int_grouped */
TEST(string, StrFormatIntGrouped)
{
	char num_str[16];
	int num;

	BLI_str_format_int_grouped(num_str, num = 0);
	EXPECT_STREQ("0", num_str);

	BLI_str_format_int_grouped(num_str, num = 1);
	EXPECT_STREQ("1", num_str);

	BLI_str_format_int_grouped(num_str, num = -1);
	EXPECT_STREQ("-1", num_str);

	BLI_str_format_int_grouped(num_str, num = -2147483648);
	EXPECT_STREQ("-2,147,483,648", num_str);

	BLI_str_format_int_grouped(num_str, num = 2147483647);
	EXPECT_STREQ("2,147,483,647", num_str);

	BLI_str_format_int_grouped(num_str, num = 1000);
	EXPECT_STREQ("1,000", num_str);

	BLI_str_format_int_grouped(num_str, num = -1000);
	EXPECT_STREQ("-1,000", num_str);

	BLI_str_format_int_grouped(num_str, num = 999);
	EXPECT_STREQ("999", num_str);

	BLI_str_format_int_grouped(num_str, num = -999);
	EXPECT_STREQ("-999", num_str);
}
