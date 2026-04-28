/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 * SPDX-FileCopyrightText: 2002-2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup DNA
 *
 * \brief Struct parser for generating SDNA.
 *
 * \section aboutmakesdnac About makesdna tool
 *
 * `makesdna` creates a `.c` file with a long string of numbers that
 * encode the Blender file format. It is fast, because it is basically
 * a binary dump. There are some details to mind when reconstructing
 * the file (endianness and byte-alignment).
 *
 * This little program scans all structs that need to be serialized,
 * and determined the names and types of all members. It calculates
 * how much memory (on disk or in ram) is needed to store that struct,
 * and the offsets for reaching a particular one.
 *
 * There is a facility to get verbose output from `sdna`. Search for
 * \ref debugSDNA. This int can be set to 0 (no output) to some int.
 * Higher numbers give more output.
 */

#define DNA_DEPRECATED_ALLOW

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "MEM_guardedalloc.h"

#include "BLI_ghash.h"
#include "BLI_memarena.h"
#include "BLI_set.hh"
#include "BLI_string_ref.hh"
#include "BLI_sys_types.h" /* For `intptr_t` support. */
#include "BLI_system.h"    /* For #BLI_system_backtrace stub. */
#include "BLI_utildefines.h"
#include "BLI_vector.hh"

#include "DNA_sdna_types.h"
#include "dna_parse.h"
#include "dna_utils.h"

namespace blender {

/* The include files that are needed to generate full Blender DNA.
 *
 * The include file below is automatically generated from the `SRC_DNA_INC`
 * variable in `source/blender/CMakeLists.txt`. */

static const char *blender_includefiles[] = {
#include "dna_includes_as_strings.h"

    /* Empty string to indicate end of include files. */
    "",
};

/* Include files that will be used to generate makesdna output.
 * By default, they match the blender_includefiles, but could be overridden via a command line
 * argument for the purposes of regression testing. */
static const char **includefiles = blender_includefiles;

/* -------------------------------------------------------------------- */
/** \name Variables
 * \{ */

static MemArena *mem_arena = nullptr;

static int max_data_size = 500000, max_array_len = 50000;
static int members_num = 0;
static int types_num = 0;
static int structs_num = 0;
/** At address `members[a]` is string `a`. */
static char **members;
/** At address `types[a]` is string `a`. */
static char **types;
/** At `types_size[a]` is the size of type `a` on this systems bitness (32 or 64). */
static short *types_size_native;
/** Contains align requirements for a struct on 32 bit systems. */
static short *types_align_32;
/** Contains align requirements for a struct on 64 bit systems. */
static short *types_align_64;
/** Contains sizes as they are calculated on 32 bit systems. */
static short *types_size_32;
/** Contains sizes as they are calculated on 64 bit systems. */
static short *types_size_64;
/**
 * At `sp = structs[a]` is the first address of a struct definition:
 * - `sp[0]` is type index.
 * - `sp[1]` is the length of the member array (next).
 * - `sp[2]` sp[3] is [(type_index, member_index), ..] (number of pairs is defined by `sp[1]`),
 */
static short **structs, *structdata;
/**
 * Optional alignment requirement for struct members, to override the standard
 * alignment of the type. Indexed by the same offset as #structdata.
 */
static short *structdata_alignment;

/** Versioning data */
static struct {
  GHash *type_map_alias_from_static;
  GHash *type_map_static_from_alias;
  GHash *member_map_alias_from_static;
  GHash *member_map_static_from_alias;
} g_version_data = {nullptr};

/**
 * Variable to control debug output of makesdna.
 * debugSDNA:
 * - 0 = no output, except errors
 * - 1 = detail actions
 * - 2 = full trace, tell which names and types were found
 * - 4 = full trace, plus all gritty details
 */
int debugSDNA = 0;

#define DEBUG_PRINTF(debug_level, ...) \
  { \
    if (debugSDNA > debug_level) { \
      printf(__VA_ARGS__); \
    } \
  } \
  ((void)0)

/* stub for BLI_abort() */
#ifndef NDEBUG
void BLI_system_backtrace(FILE *fp)
{
  (void)fp;
}
#endif

/** \} */

/* -------------------------------------------------------------------- */
/** \name Function Declarations
 * \{ */

/**
 * Ensure that type \a type_name is in the #types array.
 * \param type_name: Struct name without any qualifiers.
 * \param size: The struct size in bytes.
 * \return Index in the #types array.
 */
static int add_type(StringRefNull type_name, int size);

/**
 * Ensure that \a member_name is in the #members array.
 * \param member_name: Full struct member name (may include pointer prefix & array size).
 * \return Index in the #members array.
 */
static int add_member(StringRefNull member_name);

/**
 * Add a new structure definition, of type matching the given \a type_index.
 *
 * NOTE: there is no lookup performed here, a new struct definition is always added.
 */
static short *add_struct(int type_index);

/**
 * Determine how many bytes are needed for each struct.
 */
static int calculate_struct_sizes(int firststruct, FILE *file_verify, const char *base_directory);

/**
 * Construct the DNA.c file
 */
static void dna_write(FILE *file, const void *pntr, const int size);

/**
 * Report all structures found so far, and print their lengths.
 */
void print_struct_sizes();

/** \} */

/* -------------------------------------------------------------------- */
/** \name Implementation
 *
 * Make DNA string (write to file).
 * \{ */

static const char *version_struct_static_from_alias(const char *type_alias)
{
  const char *type_static = static_cast<const char *>(
      BLI_ghash_lookup(g_version_data.type_map_static_from_alias, type_alias));
  if (type_static != nullptr) {
    return type_static;
  }
  return type_alias;
}

static const char *version_struct_alias_from_static(const char *type_static)
{
  const char *type_alias = static_cast<const char *>(
      BLI_ghash_lookup(g_version_data.type_map_alias_from_static, type_static));
  if (type_alias != nullptr) {
    return type_alias;
  }
  return type_static;
}

static const char *version_member_static_from_alias(const int type_index,
                                                    const char *member_alias_full)
{
  const uint member_alias_full_len = strlen(member_alias_full);
  std::string member_alias_storage(member_alias_full_len + 1, '\0');
  char *member_alias = member_alias_storage.data();
  const int member_alias_len = DNA_member_id_strip_copy(member_alias, member_alias_full);
  const char *str_pair[2] = {types[type_index], member_alias};
  const char *member_static = static_cast<const char *>(
      BLI_ghash_lookup(g_version_data.member_map_static_from_alias, str_pair));
  if (member_static != nullptr) {
    return DNA_member_id_rename(mem_arena,
                                member_alias,
                                member_alias_len,
                                member_static,
                                strlen(member_static),
                                member_alias_full,
                                member_alias_full_len,
                                DNA_member_id_offset_start(member_alias_full));
  }
  return member_alias_full;
}

static int add_type(const StringRefNull type_name_input, const int size)
{
  const char *type_name = version_struct_static_from_alias(type_name_input.c_str());

  /* search through type array */
  for (int type_index = 0; type_index < types_num; type_index++) {
    if (STREQ(type_name, types[type_index])) {
      if (size) {
        types_size_native[type_index] = size;
        types_size_32[type_index] = size;
        types_size_64[type_index] = size;
        types_align_32[type_index] = size;
        types_align_64[type_index] = size;
      }
      return type_index;
    }
  }

  /* append new type */
  const size_t type_name_len = strlen(type_name);
  char *cp = static_cast<char *>(BLI_memarena_alloc(mem_arena, type_name_len + 1));
  std::copy_n(type_name, type_name_len + 1, cp);
  types[types_num] = cp;
  types_size_native[types_num] = size;
  types_size_32[types_num] = size;
  types_size_64[types_num] = size;
  types_align_32[types_num] = size;
  types_align_64[types_num] = size;
  if (types_num >= max_array_len) {
    printf("too many types\n");
    return types_num - 1;
  }
  types_num++;

  return types_num - 1;
}

/**
 * Add a member to the members table. The name is expected to already be in canonical
 * form (function pointers rewritten as `(*name)()`, `(*name)(void)`, and name validate
 * already checked by the parser).
 */
static int add_member(const StringRefNull member_name)
{
  /* search name array */
  for (int member_index = 0; member_index < members_num; member_index++) {
    if (member_name == members[member_index]) {
      return member_index;
    }
  }

  /* Append new name. */
  const size_t name_len = member_name.size();
  char *cp = static_cast<char *>(BLI_memarena_alloc(mem_arena, name_len + 1));
  std::copy_n(member_name.c_str(), name_len + 1, cp);
  members[members_num] = cp;

  if (members_num >= max_array_len) {
    printf("too many names\n");
    return members_num - 1;
  }
  members_num++;

  return members_num - 1;
}

static short *add_struct(int type_index)
{
  if (structs_num == 0) {
    structs[0] = structdata;
  }
  else {
    short *sp = structs[structs_num - 1];
    const int len = sp[1];
    structs[structs_num] = sp + 2 * len + 2;
  }

  short *sp = structs[structs_num];
  sp[0] = type_index;

  if (structs_num >= max_array_len) {
    printf("too many structs\n");
    return sp;
  }
  structs_num++;

  return sp;
}

static bool check_field_alignment(int firststruct,
                                  int struct_type_index,
                                  int type,
                                  int len,
                                  int member_align_override,
                                  const char *name,
                                  const char *detail)
{
  bool result = true;
  if (member_align_override > 0 && (len % member_align_override)) {
    fprintf(stderr,
            "Align %d error (%s) in struct: %s %s (add %d padding bytes)\n",
            member_align_override,
            detail,
            types[struct_type_index],
            name,
            member_align_override - (len % member_align_override));
    result = false;
  }
  if (type < firststruct && types_size_native[type] > 4 && (len % 8)) {
    fprintf(stderr,
            "Align 8 error (%s) in struct: %s %s (add %d padding bytes)\n",
            detail,
            types[struct_type_index],
            name,
            len % 8);
    result = false;
  }
  if (types_size_native[type] > 3 && (len % 4)) {
    fprintf(stderr,
            "Align 4 error (%s) in struct: %s %s (add %d padding bytes)\n",
            detail,
            types[struct_type_index],
            name,
            len % 4);
    result = false;
  }
  if (types_size_native[type] == 2 && (len % 2)) {
    fprintf(stderr,
            "Align 2 error (%s) in struct: %s %s (add %d padding bytes)\n",
            detail,
            types[struct_type_index],
            name,
            len % 2);
    result = false;
  }
  return result;
}

static int calculate_struct_sizes(int firststruct, FILE *file_verify, const char *base_directory)
{
  bool dna_error = false;

  /* Write test to verify sizes are accurate. */
  fprintf(file_verify, "/* Verify struct sizes and member offsets are as expected by DNA. */\n");
  fprintf(file_verify, "#include \"BLI_assert.h\"\n\n");
  /* Needed so we can find offsets of deprecated structs. */
  fprintf(file_verify, "#define DNA_DEPRECATED_ALLOW\n");
  /* Workaround enum naming collision in static asserts
   * (ideally this included a unique name/id per file). */
  fprintf(file_verify, "#define assert_line_ assert_line_DNA_\n");
  for (int i = 0; *(includefiles[i]) != '\0'; i++) {
    fprintf(file_verify, "#include \"%s%s\"\n", base_directory, includefiles[i]);
  }
  fprintf(file_verify, "#undef assert_line_\n");
  fprintf(file_verify, "\n");
  fprintf(file_verify, "using namespace blender;\n");
  fprintf(file_verify, "\n");

  /* Multiple iterations to handle nested structs. */
  /* 'raw data' SDNA_RAW_DATA_STRUCT_INDEX fake struct should be ignored here. */
  int unknown = structs_num - 1;
  while (unknown) {
    const int lastunknown = unknown;
    unknown = 0;

    /* check all structs... */
    BLI_STATIC_ASSERT(SDNA_RAW_DATA_STRUCT_INDEX == 0, "'raw data' SDNA struct index should be 0")
    for (int a = SDNA_RAW_DATA_STRUCT_INDEX + 1; a < structs_num; a++) {
      const short *structpoin = structs[a];
      const int struct_type_index = structpoin[0];
      const char *struct_type_name = version_struct_alias_from_static(types[struct_type_index]);

      /* when length is not known... */
      if (types_size_native[struct_type_index] == 0) {

        const short *sp = structpoin + 2;
        int size_native = 0;
        int size_32 = 0;
        int size_64 = 0;
        /* Sizes of the largest field in a struct. */
        int max_align_32 = 0;
        int max_align_64 = 0;

        /* check all members in struct */
        for (int b = 0; b < structpoin[1]; b++, sp += 2) {
          int type = sp[0];
          const char *cp = members[sp[1]];
          int namelen = int(strlen(cp));

          /* Write size verification to file. */
          {
            /* Normally `alloca` would be used here, however we can't in a loop.
             * Use an over-sized buffer instead. */
            char name_static[1024];
            BLI_assert(sizeof(name_static) > namelen);

            DNA_member_id_strip_copy(name_static, cp);
            const char *str_pair[2] = {types[struct_type_index], name_static};
            const char *name_alias = static_cast<const char *>(
                BLI_ghash_lookup(g_version_data.member_map_alias_from_static, str_pair));
            fprintf(file_verify,
                    "BLI_STATIC_ASSERT(offsetof(struct %s, %s) == %d, \"DNA member offset "
                    "verify\");\n",
                    struct_type_name,
                    name_alias ? name_alias : name_static,
                    size_native);
          }

          /* is it a pointer or function pointer? */
          if (cp[0] == '*' || cp[1] == '*') {
            /* has the name an extra length? (array) */
            int mul = 1;
            if (cp[namelen - 1] == ']') {
              mul = DNA_member_array_num(cp);
            }

            if (mul == 0) {
              fprintf(stderr,
                      "Zero array size found or could not parse %s: '%.*s'\n",
                      types[struct_type_index],
                      namelen + 1,
                      cp);
              dna_error = true;
            }

            /* 4-8 aligned/ */
            if (sizeof(void *) == 4) {
              if (size_native % 4) {
                fprintf(stderr,
                        "Align pointer error in struct (size_native 4): %s %s\n",
                        types[struct_type_index],
                        cp);
                dna_error = true;
              }
            }
            else {
              if (size_native % 8) {
                fprintf(stderr,
                        "Align pointer error in struct (size_native 8): %s %s\n",
                        types[struct_type_index],
                        cp);
                dna_error = true;
              }
            }

            if (size_64 % 8) {
              fprintf(stderr,
                      "Align pointer error in struct (size_64 8): %s %s\n",
                      types[struct_type_index],
                      cp);
              dna_error = true;
            }

            size_native += sizeof(void *) * mul;
            size_32 += 4 * mul;
            size_64 += 8 * mul;
            max_align_32 = std::max(max_align_32, 4);
            max_align_64 = std::max(max_align_64, 8);
          }
          else if (cp[0] == '[') {
            /* parsing can cause names "var" and "[3]"
             * to be found for "float var [3]" */
            fprintf(stderr,
                    "Parse error in struct, invalid member name: %s %s\n",
                    types[struct_type_index],
                    cp);
            dna_error = true;
          }
          else if (types_size_native[type]) {
            /* has the name an extra length? (array) */
            int mul = 1;
            if (cp[namelen - 1] == ']') {
              mul = DNA_member_array_num(cp);
            }

            if (mul == 0) {
              fprintf(stderr,
                      "Zero array size found or could not parse %s: '%.*s'\n",
                      types[struct_type_index],
                      namelen + 1,
                      cp);
              dna_error = true;
            }

            /* struct alignment */
            if (type >= firststruct) {
              if (sizeof(void *) == 8 && (size_native % 8)) {
                fprintf(stderr,
                        "Align struct error: %s::%s (starts at %d on the native platform; "
                        "%d %% %zu = %d bytes)\n",
                        types[struct_type_index],
                        cp,
                        size_native,
                        size_native,
                        sizeof(void *),
                        size_native % 8);
                dna_error = true;
              }
            }

            /* Per-member C++ alignment override from the parser. */
            const int member_align = structdata_alignment[sp - structdata];

            /* Check 2-4-8 aligned, plus any stricter C++ alignment. */
            if (!check_field_alignment(
                    firststruct, struct_type_index, type, size_32, member_align, cp, "32 bit"))
            {
              dna_error = true;
            }
            if (!check_field_alignment(
                    firststruct, struct_type_index, type, size_64, member_align, cp, "64 bit"))
            {
              dna_error = true;
            }

            size_native += mul * types_size_native[type];
            size_32 += mul * types_size_32[type];
            size_64 += mul * types_size_64[type];
            max_align_32 = std::max<int>(max_align_32, types_align_32[type]);
            max_align_64 = std::max<int>(max_align_64, types_align_64[type]);
            max_align_32 = std::max<int>(max_align_32, member_align);
            max_align_64 = std::max<int>(max_align_64, member_align);
          }
          else {
            size_native = 0;
            size_32 = 0;
            size_64 = 0;
            break;
          }
        }

        if (size_native == 0) {
          unknown++;
        }
        else {
          types_size_native[struct_type_index] = size_native;
          types_size_32[struct_type_index] = size_32;
          types_size_64[struct_type_index] = size_64;
          types_align_32[struct_type_index] = max_align_32;
          types_align_64[struct_type_index] = max_align_64;

          /* Sanity check 1: alignment should never be 0. */
          BLI_assert(max_align_32);
          BLI_assert(max_align_64);

          /* Sanity check 2: alignment should always be equal or smaller than the maximum
           * alignment we support. 8 bytes for built-in types (e.g. `int64_t`, `double`),
           * up to 16 bytes for C++ over-aligned types like `float4x4`. */
          BLI_assert(max_align_32 <= 16);
          BLI_assert(max_align_64 <= 16);

          if (size_32 % max_align_32) {
            /* There is an one odd case where only the 32 bit struct has alignment issues
             * and the 64 bit does not, that can only be fixed by adding a padding pointer
             * to the struct to resolve the problem. */
            if ((size_64 % max_align_64 == 0) && (size_32 % max_align_32 == 4)) {
              fprintf(stderr,
                      "Sizeerror in 32 bit struct: %s (add padding pointer)\n",
                      types[struct_type_index]);
            }
            else {
              fprintf(stderr,
                      "Sizeerror in 32 bit struct: %s (add %d bytes)\n",
                      types[struct_type_index],
                      max_align_32 - (size_32 % max_align_32));
            }
            dna_error = true;
          }

          if (size_64 % max_align_64) {
            fprintf(stderr,
                    "Sizeerror in 64 bit struct: %s (add %d bytes)\n",
                    types[struct_type_index],
                    max_align_64 - (size_64 % max_align_64));
            dna_error = true;
          }

          if (size_native % 4 && !ELEM(size_native, 1, 2)) {
            fprintf(stderr,
                    "Sizeerror 4 in struct: %s (add %d bytes)\n",
                    types[struct_type_index],
                    size_native % 4);
            dna_error = true;
          }

          /* Write size verification to file. */
          fprintf(file_verify,
                  "BLI_STATIC_ASSERT(sizeof(struct %s) == %d, \"DNA struct size verify\");\n\n",
                  struct_type_name,
                  size_native);
        }
      }
    }

    if (unknown == lastunknown) {
      break;
    }
  }

  if (unknown) {
    fprintf(stderr, "ERROR: still %d structs unknown\n", unknown);

    if (debugSDNA) {
      fprintf(stderr, "*** Known structs :\n");

      for (int a = 0; a < structs_num; a++) {
        const short *structpoin = structs[a];
        const int structtype = structpoin[0];

        /* length unknown */
        if (types_size_native[structtype] != 0) {
          fprintf(stderr, "  %s\n", types[structtype]);
        }
      }
    }

    fprintf(stderr, "*** Unknown structs :\n");

    for (int a = 0; a < structs_num; a++) {
      const short *structpoin = structs[a];
      const int structtype = structpoin[0];

      /* length unknown yet */
      if (types_size_native[structtype] == 0) {
        fprintf(stderr, "  %s\n", types[structtype]);
      }
    }

    dna_error = true;
  }

  return dna_error;
}

#define MAX_DNA_LINE_LENGTH 20

static void dna_write(FILE *file, const void *pntr, const int size)
{
  static int linelength = 0;
  const char *data = static_cast<const char *>(pntr);

  for (int i = 0; i < size; i++) {
    fprintf(file, "%d, ", data[i]);
    linelength++;
    if (linelength >= MAX_DNA_LINE_LENGTH) {
      fprintf(file, "\n");
      linelength = 0;
    }
  }
}

void print_struct_sizes()
{
  int unknown = structs_num;
  printf("\n\n*** All detected structs:\n");

  while (unknown) {
    unknown = 0;

    /* check all structs... */
    for (int a = 0; a < structs_num; a++) {
      const short *structpoin = structs[a];
      const int structtype = structpoin[0];
      printf("\t%s\t:%d\n", types[structtype], types_size_native[structtype]);
    }
  }

  printf("*** End of list\n");
}

/** Register parsed structs, types, and members into the SDNA tables. */
static void register_parsed_structs(const Span<dna::ParsedStruct> parsed_structs)
{
  for (const dna::ParsedStruct &parsed_struct : parsed_structs) {
    const int struct_type_index = add_type(parsed_struct.type_name, 0);
    short *structpoin = add_struct(struct_type_index);
    short *sp = structpoin + 2;

    for (const dna::ParsedMember &parsed_member : parsed_struct.members) {
      const int member_type_index = add_type(parsed_member.type_name, 0);
      const char *versioned_name = version_member_static_from_alias(
          struct_type_index, parsed_member.member_name.c_str());
      const int name = add_member(versioned_name);

      sp[0] = member_type_index;
      sp[1] = name;
      structdata_alignment[sp - structdata] = short(parsed_member.alignment);
      structpoin[1]++;
      sp += 2;
    }
  }
}

static int make_structDNA(const char *base_directory,
                          FILE *file,
                          FILE *file_offsets,
                          FILE *file_verify,
                          FILE *file_ids,
                          FILE *file_defaults)
{
  if (debugSDNA > 0) {
    fflush(stdout);
    printf("Running makesdna at debug level %d\n", debugSDNA);
  }

  mem_arena = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, __func__);

  /* the longest known struct is 50k, so we assume 100k is sufficient! */
  structdata = MEM_new_array_zeroed<short>(max_data_size, "structdata");
  structdata_alignment = MEM_new_array_zeroed<short>(max_data_size, "structdata_alignment");

  /* a maximum of 5000 variables, must be sufficient? */
  members = MEM_new_array_zeroed<char *>(max_array_len, "names");
  types = MEM_new_array_zeroed<char *>(max_array_len, "types");
  types_size_native = MEM_new_array_zeroed<short>(max_array_len, "types_size_native");
  types_size_32 = MEM_new_array_zeroed<short>(max_array_len, "types_size_32");
  types_size_64 = MEM_new_array_zeroed<short>(max_array_len, "types_size_64");
  types_align_32 = MEM_new_array_zeroed<short>(max_array_len, "types_size_32");
  types_align_64 = MEM_new_array_zeroed<short>(max_array_len, "types_size_64");

  structs = MEM_new_array_zeroed<short *>(max_array_len, "structs");

  /* Build versioning data */
  DNA_alias_maps(DNA_RENAME_ALIAS_FROM_STATIC,
                 &g_version_data.type_map_alias_from_static,
                 &g_version_data.member_map_alias_from_static);
  DNA_alias_maps(DNA_RENAME_STATIC_FROM_ALIAS,
                 &g_version_data.type_map_static_from_alias,
                 &g_version_data.member_map_static_from_alias);

  /**
   * Insertion of all known types.
   *
   * \warning Order of function calls here must be aligned with #eSDNA_Type.
   * \warning uint is not allowed! use in structs an unsigned int.
   * \warning sizes must match #DNA_elem_type_size().
   */
  add_type("char", 1);   /* SDNA_TYPE_CHAR */
  add_type("uchar", 1);  /* SDNA_TYPE_UCHAR */
  add_type("short", 2);  /* SDNA_TYPE_SHORT */
  add_type("ushort", 2); /* SDNA_TYPE_USHORT */
  add_type("int", 4);    /* SDNA_TYPE_INT */

  /* NOTE: long isn't supported,
   * these are place-holders to maintain alignment with #eSDNA_Type. */
  add_type("long", 4);  /* SDNA_TYPE_LONG */
  add_type("ulong", 4); /* SDNA_TYPE_ULONG */

  add_type("float", 4);    /* SDNA_TYPE_FLOAT */
  add_type("double", 8);   /* SDNA_TYPE_DOUBLE */
  add_type("int64_t", 8);  /* SDNA_TYPE_INT64 */
  add_type("uint64_t", 8); /* SDNA_TYPE_UINT64 */
  add_type("void", 0);     /* SDNA_TYPE_VOID */
  add_type("int8_t", 1);   /* SDNA_TYPE_INT8 */

  /* Fake place-holder struct definition used to get an identifier for raw, untyped bytes buffers
   * in blend-files.
   *
   * It will be written into the blend-files SDNA, but it must never be used in the source code.
   * Trying to declare `struct raw_data` in DNA headers will cause a build error.
   *
   * NOTE: While not critical, since all blend-files before introduction of this 'raw_data'
   * type/struct have been using the `0` value for raw data #BHead.SDNAnr, it's best to reserve
   * that first struct index to this raw data explicitly. */
  const int raw_data_type_index = add_type("raw_data", 0); /* SDNA_TYPE_RAW_DATA */
  short *raw_data_struct_info = add_struct(raw_data_type_index);
  /* There are no members in this struct. */
  raw_data_struct_info[1] = 0;
  BLI_STATIC_ASSERT(SDNA_RAW_DATA_STRUCT_INDEX == 0, "'raw data' SDNA struct index should be 0")
  BLI_assert(raw_data_struct_info == structs[SDNA_RAW_DATA_STRUCT_INDEX]);

  /* the defines above shouldn't be output in the padding file... */
  const int firststruct = types_num;

  /* Add all include files defined in the global array.
   * Since the internal file+path name buffer has limited length,
   * I do a little test first...
   * Mind the breaking condition here! */
  DEBUG_PRINTF(0, "\tStart of header scan:\n");
  int header_count = 0;
  Vector<dna::ParsedStruct> parsed_structs;
  Vector<dna::ParsedEnum> parsed_enums;
  for (int i = 0; *(includefiles[i]) != '\0'; i++) {
    header_count++;

    const std::string path = std::string(base_directory) + includefiles[i];
    DEBUG_PRINTF(0, "\t|-- Converting %s\n", path.c_str());
    if (!dna::parse_dna_header(path, parsed_structs, parsed_enums)) {
      return 1;
    }
  }
  DEBUG_PRINTF(0, "\tFinished scanning %d headers.\n", header_count);

  if (!dna::substitute_cpp_types(parsed_structs, parsed_enums)) {
    return 1;
  }
  register_parsed_structs(parsed_structs);

  if (calculate_struct_sizes(firststruct, file_verify, base_directory)) {
    /* error */
    return 1;
  }

  /* FOR DEBUG */
  if (debugSDNA > 1) {
    int a, b;
    // short *elem;
    short struct_members_num;

    printf("names_len %d types_len %d structs_len %d\n", members_num, types_num, structs_num);
    for (a = 0; a < members_num; a++) {
      printf(" %s\n", members[a]);
    }
    printf("\n");

    const short *sp = types_size_native;
    for (a = 0; a < types_num; a++, sp++) {
      printf(" %s %d\n", types[a], *sp);
    }
    printf("\n");

    for (a = 0; a < structs_num; a++) {
      sp = structs[a];
      printf(" struct %s elems: %d size: %d\n", types[sp[0]], sp[1], types_size_native[sp[0]]);
      struct_members_num = sp[1];
      sp += 2;
      for (b = 0; b < struct_members_num; b++, sp += 2) {
        printf("   %s %s allign32:%d, allign64:%d\n",
               types[sp[0]],
               members[sp[1]],
               types_align_32[sp[0]],
               types_align_64[sp[0]]);
      }
    }
  }

  /* file writing */

  DEBUG_PRINTF(0, "Writing file ... ");

  if (members_num == 0 || structs_num == 0) {
    /* pass */
  }
  else {
    const char nil_bytes[4] = {0};

    dna_write(file, "SDNA", 4);

    /* write names */
    dna_write(file, "NAME", 4);
    int len = members_num;
    dna_write(file, &len, 4);
    /* write array */
    len = 0;
    for (int member_index = 0; member_index < members_num; member_index++) {
      int member_len = strlen(members[member_index]) + 1;
      dna_write(file, members[member_index], member_len);
      len += member_len;
    }
    int len_align = (len + 3) & ~3;
    if (len != len_align) {
      dna_write(file, nil_bytes, len_align - len);
    }

    /* write TYPES */
    dna_write(file, "TYPE", 4);
    len = types_num;
    dna_write(file, &len, 4);
    /* write array */
    len = 0;
    for (int type_index = 0; type_index < types_num; type_index++) {
      int type_len = strlen(types[type_index]) + 1;
      dna_write(file, types[type_index], type_len);
      len += type_len;
    }
    len_align = (len + 3) & ~3;
    if (len != len_align) {
      dna_write(file, nil_bytes, len_align - len);
    }

    /* WRITE TYPELENGTHS */
    dna_write(file, "TLEN", 4);

    len = 2 * types_num;
    if (types_num & 1) {
      len += 2;
    }
    dna_write(file, types_size_native, len);

    /* WRITE STRUCTS */
    dna_write(file, "STRC", 4);
    len = structs_num;
    dna_write(file, &len, 4);

    /* calc datablock size */
    const short *sp = structs[structs_num - 1];
    sp += 2 + 2 * (sp[1]);
    len = intptr_t(reinterpret_cast<char *>(const_cast<short *>(sp)) -
                   reinterpret_cast<char *>(structs[0]));
    len = (len + 3) & ~3;

    dna_write(file, structs[0], len);
  }

  /* write a simple enum with all structs offsets,
   * should only be accessed via SDNA_TYPE_FROM_STRUCT macro */
  {
    fprintf(file_offsets, "#pragma once\n");
    fprintf(file_offsets, "#define SDNA_TYPE_FROM_STRUCT(id) _SDNA_TYPE_##id\n");
    fprintf(file_offsets, "enum {\n");
    for (int i = 0; i < structs_num; i++) {
      const short *structpoin = structs[i];
      const int struct_type_index = structpoin[0];
      fprintf(file_offsets,
              "\t_SDNA_TYPE_%s = %d,\n",
              version_struct_alias_from_static(types[struct_type_index]),
              i);
    }
    fprintf(file_offsets, "\tSDNA_TYPE_MAX = %d,\n", structs_num);
    fprintf(file_offsets, "};\n\n");
  }

  {
    fprintf(file_ids, "namespace blender {\n");
    fprintf(file_ids, "namespace dna {\n\n");
    fprintf(file_ids, "template<typename T> int sdna_struct_id_get();\n\n");
    fprintf(file_ids, "int sdna_struct_id_get_max();\n");
    fprintf(file_ids, "int sdna_struct_id_get_max() { return %d; }\n", structs_num - 1);
    fprintf(file_ids, "\n}\n");

    /* Starting at 1, because 0 is "raw data". */
    for (int i = 1; i < structs_num; i++) {
      const short *structpoin = structs[i];
      const int struct_type_index = structpoin[0];
      const char *name = version_struct_alias_from_static(types[struct_type_index]);
      fprintf(file_ids, "struct %s;\n", name);
      fprintf(file_ids, "template<> int dna::sdna_struct_id_get<%s>() { return %d; }\n", name, i);
    }

    fprintf(file_ids, "\n}\n");
  }

  {
    /* Write default struct member values for RNA. */
    fprintf(file_defaults, "/* Default struct member values for RNA. */\n");
    fprintf(file_defaults, "#define DNA_DEPRECATED_ALLOW\n");
    fprintf(file_defaults, "#define DNA_NO_EXTERNAL_CONSTRUCTORS\n");
    for (int i = 0; *(includefiles[i]) != '\0'; i++) {
      fprintf(file_defaults, "#include \"%s%s\"\n", base_directory, includefiles[i]);
    }
    fprintf(file_defaults, "using namespace blender;\n");
    /* Starting at 1, because 0 is "raw data". */
    for (int i = 1; i < structs_num; i++) {
      const short *structpoin = structs[i];
      const int struct_type_index = structpoin[0];
      const char *name = version_struct_alias_from_static(types[struct_type_index]);
      if (STREQ(name, "bTheme")) {
        /* Exception for bTheme which is auto-generated. */
        fprintf(file_defaults, "extern \"C\" const bTheme U_theme_default;\n");
      }
      else {
        fprintf(file_defaults, "static const %s DNA_DEFAULT_%s = {};\n", name, name);
      }
    }
    fprintf(file_defaults, "const void *DNA_default_table[%d] = {\n", structs_num);
    fprintf(file_defaults, "  nullptr,\n");
    for (int i = 1; i < structs_num; i++) {
      const short *structpoin = structs[i];
      const int struct_type_index = structpoin[0];
      const char *name = version_struct_alias_from_static(types[struct_type_index]);
      if (STREQ(name, "bTheme")) {
        fprintf(file_defaults, "  &U_theme_default,\n");
      }
      else {
        fprintf(file_defaults, "  &DNA_DEFAULT_%s,\n", name);
      }
    }
    fprintf(file_defaults, "};\n");
    fprintf(file_defaults, "\n");
  }

  /* Check versioning errors which could cause duplicate names,
   * do last because names are stripped. */
  {
    for (int struct_index = 0; struct_index < structs_num; struct_index++) {
      const short *sp = structs[struct_index];
      const char *type = types[sp[0]];
      const int len = sp[1];
      sp += 2;
      Set<StringRef> members_unique;
      members_unique.reserve(len);
      for (int a = 0; a < len; a++, sp += 2) {
        char *member = members[sp[1]];
        DNA_member_id_strip(member);
        if (!members_unique.add(member)) {
          fprintf(stderr,
                  "Error: duplicate name found '%s.%s', "
                  "likely cause is 'dna_rename_defs.h'\n",
                  type,
                  member);
          return 1;
        }
      }
    }
  }

  MEM_delete(structdata);
  MEM_delete(structdata_alignment);
  MEM_delete(members);
  MEM_delete(types);
  MEM_delete(types_size_native);
  MEM_delete(types_size_32);
  MEM_delete(types_size_64);
  MEM_delete(types_align_32);
  MEM_delete(types_align_64);
  MEM_delete(structs);

  BLI_memarena_free(mem_arena);

  BLI_ghash_free(g_version_data.type_map_alias_from_static, nullptr, nullptr);
  BLI_ghash_free(g_version_data.type_map_static_from_alias, nullptr, nullptr);
  BLI_ghash_free(g_version_data.member_map_static_from_alias, MEM_delete_void, nullptr);
  BLI_ghash_free(g_version_data.member_map_alias_from_static, MEM_delete_void, nullptr);

  DEBUG_PRINTF(0, "done.\n");

  return 0;
}

/** \} */

/* end make DNA. */

/* -------------------------------------------------------------------- */
/** \name Main Function
 * \{ */

static void make_bad_file(const char *file, int line)
{
  FILE *fp = fopen(file, "w");
  fprintf(fp,
          "#error \"Error! can't make correct DNA.c file from %s:%d, check alignment.\"\n",
          __FILE__,
          line);
  fclose(fp);
}

#ifndef BASE_HEADER
#  define BASE_HEADER "../"
#endif

static void print_usage(const char *argv0)
{
  printf(
      "Usage: %s [--include-file <file>, ...] "
      "dna.cc dna_type_offsets.h dna_verify.cc dna_struct_ids.cc dna_defaults.cc "
      "[base directory]\n",
      argv0);
}

}  // namespace blender

int main(int argc, char **argv)
{
  using namespace blender;
  Vector<const char *> cli_include_files;

  /* There is a number of non-optional arguments that must be provided to the executable. */
  if (argc < 6) {
    print_usage(argv[0]);
    return 1;
  }

  /* Parse optional arguments. */
  int arg_index = 1; /* Skip the argv0. */
  while (arg_index < argc) {
    if (STREQ(argv[arg_index], "--include-file")) {
      ++arg_index;
      if (arg_index == argc) {
        printf("Missing argument for --include-file\n");
        print_usage(argv[0]);
        return 1;
      }
      cli_include_files.append(argv[arg_index]);
      ++arg_index;
      continue;
    }
    break;
  }

  if (!cli_include_files.is_empty()) {
    /* Append end sentinel. */
    cli_include_files.append("");

    includefiles = cli_include_files.data();
  }

  /* Check the number of non-optional positional arguments. */
  const int num_arguments = argc - arg_index;
  if (!ELEM(num_arguments, 5, 6)) {
    print_usage(argv[0]);
    return 0;
  }

  int return_status = 0;

  FILE *file_dna = fopen(argv[arg_index], "w");
  FILE *file_dna_offsets = fopen(argv[arg_index + 1], "w");
  FILE *file_dna_verify = fopen(argv[arg_index + 2], "w");
  FILE *file_dna_ids = fopen(argv[arg_index + 3], "w");
  FILE *file_dna_defaults = fopen(argv[arg_index + 4], "w");
  if (!file_dna) {
    printf("Unable to open file: %s\n", argv[arg_index]);
    return_status = 1;
  }
  else if (!file_dna_offsets) {
    printf("Unable to open file: %s\n", argv[arg_index + 1]);
    return_status = 1;
  }
  else if (!file_dna_verify) {
    printf("Unable to open file: %s\n", argv[arg_index + 2]);
    return_status = 1;
  }
  else if (!file_dna_ids) {
    printf("Unable to open file: %s\n", argv[arg_index + 3]);
    return_status = 1;
  }
  else if (!file_dna_defaults) {
    printf("Unable to open file: %s\n", argv[arg_index + 4]);
    return_status = 1;
  }
  else {
    const char *base_directory;

    if (num_arguments == 6) {
      base_directory = argv[arg_index + 5];
    }
    else {
      base_directory = BASE_HEADER;
    }

    /* NOTE: #init_structDNA() in dna_genfile.cc expects `sdna->data` is 4-bytes aligned.
     * `DNAstr[]` buffer written by `makesdna` is used for this data, so make `DNAstr` forcefully
     * 4-bytes aligned. */
#ifdef __GNUC__
#  define FORCE_ALIGN_4 " __attribute__((aligned(4))) "
#else
#  define FORCE_ALIGN_4 " "
#endif
    fprintf(file_dna, "extern const unsigned char DNAstr[];\n");
    fprintf(file_dna, "const unsigned char" FORCE_ALIGN_4 "DNAstr[] = {\n");
#undef FORCE_ALIGN_4

    if (make_structDNA(base_directory,
                       file_dna,
                       file_dna_offsets,
                       file_dna_verify,
                       file_dna_ids,
                       file_dna_defaults))
    {
      /* error */
      fclose(file_dna);
      file_dna = nullptr;
      make_bad_file(argv[1], __LINE__);
      return_status = 1;
    }
    else {
      fprintf(file_dna, "};\n");
      fprintf(file_dna, "extern const int DNAlen;\n");
      fprintf(file_dna, "const int DNAlen = sizeof(DNAstr);\n");
    }
  }

  if (file_dna) {
    fclose(file_dna);
  }
  if (file_dna_offsets) {
    fclose(file_dna_offsets);
  }
  if (file_dna_verify) {
    fclose(file_dna_verify);
  }
  if (file_dna_ids) {
    fclose(file_dna_ids);
  }
  if (file_dna_defaults) {
    fclose(file_dna_defaults);
  }

  return return_status;
}

/* handy but fails on struct bounds which makesdna doesn't care about
 * with quite the same strictness as GCC does */
#if 0
/* include files for automatic dependencies */

/* extra safety check that we are aligned,
 * warnings here are easier to fix the makesdna's */
#  ifdef __GNUC__
#    pragma GCC diagnostic error "-Wpadded"
#  endif

#endif /* if 0 */

/* The include file below is automatically generated from the `SRC_DNA_INC`
 * variable in 'source/blender/CMakeLists.txt'. */
#include "dna_includes_all.h"

/* end of list */

/** \} */

/* -------------------------------------------------------------------- */
/** \name DNA Renaming Sanity Check
 *
 * Without this it's possible to reference struct members that don't exist,
 * breaking backward & forward compatibility.
 *
 * \{ */

static void UNUSED_FUNCTION(dna_rename_defs_ensure)()
{
  using namespace blender;
#define DNA_STRUCT_RENAME(old, new) (void)sizeof(new);
#define DNA_STRUCT_RENAME_MEMBER(struct_name, old, new) (void)offsetof(struct_name, new);
#include "dna_rename_defs.h"

#undef DNA_STRUCT_RENAME
#undef DNA_STRUCT_RENAME_MEMBER
}

/** \} */
