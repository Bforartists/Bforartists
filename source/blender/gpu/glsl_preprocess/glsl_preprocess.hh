/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup glsl_preprocess
 */

#pragma once

#include <cctype>
#include <cstdint>
#include <functional>
#include <iostream>
#include <regex>
#include <sstream>
#include <string>
#include <vector>

#include "shader_parser.hh"

namespace blender::gpu::shader {

#define ERROR_TOK(token) (token).line_number(), (token).char_number(), (token).line_str()

/* Metadata extracted from shader source file.
 * These are then converted to their GPU module equivalent. */
/* TODO(fclem): Make GPU enums standalone and directly use them instead of using separate enums
 * and types. */
namespace metadata {

/* Compile-time hashing function which converts string to a 64bit hash. */
constexpr static uint64_t hash(const char *name)
{
  uint64_t hash = 2166136261u;
  while (*name) {
    hash = hash * 16777619u;
    hash = hash ^ *name;
    ++name;
  }
  return hash;
}

static uint64_t hash(const std::string &name)
{
  return hash(name.c_str());
}

enum Builtin : uint64_t {
  FragCoord = hash("gl_FragCoord"),
  FrontFacing = hash("gl_FrontFacing"),
  GlobalInvocationID = hash("gl_GlobalInvocationID"),
  InstanceID = hash("gl_InstanceID"),
  LocalInvocationID = hash("gl_LocalInvocationID"),
  LocalInvocationIndex = hash("gl_LocalInvocationIndex"),
  NumWorkGroup = hash("gl_NumWorkGroup"),
  PointCoord = hash("gl_PointCoord"),
  PointSize = hash("gl_PointSize"),
  PrimitiveID = hash("gl_PrimitiveID"),
  VertexID = hash("gl_VertexID"),
  WorkGroupID = hash("gl_WorkGroupID"),
  WorkGroupSize = hash("gl_WorkGroupSize"),
  drw_debug = hash("drw_debug_"),
  printf = hash("printf"),
  assert = hash("assert"),
  runtime_generated = hash("runtime_generated"),
};

enum Qualifier : uint64_t {
  in = hash("in"),
  out = hash("out"),
  inout = hash("inout"),
};

enum Type : uint64_t {
  float1 = hash("float"),
  float2 = hash("float2"),
  float3 = hash("float3"),
  float4 = hash("float4"),
  float3x3 = hash("float3x3"),
  float4x4 = hash("float4x4"),
  sampler1DArray = hash("sampler1DArray"),
  sampler2DArray = hash("sampler2DArray"),
  sampler2D = hash("sampler2D"),
  sampler3D = hash("sampler3D"),
  Closure = hash("Closure"),
};

struct ArgumentFormat {
  Qualifier qualifier;
  Type type;
};

struct FunctionFormat {
  std::string name;
  std::vector<ArgumentFormat> arguments;
};

struct PrintfFormat {
  uint32_t hash;
  std::string format;
};

struct Source {
  std::vector<Builtin> builtins;
  /* Note: Could be a set, but for now the order matters. */
  std::vector<std::string> dependencies;
  std::vector<PrintfFormat> printf_formats;
  std::vector<FunctionFormat> functions;

  std::string serialize(const std::string &function_name) const
  {
    std::stringstream ss;
    ss << "static void " << function_name
       << "(GPUSource &source, GPUFunctionDictionary *g_functions, GPUPrintFormatMap *g_formats) "
          "{\n";
    for (auto function : functions) {
      ss << "  {\n";
      ss << "    Vector<metadata::ArgumentFormat> args = {\n";
      for (auto arg : function.arguments) {
        ss << "      "
           << "metadata::ArgumentFormat{"
           << "metadata::Qualifier(" << std::to_string(uint64_t(arg.qualifier)) << "LLU), "
           << "metadata::Type(" << std::to_string(uint64_t(arg.type)) << "LLU)"
           << "},\n";
      }
      ss << "    };\n";
      ss << "    source.add_function(\"" << function.name << "\", args, g_functions);\n";
      ss << "  }\n";
    }
    for (auto builtin : builtins) {
      ss << "  source.add_builtin(metadata::Builtin(" << std::to_string(builtin) << "LLU));\n";
    }
    for (auto dependency : dependencies) {
      ss << "  source.add_dependency(\"" << dependency << "\");\n";
    }
    for (auto format : printf_formats) {
      ss << "  source.add_printf_format(uint32_t(" << std::to_string(format.hash) << "), "
         << format.format << ", g_formats);\n";
    }
    /* Avoid warnings. */
    ss << "  UNUSED_VARS(source, g_functions, g_formats);\n";
    ss << "}\n";
    return ss.str();
  }
};

}  // namespace metadata

/**
 * Shader source preprocessor that allow to mutate GLSL into cross API source that can be
 * interpreted by the different GPU backends. Some syntax are mutated or reported as incompatible.
 *
 * Implementation speed is not a huge concern as we only apply this at compile time or on python
 * shaders source.
 */
class Preprocessor {
  using uint64_t = std::uint64_t;
  using report_callback = std::function<void(
      int error_line, int error_char, std::string error_line_string, const char *error_str)>;
  struct SharedVar {
    std::string type;
    std::string name;
    std::string array;
  };

  std::vector<SharedVar> shared_vars_;

  metadata::Source metadata;

 public:
  enum SourceLanguage {
    UNKNOWN = 0,
    CPP,
    MSL,
    GLSL,
    /* Same as GLSL but enable partial C++ feature support like template, references,
     * include system, etc ... */
    BLENDER_GLSL,
  };

  static SourceLanguage language_from_filename(const std::string &filename)
  {
    if (filename.find(".msl") != std::string::npos) {
      return MSL;
    }
    if (filename.find(".glsl") != std::string::npos) {
      return GLSL;
    }
    if (filename.find(".hh") != std::string::npos) {
      return CPP;
    }
    return UNKNOWN;
  }

  /* Takes a whole source file and output processed source. */
  std::string process(SourceLanguage language,
                      std::string str,
                      const std::string &filename,
                      bool do_parse_function,
                      bool do_small_type_linting,
                      report_callback report_error,
                      metadata::Source &r_metadata)
  {
    if (language == UNKNOWN) {
      report_error(0, 0, "", "Unknown file type");
      return "";
    }
    str = remove_comments(str, report_error);
    threadgroup_variables_parsing(str);
    parse_builtins(str, filename);
    if (language == BLENDER_GLSL || language == CPP) {
      if (do_parse_function) {
        parse_library_functions(str);
      }
      if (language == BLENDER_GLSL) {
        include_parse(str, report_error);
        pragma_runtime_generated_parsing(str);
        pragma_once_linting(str, filename, report_error);
      }
      str = preprocessor_directive_mutation(str);
      str = swizzle_function_mutation(str, report_error);
      str = enum_macro_injection(str, language == CPP, report_error);
      if (language == BLENDER_GLSL) {
        str = template_struct_mutation(str, report_error);
        str = struct_method_mutation(str, report_error);
        str = empty_struct_mutation(str, report_error);
        str = method_call_mutation(str, report_error);
        str = stage_function_mutation(str);
        str = resource_guard_mutation(str, report_error);
        str = loop_unroll(str, report_error);
        str = assert_processing(str, filename, report_error);
        str = static_strings_merging(str, report_error);
        str = static_strings_parsing_and_mutation(str, report_error);
        str = printf_processing(str, report_error);
        quote_linting(str, report_error);
      }
      global_scope_constant_linting(str, report_error);
      matrix_constructor_linting(str, report_error);
      array_constructor_linting(str, report_error);
      if (do_small_type_linting) {
        small_type_linting(str, report_error);
      }
      str = remove_quotes(str);
      if (language == BLENDER_GLSL) {
        str = using_mutation(str, report_error);
        str = namespace_mutation(str, report_error);
      }
      str = argument_reference_mutation(str, report_error);
      str = default_argument_mutation(str, report_error);
      str = variable_reference_mutation(str, report_error);
      str = template_definition_mutation(str, report_error);
      if (language == BLENDER_GLSL) {
        str = namespace_separator_mutation(str);
      }
      str = template_call_mutation(str, report_error);
    }
#ifdef __APPLE__ /* Limiting to Apple hardware since GLSL compilers might have issues. */
    if (language == GLSL) {
      str = matrix_constructor_mutation(str);
    }
#endif
    str = argument_decorator_macro_injection(str);
    str = array_constructor_macro_injection(str);
    r_metadata = metadata;
    return line_directive_prefix(filename) + str + threadgroup_variables_suffix();
  }

  /* Variant use for python shaders. */
  std::string process(const std::string &str)
  {
    auto no_err_report = [](int, int, std::string, const char *) {};
    metadata::Source unused;
    return process(GLSL, str, "", false, false, no_err_report, unused);
  }

 private:
  using regex_callback = std::function<void(const std::smatch &)>;
  using regex_callback_with_line_count = std::function<void(const std::smatch &, int64_t)>;

  /* Helper to make the code more readable in parsing functions. */
  void regex_global_search(const std::string &str,
                           const std::regex &regex,
                           regex_callback callback)
  {
    using namespace std;
    string::const_iterator it = str.begin();
    for (smatch match; regex_search(it, str.end(), match, regex); it = match.suffix().first) {
      callback(match);
    }
  }

  void regex_global_search(const std::string &str,
                           const std::regex &regex,
                           regex_callback_with_line_count callback)
  {
    using namespace std;
    int64_t line = 1;
    regex_global_search(str, regex, [&line, &callback](const std::smatch &match) {
      line += line_count(match.prefix().str());
      callback(match, line);
      line += line_count(match[0].str());
    });
  }

  template<typename ReportErrorF>
  std::string remove_comments(const std::string &str, const ReportErrorF &report_error)
  {
    std::string out_str = str;
    {
      /* Multi-line comments. */
      size_t start, end = 0;
      while ((start = out_str.find("/*", end)) != std::string::npos) {
        end = out_str.find("*/", start + 2);
        if (end == std::string::npos) {
          break;
        }
        for (size_t i = start; i < end + 2; ++i) {
          if (out_str[i] != '\n') {
            out_str[i] = ' ';
          }
        }
      }

      if (end == std::string::npos) {
        report_error(line_number(out_str, start),
                     char_number(out_str, start),
                     line_str(out_str, start),
                     "Malformed multi-line comment.");
        return out_str;
      }
    }
    {
      /* Single-line comments. */
      size_t start, end = 0;
      while ((start = out_str.find("//", end)) != std::string::npos) {
        end = out_str.find('\n', start + 2);
        if (end == std::string::npos) {
          break;
        }
        for (size_t i = start; i < end; ++i) {
          out_str[i] = ' ';
        }
      }

      if (end == std::string::npos) {
        report_error(line_number(out_str, start),
                     char_number(out_str, start),
                     line_str(out_str, start),
                     "Malformed single line comment, missing newline.");
        return out_str;
      }
    }
    /* Remove trailing white space as they make the subsequent regex much slower. */
    std::regex regex(R"((\ )*?\n)");
    return std::regex_replace(out_str, regex, "\n");
  }

  static std::string template_arguments_mangle(const shader::parser::Scope template_args)
  {
    using namespace std;
    using namespace shader::parser;
    string args_concat;
    template_args.foreach_scope(ScopeType::TemplateArg, [&](const Scope &scope) {
      args_concat += 'T' + scope.start().str();
    });
    return args_concat;
  }

  std::string template_struct_mutation(const std::string &str, report_callback &report_error)
  {
    using namespace std;
    using namespace shader::parser;

    std::string out_str = str;

    {
      Parser parser(out_str, report_error);

      parser.foreach_match("w<..>(..)", [&](const vector<Token> &tokens) {
        const Scope template_args = tokens[1].scope();
        template_args.foreach_match("w<..>", [&parser](const vector<Token> &tokens) {
          parser.replace(tokens[1].scope(), template_arguments_mangle(tokens[1].scope()), true);
        });
      });

      parser.apply_mutations();

      /* Replace full specialization by simple struct. */
      parser.foreach_match("t<>sw<..>", [&](const std::vector<Token> &tokens) {
        parser.erase(tokens[0], tokens[2]);
        parser.replace(tokens[5].scope(), template_arguments_mangle(tokens[5].scope()), true);
      });

      out_str = parser.result_get();
    }
    {
      Parser parser(out_str, report_error);

      parser.foreach_scope(ScopeType::Template, [&](Scope temp) {
        /* Parse template declaration. */
        Token struct_start = temp.end().next();
        if (struct_start != Struct) {
          return;
        }
        Token struct_name = struct_start.next();
        Scope struct_body = struct_name.next().scope();

        bool error = false;
        temp.foreach_match("=", [&](const std::vector<Token> &tokens) {
          report_error(ERROR_TOK(tokens[0]),
                       "Default arguments are not supported inside template declaration");
          error = true;
        });
        if (error) {
          return;
        }

        string arg_pattern;
        vector<string> arg_list;
        temp.foreach_scope(ScopeType::TemplateArg, [&](Scope arg) {
          const Token type = arg.start();
          const Token name = type.next();
          const string name_str = name.str();
          const string type_str = type.str();

          arg_list.emplace_back(name_str);

          if (type_str == "typename") {
            arg_pattern += ",w";
          }
          else if (type_str == "enum" || type_str == "bool") {
            arg_pattern += ",w";
          }
          else if (type_str == "int" || type_str == "uint") {
            arg_pattern += ",0";
          }
          else {
            report_error(ERROR_TOK(type), "Invalid template argument type");
          }
        });

        Token struct_end = struct_body.end();
        const string fn_decl = parser.substr_range_inclusive(struct_start.str_index_start(),
                                                             struct_end.str_index_last());

        /* Remove declaration. */
        Token template_keyword = temp.start().prev();
        parser.erase(template_keyword.str_index_start(), struct_end.line_end());

        /* Replace instantiations. */
        Scope parent_scope = temp.scope();
        string specialization_pattern = "tsw<" + arg_pattern.substr(1) + ">";
        parent_scope.foreach_match(specialization_pattern, [&](const std::vector<Token> &tokens) {
          if (struct_name.str() != tokens[2].str()) {
            return;
          }
          /* Parse template values. */
          vector<pair<string, string>> arg_name_value_pairs;
          for (int i = 0; i < arg_list.size(); i++) {
            arg_name_value_pairs.emplace_back(arg_list[i], tokens[4 + 2 * i].str());
          }
          /* Specialize template content. */
          Parser instance_parser(fn_decl, report_error, true);
          instance_parser.foreach_match("w", [&](const std::vector<Token> &tokens) {
            string token_str = tokens[0].str();
            for (const auto &arg_name_value : arg_name_value_pairs) {
              if (token_str == arg_name_value.first) {
                instance_parser.replace(tokens[0], arg_name_value.second);
              }
            }
          });

          const string template_args = parser.substr_range_inclusive(
              tokens[3], tokens[3 + arg_pattern.size()]);
          size_t pos = fn_decl.find(" " + struct_name.str());
          instance_parser.insert_after(pos + struct_name.str().size(), template_args);
          /* Paste template content in place of instantiation. */
          Token end_of_instantiation = tokens.back();
          string instance = instance_parser.result_get();
          parser.insert_line_number(tokens.front().str_index_start() - 1,
                                    struct_start.line_number());
          parser.replace(tokens.front().str_index_start(),
                         end_of_instantiation.str_index_last_no_whitespace(),
                         instance);
          parser.insert_line_number(end_of_instantiation.line_end() + 1,
                                    end_of_instantiation.line_number() + 1);
        });
      });

      out_str = parser.result_get();
    }
    {
      Parser parser(out_str, report_error);

      /* This rely on our codestyle that do not put spaces between template name and the opening
       * angle bracket. */
      parser.foreach_match("sw<..>", [&](const std::vector<Token> &tokens) {
        parser.replace(tokens[2].scope(), template_arguments_mangle(tokens[2].scope()), true);
      });
      out_str = parser.result_get();
    }
    return out_str;
  }

  std::string template_definition_mutation(const std::string &str, report_callback &report_error)
  {
    if (str.find("template") == std::string::npos) {
      return str;
    }

    using namespace std;
    using namespace shader::parser;

    std::string out_str = str;

    Parser parser(out_str, report_error);

    auto process_specialization = [&](const Token specialization_start,
                                      const Scope template_args) {
      parser.erase(specialization_start, specialization_start.next().next());
      parser.replace(template_args, template_arguments_mangle(template_args), true);
    };

    parser.foreach_scope(ScopeType::Global, [&](Scope scope) {
      /* Replace full specialization by simple functions. */
      scope.foreach_match("t<>ww<", [&](const std::vector<Token> &tokens) {
        process_specialization(tokens[0], tokens[5].scope());
      });
      scope.foreach_match("t<>ww::w<", [&](const std::vector<Token> &tokens) {
        process_specialization(tokens[0], tokens[8].scope());
      });
    });

    parser.apply_mutations();

    auto process_template = [&](const Token fn_start,
                                const string &fn_name,
                                const Scope fn_args,
                                const Scope temp,
                                const Token fn_end) {
      bool error = false;
      temp.foreach_match("=", [&](const std::vector<Token> &tokens) {
        report_error(tokens[0].line_number(),
                     tokens[0].char_number(),
                     tokens[0].line_str(),
                     "Default arguments are not supported inside template declaration");
        error = true;
      });
      if (error) {
        return;
      }

      string arg_pattern;
      vector<string> arg_list;
      bool all_template_args_in_function_signature = true;
      temp.foreach_scope(ScopeType::TemplateArg, [&](Scope arg) {
        const Token type = arg.start();
        const Token name = type.next();
        const string name_str = name.str();
        const string type_str = type.str();

        arg_list.emplace_back(name_str);

        if (type_str == "typename") {
          arg_pattern += ",w";
          bool found = false;
          /* Search argument list for typenames. If typename matches, the template argument is
           * present inside the function signature. */
          fn_args.foreach_match("ww", [&](const std::vector<Token> &tokens) {
            if (tokens[0].str() == name_str) {
              found = true;
            }
          });
          all_template_args_in_function_signature &= found;
        }
        else if (type_str == "enum" || type_str == "bool") {
          arg_pattern += ",w";
          /* Values cannot be resolved using type deduction. */
          all_template_args_in_function_signature = false;
        }
        else if (type_str == "int" || type_str == "uint") {
          arg_pattern += ",0";
          /* Values cannot be resolved using type deduction. */
          all_template_args_in_function_signature = false;
        }
        else {
          report_error(ERROR_TOK(type), "Invalid template argument type");
        }
      });

      const string fn_decl = parser.substr_range_inclusive(fn_start.str_index_start(),
                                                           fn_end.line_end());

      /* Remove declaration. */
      Token template_keyword = temp.start().prev();
      parser.erase(template_keyword.str_index_start(), fn_end.line_end());

      auto process_instantiation = [&](const string &inst_name,
                                       const Token inst_start,
                                       const Token inst_end,
                                       const Scope &inst_args) {
        if (fn_name != inst_name) {
          return;
        }
        /* Parse template values. */
        vector<pair<string, string>> arg_name_value_pairs;
        for (int i = 0; i < arg_list.size(); i++) {
          arg_name_value_pairs.emplace_back(arg_list[i], inst_args[1 + 2 * i].str());
        }
        /* Specialize template content. */
        Parser instance_parser(fn_decl, report_error, true);
        instance_parser.foreach_token(Word, [&](const Token &word) {
          string token_str = word.str();
          for (const auto &arg_name_value : arg_name_value_pairs) {
            if (token_str == arg_name_value.first) {
              instance_parser.replace(word, arg_name_value.second);
            }
          }
        });

        if (!all_template_args_in_function_signature) {
          /* Append template args after function name.
           * `void func() {}` > `void func<a, 1>() {}`. */
          size_t pos = fn_decl.find(" " + fn_name);
          instance_parser.insert_after(pos + fn_name.size(), inst_args.str());
        }
        /* Paste template content in place of instantiation. */
        string instance = instance_parser.result_get();
        parser.insert_line_number(inst_start.str_index_start() - 1, fn_start.line_number());
        parser.replace(
            inst_start.str_index_start(), inst_end.str_index_last_no_whitespace(), instance);
        parser.insert_line_number(inst_end.line_end() + 1, inst_end.line_number() + 1);
      };

      /* Replace instantiations. */
      Scope parent_scope = temp.scope();
      {
        string specialization_pattern = "tww<" + arg_pattern.substr(1) + ">(..);";
        parent_scope.foreach_match(specialization_pattern, [&](const vector<Token> &tokens) {
          process_instantiation(tokens[2].str(), tokens.front(), tokens.back(), tokens[3].scope());
        });
      }
      {
        string specialization_pattern = "tww::w<" + arg_pattern.substr(1) + ">(..);";
        parent_scope.foreach_match(specialization_pattern, [&](const vector<Token> &tokens) {
          const string inst_name = parser.substr_range_inclusive(tokens[2], tokens[5]);
          process_instantiation(inst_name, tokens.front(), tokens.back(), tokens[6].scope());
        });
      }
    };

    parser.foreach_match("t<..>ww(..)c?{..}", [&](const vector<Token> &tokens) {
      process_template(
          tokens[5], tokens[6].str(), tokens[7].scope(), tokens[1].scope(), tokens[16]);
    });

    parser.foreach_match("t<..>ww::w(..)c?{..}", [&](const vector<Token> &tokens) {
      const string fn_name = parser.substr_range_inclusive(tokens[6], tokens[9]);
      process_template(tokens[5], fn_name, tokens[10].scope(), tokens[1].scope(), tokens[19]);
    });

    out_str = parser.result_get();

    {
      /* Check if there is no remaining declaration and instantiation that were not processed. */
      size_t error_pos;
      if ((error_pos = out_str.find("template<")) != std::string::npos) {
        report_error(line_number(out_str, error_pos),
                     char_number(out_str, error_pos),
                     line_str(out_str, error_pos),
                     "Template declaration unsupported syntax");
      }
      if ((error_pos = out_str.find("template ")) != std::string::npos) {
        report_error(line_number(out_str, error_pos),
                     char_number(out_str, error_pos),
                     line_str(out_str, error_pos),
                     "Template instantiation unsupported syntax");
      }
    }
    return out_str;
  }

  std::string template_call_mutation(const std::string &str, report_callback &report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);
    parser.foreach_match("w<..>", [&](const std::vector<Token> &tokens) {
      parser.replace(tokens[1].scope(), template_arguments_mangle(tokens[1].scope()), true);
    });
    return parser.result_get();
  }

  std::string remove_quotes(const std::string &str)
  {
    return std::regex_replace(str, std::regex(R"(["'])"), " ");
  }

  void include_parse(const std::string &str, report_callback report_error)
  {
    /* Parse include directive before removing them. */
    std::regex regex(R"(#(\s*)include\s*\"(\w+\.\w+)\")");

    regex_global_search(str, regex, [&](const std::smatch &match) {
      std::string indent = match[1].str();
      /* Assert that includes are not nested in other preprocessor directives. */
      if (!indent.empty()) {
        report_error(line_number(match),
                     char_number(match),
                     line_str(match),
                     "#include directives must not be inside #if clause");
      }
      std::string dependency_name = match[2].str();
      /* Assert that includes are at the top of the file. */
      if (dependency_name == "gpu_glsl_cpp_stubs.hh") {
        /* Skip GLSL-C++ stubs. They are only for IDE linting. */
        return;
      }
      if (dependency_name.find("info.hh") != std::string::npos) {
        /* Skip info files. They are only for IDE linting. */
        return;
      }
      metadata.dependencies.emplace_back(dependency_name);
    });
  }

  void pragma_runtime_generated_parsing(const std::string &str)
  {
    if (str.find("\n#pragma runtime_generated") != std::string::npos) {
      metadata.builtins.emplace_back(metadata::Builtin::runtime_generated);
    }
  }

  void pragma_once_linting(const std::string &str,
                           const std::string &filename,
                           report_callback report_error)
  {
    if (filename.find("_lib.") == std::string::npos) {
      return;
    }
    if (str.find("\n#pragma once") == std::string::npos) {
      std::smatch match;
      report_error(line_number(match),
                   char_number(match),
                   line_str(match),
                   "Library files must contain #pragma once directive.");
    }
  }

  std::string loop_unroll(const std::string &str, report_callback report_error)
  {
    if (str.find("[[gpu::unroll") == std::string::npos) {
      return str;
    }

    struct Loop {
      /* `[[gpu::unroll]] for (int i = 0; i < 10; i++)` */
      std::string definition;
      /* `{ some_computation(i); }` */
      std::string body;
      /* `int i = 0` */
      std::string init_statement;
      /* `i < 10` */
      std::string test_statement;
      /* `i++` */
      std::string iter_statement;
      /* Spaces and newline between loop start and body. */
      std::string body_prefix;
      /* Spaces before the loop definition. */
      std::string indent;
      /* `10` */
      int64_t iter_count;
      /* Line at which the loop was defined. */
      int64_t definition_line;
      /* Line at which the body starts. */
      int64_t body_line;
      /* Line at which the body ends. */
      int64_t end_line;
    };

    std::vector<Loop> loops;

    auto add_loop = [&](Loop &loop,
                        const std::smatch &match,
                        int64_t line,
                        int64_t lines_in_content) {
      std::string suffix = match.suffix().str();
      loop.body = get_content_between_balanced_pair(loop.definition + suffix, '{', '}');
      loop.body = '{' + loop.body + '}';
      loop.definition_line = line - lines_in_content;
      loop.body_line = line;
      loop.end_line = loop.body_line + line_count(loop.body);

      /* Check that there is no unsupported keywords in the loop body. */
      if (loop.body.find(" break;") != std::string::npos ||
          loop.body.find(" continue;") != std::string::npos)
      {
        /* Expensive check. Remove other loops and switch scopes inside the unrolled loop scope and
         * check again to avoid false positive. */
        std::string modified_body = loop.body;

        std::regex regex_loop(R"( (for|while|do) )");
        regex_global_search(loop.body, regex_loop, [&](const std::smatch &match) {
          std::string inner_scope = get_content_between_balanced_pair(match.suffix(), '{', '}');
          replace_all(modified_body, inner_scope, "");
        });

        /* Checks if `continue` exists, even in switch statement inside the unrolled loop scope. */
        if (modified_body.find(" continue;") != std::string::npos) {
          report_error(line_number(match),
                       char_number(match),
                       line_str(match),
                       "Error: Unrolled loop cannot contain \"continue\" statement.");
        }

        std::regex regex_switch(R"( switch )");
        regex_global_search(loop.body, regex_switch, [&](const std::smatch &match) {
          std::string inner_scope = get_content_between_balanced_pair(match.suffix(), '{', '}');
          replace_all(modified_body, inner_scope, "");
        });

        /* Checks if `break` exists inside the unrolled loop scope. */
        if (modified_body.find(" break;") != std::string::npos) {
          report_error(line_number(match),
                       char_number(match),
                       line_str(match),
                       "Error: Unrolled loop cannot contain \"break\" statement.");
        }
      }
      loops.emplace_back(loop);
    };

    /* Parse the loop syntax. */
    {
      /* [[gpu::unroll]]. */
      std::regex regex(R"(( *))"
                       R"(\[\[gpu::unroll\]\])"
                       R"(\s*for\s*\()"
                       R"(\s*((?:uint|int)\s+(\w+)\s+=\s+(-?\d+));)" /* Init statement. */
                       R"(\s*((\w+)\s+(>|<)(=?)\s+(-?\d+)))"         /* Conditional statement. */
                       R"(\s*(?:&&)?\s*([^;)]+)?;)"       /* Extra conditional statement. */
                       R"(\s*(((\w+)(\+\+|\-\-))[^\)]*))" /* Iteration statement. */
                       R"(\)(\s*))");

      int64_t line = 0;

      regex_global_search(str, regex, [&](const std::smatch &match) {
        std::string counter_1 = match[3].str();
        std::string counter_2 = match[6].str();
        std::string counter_3 = match[13].str();

        std::string content = match[0].str();
        int64_t lines_in_content = line_count(content);

        line += line_count(match.prefix().str()) + lines_in_content;

        if ((counter_1 != counter_2) || (counter_1 != counter_3)) {
          report_error(line_number(match),
                       char_number(match),
                       line_str(match),
                       "Error: Non matching loop counter variable.");
          return;
        }

        Loop loop;

        int64_t init = std::stol(match[4].str());
        int64_t end = std::stol(match[9].str());
        /* TODO(fclem): Support arbitrary strides (aka, arbitrary iter statement). */
        loop.iter_count = std::abs(end - init);

        std::string condition = match[7].str();
        if (condition.empty()) {
          report_error(line_number(match),
                       char_number(match),
                       line_str(match),
                       "Error: Unsupported condition in unrolled loop.");
        }

        std::string equal = match[8].str();
        if (equal == "=") {
          loop.iter_count += 1;
        }

        std::string iter = match[14].str();
        if (iter == "++") {
          if (condition == ">") {
            report_error(line_number(match),
                         char_number(match),
                         line_str(match),
                         "Error: Unsupported condition in unrolled loop.");
          }
        }
        else if (iter == "--") {
          if (condition == "<") {
            report_error(line_number(match),
                         char_number(match),
                         line_str(match),
                         "Error: Unsupported condition in unrolled loop.");
          }
        }
        else {
          report_error(line_number(match),
                       char_number(match),
                       line_str(match),
                       "Error: Unsupported for loop expression. Expecting ++ or --");
        }

        loop.definition = content;
        loop.indent = match[1].str();
        loop.init_statement = match[2].str();
        if (!match[10].str().empty()) {
          loop.test_statement = "if (" + match[10].str() + ") ";
        }
        loop.iter_statement = match[11].str();
        loop.body_prefix = match[15].str();

        add_loop(loop, match, line, lines_in_content);
      });
    }
    {
      /* [[gpu::unroll(n)]]. */
      std::regex regex(R"(( *))"
                       R"(\[\[gpu::unroll\((\d+)\)\]\])"
                       R"(\s*for\s*\()"
                       R"(\s*([^;]*);)"
                       R"(\s*([^;]*);)"
                       R"(\s*([^)]*))"
                       R"(\)(\s*))");

      int64_t line = 0;

      regex_global_search(str, regex, [&](const std::smatch &match) {
        std::string content = match[0].str();

        int64_t lines_in_content = line_count(content);

        line += line_count(match.prefix().str()) + lines_in_content;

        Loop loop;
        loop.iter_count = std::stol(match[2].str());
        loop.definition = content;
        loop.indent = match[1].str();
        loop.init_statement = match[3].str();
        loop.test_statement = "if (" + match[4].str() + ") ";
        loop.iter_statement = match[5].str();
        loop.body_prefix = match[13].str();

        add_loop(loop, match, line, lines_in_content);
      });
    }

    std::string out = str;

    /* Copy paste loop iterations. */
    for (const Loop &loop : loops) {
      std::string replacement = loop.indent + "{ " + loop.init_statement + ";";
      for (int64_t i = 0; i < loop.iter_count; i++) {
        replacement += std::string("\n#line ") + std::to_string(loop.body_line + 1) + "\n";
        replacement += loop.indent + loop.test_statement + loop.body;
        replacement += std::string("\n#line ") + std::to_string(loop.definition_line + 1) + "\n";
        replacement += loop.indent + loop.iter_statement + ";";
        if (i == loop.iter_count - 1) {
          replacement += std::string("\n#line ") + std::to_string(loop.end_line + 1) + "\n";
          replacement += loop.indent + "}";
        }
      }

      std::string replaced = loop.definition + loop.body;

      /* Replace all occurrences in case of recursive unrolling. */
      replace_all(out, replaced, replacement);
    }

    /* Check for remaining keywords. */
    if (out.find("[[gpu::unroll") != std::string::npos) {
      regex_global_search(str, std::regex(R"(\[\[gpu::unroll)"), [&](const std::smatch &match) {
        report_error(line_number(match),
                     char_number(match),
                     line_str(match),
                     "Error: Incompatible format for [[gpu::unroll]].");
      });
    }

    return out;
  }

  std::string namespace_mutation(const std::string &str, report_callback report_error)
  {
    if (str.find("namespace") == std::string::npos) {
      return str;
    }

    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    std::string out = str;

    /* Parse each namespace declaration. */
    parser.foreach_scope(ScopeType::Namespace, [&](const Scope &scope) {
      /* TODO(fclem): This could be supported using multiple passes. */
      scope.foreach_match("n", [&](const std::vector<Token> &tokens) {
        report_error(ERROR_TOK(tokens[0]), "Nested namespaces are unsupported.");
      });

      string namespace_prefix = scope.start().prev().full_symbol_name() + "::";
      auto process_symbol = [&](const Token &symbol) {
        if (symbol.next() == '<') {
          /* Template instantiation or specialization. */
          return;
        }
        /* Replace all occurrences of the non-namespace specified symbol. */
        scope.foreach_token(Word, [&](const Token &token) {
          if (token.str() != symbol.str()) {
            return;
          }
          /* Reject symbols that already have namespace specified. */
          if (token.namespace_start() != token) {
            return;
          }
          /* Reject method calls. */
          if (token.prev() == '.') {
            return;
          }
          parser.replace(token, namespace_prefix + token.str(), true);
        });
      };

      scope.foreach_function(
          [&](bool, Token, Token fn_name, Scope, bool, Scope) { process_symbol(fn_name); });
      scope.foreach_struct([&](Token, Token struct_name, Scope) { process_symbol(struct_name); });

      Token namespace_tok = scope.start().prev().namespace_start().prev();
      if (namespace_tok == Namespace) {
        parser.erase(namespace_tok, scope.start());
        parser.erase(scope.end());
      }
      else {
        report_error(ERROR_TOK(namespace_tok), "Expected namespace token.");
      }
    });

    return parser.result_get();
  }

  /* Needs to run before namespace mutation so that `using` have more precedence. */
  std::string using_mutation(const std::string &str, report_callback report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    parser.foreach_match("un", [&](const std::vector<Token> &tokens) {
      report_error(ERROR_TOK(tokens[0]),
                   "Unsupported `using namespace`. "
                   "Add individual `using` directives for each needed symbol.");
    });

    auto process_using = [&](const Token &using_tok,
                             const Token &from,
                             const Token &to_start,
                             const Token &to_end,
                             const Token &end_tok) {
      string to = parser.substr_range_inclusive(to_start, to_end);
      string namespace_prefix = parser.substr_range_inclusive(to_start,
                                                              to_end.prev().prev().prev());
      Scope scope = from.scope();

      /* Using the keyword in global or at namespace scope. */
      if (scope.type() == ScopeType::Global) {
        report_error(ERROR_TOK(using_tok), "The `using` keyword is not allowed in global scope.");
        return;
      }
      if (scope.type() == ScopeType::Namespace) {
        /* Ensure we are bringing symbols from the same namespace.
         * Otherwise we can have different shadowing outcome between shader and C++. */
        string namespace_name = scope.start().prev().full_symbol_name();
        if (namespace_name != namespace_prefix) {
          report_error(
              ERROR_TOK(using_tok),
              "The `using` keyword is only allowed in namespace scope to make visible symbols "
              "from the same namespace declared in another scope, potentially from another "
              "file.");
          return;
        }
      }

      /* Assignments do not allow to alias functions symbols. */
      const bool use_alias = from.str() != to_end.str();
      const bool replace_fn = !use_alias;
      /** IMPORTANT: If replace_fn is true, this can replace any symbol type if there are functions
       * and types with the same name. We could support being more explicit about the type of
       * symbol to replace using an optional attribute [[gpu::using_function]]. */

      /* Replace all occurrences of the non-namespace specified symbol. */
      scope.foreach_token(Word, [&](const Token &token) {
        /* Do not replace symbols before the using statement. */
        if (token.index <= to_end.index) {
          return;
        }
        /* Reject symbols that contain the target symbol name. */
        if (token.prev() == ':') {
          return;
        }
        if (!replace_fn && token.next() == '(') {
          return;
        }
        if (token.str() != from.str()) {
          return;
        }
        parser.replace(token, to, true);
      });

      parser.erase(using_tok, end_tok);
    };

    parser.foreach_match("uw::w", [&](const std::vector<Token> &tokens) {
      Token end = tokens.back().find_next(SemiColon);
      process_using(tokens[0], end.prev(), tokens[1], end.prev(), end);
    });

    parser.foreach_match("uw=w::w", [&](const std::vector<Token> &tokens) {
      Token end = tokens.back().find_next(SemiColon);
      process_using(tokens[0], tokens[1], tokens[3], end.prev(), end);
    });

    parser.apply_mutations();

    /* Verify all using were processed. */
    parser.foreach_token(Using, [&](const Token &token) {
      report_error(ERROR_TOK(token), "Unsupported `using` keyword usage.");
    });

    return parser.result_get();
  }

  std::string namespace_separator_mutation(const std::string &str)
  {
    std::string out = str;

    /* Global namespace reference. */
    replace_all(out, " ::", "   ");
    /* Specific namespace reference.
     * Cannot use `__` because of some compilers complaining about reserved symbols. */
    replace_all(out, "::", "_");
    return out;
  }

  std::string preprocessor_directive_mutation(const std::string &str)
  {
    /* Remove unsupported directives. */
    std::regex regex(R"(#\s*(?:include|pragma once|pragma runtime_generated)[^\n]*)");
    return std::regex_replace(str, regex, "");
  }

  std::string swizzle_function_mutation(const std::string &str, report_callback &report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    parser.foreach_scope(ScopeType::Global, [&](Scope scope) {
      /* Change C++ swizzle functions into plain swizzle. */
      /** IMPORTANT: This prevent the usage of any method with a swizzle name. */
      scope.foreach_match(".w()", [&](const std::vector<Token> &tokens) {
        string method_name = tokens[1].str();
        if (method_name.length() > 1 && method_name.length() <= 4 &&
            (method_name.find_first_not_of("xyzw") == string::npos ||
             method_name.find_first_not_of("rgba") == string::npos))
        {
          /* `.xyz()` -> `.xyz` */
          /* Keep character count the same. Replace parenthesis by spaces. */
          parser.replace(tokens[2], tokens[3], "  ");
        }
      });
    });
    return parser.result_get();
  }

  void threadgroup_variables_parsing(const std::string &str)
  {
    std::regex regex(R"(shared\s+(\w+)\s+(\w+)([^;]*);)");
    regex_global_search(str, regex, [&](const std::smatch &match) {
      shared_vars_.push_back({match[1].str(), match[2].str(), match[3].str()});
    });
  }

  void parse_library_functions(const std::string &str)
  {
    using namespace metadata;
    std::regex regex_func(R"(void\s+(\w+)\s*\(([^)]+\))\s*\{)");
    regex_global_search(str, regex_func, [&](const std::smatch &match) {
      std::string name = match[1].str();
      std::string args = match[2].str();

      FunctionFormat fn;
      fn.name = name;

      std::regex regex_arg(R"((?:(const|in|out|inout)\s)?(\w+)\s([\w\[\]]+)(?:,|\)))");
      regex_global_search(args, regex_arg, [&](const std::smatch &arg) {
        std::string qualifier = arg[1].str();
        std::string type = arg[2].str();
        if (qualifier.empty() || qualifier == "const") {
          qualifier = "in";
        }
        fn.arguments.emplace_back(
            ArgumentFormat{metadata::Qualifier(hash(qualifier)), metadata::Type(hash(type))});
      });
      metadata.functions.emplace_back(fn);
    });
  }

  void parse_builtins(const std::string &str, const std::string &filename)
  {
    const bool skip_drw_debug = filename.find("draw_debug_draw_lib.glsl") != std::string::npos ||
                                filename.find("draw_debug_draw_display_vert.glsl") !=
                                    std::string::npos;
    using namespace metadata;
    /* TODO: This can trigger false positive caused by disabled #if blocks. */
    std::string tokens[] = {"gl_FragCoord",
                            "gl_FrontFacing",
                            "gl_GlobalInvocationID",
                            "gl_InstanceID",
                            "gl_LocalInvocationID",
                            "gl_LocalInvocationIndex",
                            "gl_NumWorkGroup",
                            "gl_PointCoord",
                            "gl_PointSize",
                            "gl_PrimitiveID",
                            "gl_VertexID",
                            "gl_WorkGroupID",
                            "gl_WorkGroupSize",
                            "drw_debug_",
#ifdef WITH_GPU_SHADER_ASSERT
                            "assert",
#endif
                            "printf"};
    for (auto &token : tokens) {
      if (skip_drw_debug && token == "drw_debug_") {
        continue;
      }
      if (str.find(token) != std::string::npos) {
        metadata.builtins.emplace_back(Builtin(hash(token)));
      }
    }
  }

  template<typename ReportErrorF>
  std::string printf_processing(const std::string &str, const ReportErrorF &report_error)
  {
    std::string out_str = str;
    {
      /* Example: `printf(2, b, f(c, d));` > `printf(2@ b@ f(c@ d))$` */
      size_t start, end = 0;
      while ((start = out_str.find("printf(", end)) != std::string::npos) {
        end = out_str.find(';', start);
        if (end == std::string::npos) {
          break;
        }
        out_str[end] = '$';
        int bracket_depth = 0;
        int arg_len = 0;
        for (size_t i = start; i < end; ++i) {
          if (out_str[i] == '(') {
            bracket_depth++;
          }
          else if (out_str[i] == ')') {
            bracket_depth--;
          }
          else if (bracket_depth == 1 && out_str[i] == ',') {
            out_str[i] = '@';
            arg_len++;
          }
        }
        if (arg_len > 99) {
          report_error(line_number(out_str, start),
                       char_number(out_str, start),
                       line_str(out_str, start),
                       "Too many parameters in printf. Max is 99.");
          break;
        }
        /* Encode number of arg in the `ntf` of `printf`. */
        out_str[start + sizeof("printf") - 4] = '$';
        out_str[start + sizeof("printf") - 3] = ((arg_len / 10) > 0) ? ('0' + arg_len / 10) : '$';
        out_str[start + sizeof("printf") - 2] = '0' + arg_len % 10;
      }
      if (end == 0) {
        /* No printf in source. */
        return str;
      }
    }
    /* Example: `pri$$1(2@ b)$` > `{int c_ = print_header(1, 2); c_ = print_data(c_, b); }` */
    {
      std::regex regex(R"(pri\$\$?(\d{1,2})\()");
      out_str = std::regex_replace(out_str, regex, "{uint c_ = print_header($1u, ");
    }
    {
      std::regex regex(R"(\@)");
      out_str = std::regex_replace(out_str, regex, "); c_ = print_data(c_,");
    }
    {
      std::regex regex(R"(\$)");
      out_str = std::regex_replace(out_str, regex, "; }");
    }
    return out_str;
  }

  std::string assert_processing(const std::string &str,
                                const std::string &filepath,
                                report_callback report_error)
  {
    std::string filename = std::regex_replace(filepath, std::regex(R"((?:.*)\/(.*))"), "$1");

    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);
    /* Example: `assert(i < 0)` > `if (!(i < 0)) { printf(...); }` */
    parser.foreach_match("w(..)", [&](const vector<Token> &tokens) {
      if (tokens[0].str() != "assert") {
        return;
      }
      string replacement;
#ifdef WITH_GPU_SHADER_ASSERT
      string condition = tokens[1].scope().str();
      replacement += "if (!" + condition + ") ";
      replacement += "{";
      replacement += " printf(\"";
      replacement += "Assertion failed: " + condition + ", ";
      replacement += "file " + filename + ", ";
      replacement += "line %d, ";
      replacement += "thread (%u,%u,%u).\\n";
      replacement += "\"";
      replacement += ", __LINE__, GPU_THREAD.x, GPU_THREAD.y, GPU_THREAD.z); ";
      replacement += "}";
#endif
      parser.replace(tokens[0], tokens[4], replacement);
    });
#ifndef WITH_GPU_SHADER_ASSERT
    (void)filename;
    (void)report_error;
#endif
    parser.apply_mutations();
    return parser.result_get();
  }

  /* String hash are outputted inside GLSL and needs to fit 32 bits. */
  static uint32_t hash_string(const std::string &str)
  {
    uint64_t hash_64 = metadata::hash(str);
    uint32_t hash_32 = uint32_t(hash_64 ^ (hash_64 >> 32));
    return hash_32;
  }

  std::string static_strings_merging(const std::string &str, report_callback report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);
    do {
      parser.foreach_match("__", [&](const std::vector<Token> &tokens) {
        string first = tokens[0].str();
        string second = tokens[1].str();
        string between = parser.substr_range_inclusive(
            tokens[0].str_index_last_no_whitespace() + 1, tokens[1].str_index_start() - 1);
        string trailing = parser.substr_range_inclusive(
            tokens[1].str_index_last_no_whitespace() + 1, tokens[1].str_index_last());
        string merged = first.substr(0, first.length() - 1) + second.substr(1) + between +
                        trailing;
        parser.replace_try(tokens[0], tokens[1], merged);
      });
    } while (parser.apply_mutations());

    return parser.result_get();
  }

  std::string static_strings_parsing_and_mutation(const std::string &str,
                                                  report_callback report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);
    parser.foreach_token(String, [&](const Token &token) {
      uint32_t hash = hash_string(token.str());
      metadata::PrintfFormat format = {hash, token.str()};
      metadata.printf_formats.emplace_back(format);
      parser.replace(token, std::to_string(hash) + 'u', true);
    });
    return parser.result_get();
  }

  /* Move all method definition outside of struct definition blocks. */
  std::string struct_method_mutation(const std::string &str, report_callback report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    parser.foreach_scope(ScopeType::Global, [&](Scope scope) {
      /* `class` -> `struct` */
      scope.foreach_match("S", [&](const std::vector<Token> &tokens) {
        parser.replace(tokens[0], tokens[0], "struct ");
      });
    });

    parser.apply_mutations();

    parser.foreach_scope(ScopeType::Global, [&](Scope scope) {
      scope.foreach_match("sw", [&](const std::vector<Token> &tokens) {
        const Token struct_name = tokens[1];

        if (struct_name.next() == ':') {
          report_error(struct_name.next().line_number(),
                       struct_name.next().char_number(),
                       struct_name.next().line_str(),
                       "class inheritance is not supported");
          return;
        }
        if (struct_name.next() != '{') {
          report_error(struct_name.line_number(),
                       struct_name.char_number(),
                       struct_name.line_str(),
                       "Expected `{`");
          return;
        }

        const Scope struct_scope = struct_name.next().scope();
        const Token struct_end = struct_scope.end().next();

        /* Erase `public:` and `private:` keywords. */
        struct_scope.foreach_match("v:", [&](const std::vector<Token> &tokens) {
          parser.erase(tokens[0].line_start(), tokens[1].line_end());
        });
        struct_scope.foreach_match("V:", [&](const std::vector<Token> &tokens) {
          parser.erase(tokens[0].line_start(), tokens[1].line_end());
        });

        struct_scope.foreach_match("ww(", [&](const std::vector<Token> &tokens) {
          if (tokens[0].prev() == Const) {
            report_error(tokens[0].prev().line_number(),
                         tokens[0].prev().char_number(),
                         tokens[0].prev().line_str(),
                         "function return type is marked `const` but it makes no sense for values "
                         "and returning reference is not supported");
            return;
          }

          const bool is_static = tokens[0].prev() == Static;
          const Token fn_start = is_static ? tokens[0].prev() : tokens[0];
          const Scope fn_args = tokens[2].scope();
          const Token after_args = fn_args.end().next();
          const bool is_const = after_args == Const;
          const Scope fn_body = (is_const ? after_args.next() : after_args).scope();

          string fn_content = parser.substr_range_inclusive(fn_start.line_start(),
                                                            fn_body.end().line_end() + 1);

          Parser fn_parser(fn_content, report_error);
          fn_parser.foreach_scope(ScopeType::Global, [&](Scope scope) {
            if (is_static) {
              scope.foreach_match("mww(", [&](const std::vector<Token> &tokens) {
                const Token fn_name = tokens[2];
                fn_parser.replace(fn_name, fn_name, struct_name.str() + "::" + fn_name.str());
                /* WORKAROUND: Erase the static keyword as it conflict with the wrapper class
                 * member accesses MSL. */
                fn_parser.erase(tokens[0]);
              });
            }
            else {
              scope.foreach_match("ww(", [&](const std::vector<Token> &tokens) {
                const Scope args = tokens[2].scope();
                const bool has_no_args = args.token_count() == 2;
                const char *suffix = (has_no_args ? "" : ", ");

                if (is_const) {
                  fn_parser.erase(args.end().next());
                  fn_parser.insert_after(args.start(),
                                         "const " + struct_name.str() + " this_" + suffix);
                }
                else {
                  fn_parser.insert_after(args.start(), struct_name.str() + " &this_" + suffix);
                }
              });
            }

            /* `*this` -> `this_` */
            scope.foreach_match("*T", [&](const std::vector<Token> &tokens) {
              fn_parser.replace(tokens[0], tokens[1], "this_");
            });
            /* `this->` -> `this_.` */
            scope.foreach_match("TD", [&](const std::vector<Token> &tokens) {
              fn_parser.replace(tokens[0], tokens[1], "this_.");
            });
          });

          string line_directive = "#line " + std::to_string(fn_start.line_number()) + '\n';
          parser.erase(fn_start.line_start(), fn_body.end().line_end());
          parser.insert_after(struct_end.line_end() + 1, line_directive + fn_parser.result_get());
        });

        string line_directive = "#line " + std::to_string(struct_end.line_number() + 1) + '\n';
        parser.insert_after(struct_end.line_end() + 1, line_directive);
      });
    });

    return parser.result_get();
  }

  /* Add padding member to empty structs.
   * Empty structs are useful for templating. */
  std::string empty_struct_mutation(const std::string &str, report_callback report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    parser.foreach_scope(ScopeType::Global, [&](Scope scope) {
      scope.foreach_match("sw{};", [&](const std::vector<Token> &tokens) {
        parser.insert_after(tokens[2], "int _pad;");
      });
    });

    return parser.result_get();
  }

  /* Transform `a.fn(b)` into `fn(a, b)`. */
  std::string method_call_mutation(const std::string &str, report_callback report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    do {
      parser.foreach_scope(ScopeType::Function, [&](Scope scope) {
        scope.foreach_match(".w(", [&](const std::vector<Token> &tokens) {
          const Token dot = tokens[0];
          const Token func = tokens[1];
          const Token par_open = tokens[2];
          const Token end_of_this = dot.prev();
          Token start_of_this = end_of_this;
          while (true) {
            if (start_of_this == ')') {
              /* Function call. Take argument scope and function name. No recursion. */
              start_of_this = start_of_this.scope().start().prev();
              break;
            }
            if (start_of_this == ']') {
              /* Array subscript. Take scope and continue. */
              start_of_this = start_of_this.scope().start().prev();
              continue;
            }
            if (start_of_this == Word) {
              /* Member. */
              if (start_of_this.prev() == '.') {
                start_of_this = start_of_this.prev().prev();
                /* Continue until we find root member. */
                continue;
              }
              /* End of chain. */
              break;
            }
            report_error(start_of_this.line_number(),
                         start_of_this.char_number(),
                         start_of_this.line_str(),
                         "method_call_mutation parsing error");
            break;
          }
          string this_str = parser.substr_range_inclusive(start_of_this, end_of_this);
          string func_str = func.str();
          const bool has_no_arg = par_open.next() == ')';
          /* `a.fn(b)` -> `fn(a, b)` */
          parser.replace_try(
              start_of_this, par_open, func_str + "(" + this_str + (has_no_arg ? "" : ", "));
        });
      });
    } while (parser.apply_mutations());

    return parser.result_get();
  }

  std::string stage_function_mutation(const std::string &str)
  {
    using namespace std;

    if (str.find("_function]]") == string::npos) {
      return str;
    }

    vector<pair<string, string>> mutations;

    int64_t line = 1;
    regex regex_attr(R"(\[\[gpu::(vertex|fragment|compute)_function\]\])");
    regex_global_search(str, regex_attr, [&](const smatch &match) {
      string prefix = match.prefix().str();
      string suffix = match.suffix().str();
      string attribute = match[0].str();
      string shader_stage = match[1].str();

      line += line_count(prefix);
      string signature = suffix.substr(0, suffix.find('{'));
      string body = '{' +
                    get_content_between_balanced_pair(suffix.substr(signature.size()), '{', '}') +
                    "}\n";

      string function = signature + body;

      string check = "defined(";
      if (shader_stage == "vertex") {
        check += "GPU_VERTEX_SHADER";
      }
      else if (shader_stage == "fragment") {
        check += "GPU_FRAGMENT_SHADER";
      }
      else if (shader_stage == "compute") {
        check += "GPU_COMPUTE_SHADER";
      }
      check += ")";

      string mutated = guarded_scope_mutation(
          string(attribute.size(), ' ') + function, line, check);
      mutations.emplace_back(attribute + function, mutated);
    });

    string out = str;
    for (auto mutation : mutations) {
      replace_all(out, mutation.first, mutation.second);
    }
    return out;
  }

  std::string resource_guard_mutation(const std::string &str, report_callback &report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    parser.foreach_function([&](bool, Token fn_type, Token, Scope, bool, Scope fn_body) {
      fn_body.foreach_match("w(w,", [&](const std::vector<Token> &tokens) {
        string func_name = tokens[0].str();
        if (func_name != "specialization_constant_get" && func_name != "shared_variable_get" &&
            func_name != "push_constant_get" && func_name != "interface_get" &&
            func_name != "attribute_get" && func_name != "buffer_get" &&
            func_name != "sampler_get" && func_name != "image_get")
        {
          return;
        }
        string info_name = tokens[2].str();
        Scope scope = tokens[0].scope();
        /* We can be in expression scope. Take parent scope until we find a local scope. */
        while (scope.type() != ScopeType::Function && scope.type() != ScopeType::Local) {
          scope = scope.scope();
        }

        if (scope.type() == ScopeType::Function) {
          guarded_scope_mutation(parser, scope, info_name, fn_type);
        }
        else {
          guarded_scope_mutation(parser, scope, info_name);
        }
      });
    });

    return parser.result_get();
  }

  void guarded_scope_mutation(parser::Parser &parser,
                              parser::Scope scope,
                              const std::string &info,
                              parser::Token fn_type = parser::Token::invalid())
  {
    using namespace std;
    using namespace shader::parser;

    string line_start = "#line " + std::to_string(scope.start().next().line_number()) + "\n";
    string line_end = "#line " + std::to_string(scope.end().line_number()) + "\n";

    string guard_start = "#if defined(CREATE_INFO_" + info + ")\n";
    string guard_else;
    if (fn_type.is_valid() && fn_type.str() != "void") {
      string type = fn_type.str();
      bool is_trivial = false;
      if (type == "float" || type == "float2" || type == "float3" || type == "float4" ||
          /**/
          type == "int" || type == "int2" || type == "int3" || type == "int4" ||
          /**/
          type == "uint" || type == "uint2" || type == "uint3" || type == "uint4" ||
          /**/
          type == "float2x2" || type == "float2x3" || type == "float2x4" ||
          /**/
          type == "float3x2" || type == "float3x3" || type == "float3x4" ||
          /**/
          type == "float4x2" || type == "float4x3" || type == "float4x4")
      {
        is_trivial = true;
      }
      guard_else += "#else\n";
      guard_else += line_start;
      guard_else += "  return " + type + (is_trivial ? "(0)" : "::zero()") + ";\n";
    }
    string guard_end = "#endif\n";

    parser.insert_after(scope.start().line_end() + 1, guard_start + line_start);
    parser.insert_before(scope.end().line_start(), guard_else + guard_end + line_end);
  };

  std::string guarded_scope_mutation(std::string content, int64_t line_start, std::string check)
  {
    int64_t line_end = line_start + line_count(content);
    std::string guarded_cope;
    guarded_cope += "#if " + check + "\n";
    guarded_cope += "#line " + std::to_string(line_start) + "\n";
    guarded_cope += content;
    guarded_cope += "#endif\n";
    guarded_cope += "#line " + std::to_string(line_end) + "\n";
    return guarded_cope;
  }

  std::string enum_macro_injection(const std::string &str,
                                   bool is_shared_file,
                                   report_callback &report_error)
  {
    /**
     * Transform C,C++ enum declaration into GLSL compatible defines and constants:
     *
     * \code{.cpp}
     * enum eMyEnum : uint {
     *   ENUM_1 = 0u,
     *   ENUM_2 = 1u,
     *   ENUM_3 = 2u,
     * };
     * \endcode
     *
     * becomes
     *
     * \code{.glsl}
     * #define eMyEnum uint
     * constant static constexpr uint ENUM_1 = 0u;
     * constant static constexpr uint ENUM_2 = 1u;
     * constant static constexpr uint ENUM_3 = 2u;
     *
     * \endcode
     *
     * It is made like so to avoid messing with error lines, allowing to point at the exact
     * location inside the source file.
     *
     * IMPORTANT: This has some requirements:
     * - Enums needs to have underlying types set to uint32_t to make them usable in UBO and SSBO.
     * - All values needs to be specified using constant literals to avoid compiler differences.
     * - All values needs to have the 'u' suffix to avoid GLSL compiler errors.
     */
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    auto missing_underlying_type = [&](vector<Token> tokens) {
      report_error(tokens[0].line_number(),
                   tokens[0].char_number(),
                   tokens[0].line_str(),
                   "enum declaration must explicitly use an underlying type");
    };

    parser.foreach_match("Mw{", missing_underlying_type);
    parser.foreach_match("MSw{", missing_underlying_type);

    auto process_enum =
        [&](Token enum_tok, Token class_tok, Token enum_name, Token enum_type, Scope enum_scope) {
          string type_str = enum_type.str();

          if (is_shared_file) {
            if (type_str != "uint32_t" && type_str != "int32_t") {
              report_error(
                  enum_type.line_number(),
                  enum_type.char_number(),
                  enum_type.line_str(),
                  "enum declaration must use uint32_t or int32_t underlying type for interface "
                  "compatibility");
              return;
            }
          }

          size_t insert_at = enum_scope.end().line_end();
          parser.erase(enum_tok.str_index_start(), insert_at);
          parser.insert_line_number(insert_at + 1, enum_tok.line_number());
          parser.insert_after(insert_at + 1,
                              "#define " + enum_name.str() + " " + enum_type.str() + "\n");

          enum_scope.foreach_scope(ScopeType::Assignment, [&](Scope scope) {
            string name = scope.start().prev().str();
            string value = scope.str();
            if (class_tok.is_valid()) {
              name = enum_name.str() + "::" + name;
            }
            string decl = "constant static constexpr " + type_str + " " + name + " " + value +
                          ";\n";
            parser.insert_line_number(insert_at + 1, scope.start().line_number());
            parser.insert_after(insert_at + 1, decl);
          });
          parser.insert_line_number(insert_at + 1, enum_scope.end().line_number() + 1);
        };

    parser.foreach_match("MSw:w{", [&](vector<Token> tokens) {
      process_enum(tokens[0], tokens[1], tokens[2], tokens[4], tokens[5].scope());
    });
    parser.foreach_match("Mw:w{", [&](vector<Token> tokens) {
      process_enum(tokens[0], Token::invalid(), tokens[1], tokens[3], tokens[4].scope());
    });

    parser.apply_mutations();

    parser.foreach_match("M", [&](vector<Token> tokens) {
      report_error(tokens[0].line_number(),
                   tokens[0].char_number(),
                   tokens[0].line_str(),
                   "invalid enum declaration");
    });
    return parser.result_get();
  }

  std::string strip_whitespace(const std::string &str) const
  {
    return str.substr(0, str.find_last_not_of(" \n") + 1);
  }

  /**
   * Expand functions with default arguments to function overloads.
   * Expects formatted input and that function bodies are followed by newline.
   */
  std::string default_argument_mutation(std::string str, report_callback &report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    parser.foreach_function(
        [&](bool, Token fn_type, Token fn_name, Scope fn_args, bool, Scope fn_body) {
          if (!fn_args.contains_token('=')) {
            return;
          }

          const bool has_non_void_return_type = fn_type.str() != "void";

          string args_decl;
          string args_names;

          vector<string> fn_overloads;

          fn_args.foreach_scope(ScopeType::FunctionArg, [&](Scope arg) {
            Token equal = arg.find_token('=');
            const char *comma = (args_decl.empty() ? "" : ", ");
            if (equal.is_invalid()) {
              args_decl += comma + arg.str();
              args_names += comma + arg.end().str();
            }
            else {
              string arg_name = equal.prev().str();
              string value = parser.substr_range_inclusive(equal.next(), arg.end());
              string decl = parser.substr_range_inclusive(arg.start(), equal.prev());

              string fn_call = fn_name.str() + '(' + args_names + comma + value + ");";
              if (has_non_void_return_type) {
                fn_call = "return " + fn_call;
              }
              string overload;
              overload += fn_type.str() + " ";
              overload += fn_name.str() + '(' + args_decl + ")\n";
              overload += "{\n";
              overload += "#line " + std::to_string(fn_type.line_number()) + "\n";
              overload += "  " + fn_call + "\n}\n";
              fn_overloads.emplace_back(overload);

              args_decl += comma + strip_whitespace(decl);
              args_names += comma + arg_name;
              /* Erase the value assignment and keep the declaration. */
              parser.erase(equal.scope());
            }
          });
          size_t end_of_fn_char = fn_body.end().line_end() + 1;
          /* Have to reverse the declaration order. */
          for (auto it = fn_overloads.rbegin(); it != fn_overloads.rend(); ++it) {
            parser.insert_line_number(end_of_fn_char, fn_type.line_number());
            parser.insert_after(end_of_fn_char, *it);
          }
          parser.insert_line_number(end_of_fn_char, fn_body.end().line_number() + 1);
        });

    return parser.result_get();
  }

  /* Used to make GLSL matrix constructor compatible with MSL in pyGPU shaders.
   * This syntax is not supported in blender's own shaders. */
  std::string matrix_constructor_mutation(const std::string &str)
  {
    if (str.find("mat") == std::string::npos) {
      return str;
    }
    /* Example: `mat2(x)` > `mat2x2(x)` */
    std::regex regex_parenthesis(R"(\bmat([234])\()");
    std::string out = std::regex_replace(str, regex_parenthesis, "mat$1x$1(");
    /* Only process square matrices since this is the only types we overload the constructors. */
    /* Example: `mat2x2(x)` > `__mat2x2(x)` */
    std::regex regex(R"(\bmat(2x2|3x3|4x4)\()");
    return std::regex_replace(out, regex, "__mat$1(");
  }

  /* To be run before `argument_decorator_macro_injection()`. */
  std::string argument_reference_mutation(std::string &str, report_callback &report_error)
  {
    using namespace std;
    using namespace shader::parser;

    Parser parser(str, report_error);

    auto add_mutation = [&](Token type, Token arg_name, Token last_tok) {
      if (type.prev() == Const) {
        parser.replace(type.prev(), last_tok, type.str() + " " + arg_name.str());
      }
      else {
        parser.replace(type, last_tok, "inout " + type.str() + " " + arg_name.str());
      }
    };

    parser.foreach_scope(ScopeType::FunctionArgs, [&](const Scope scope) {
      scope.foreach_match(
          "w(&w)", [&](const vector<Token> toks) { add_mutation(toks[0], toks[3], toks[4]); });
      scope.foreach_match(
          "w&w", [&](const vector<Token> toks) { add_mutation(toks[0], toks[2], toks[2]); });
      scope.foreach_match(
          "w&T", [&](const vector<Token> toks) { add_mutation(toks[0], toks[2], toks[2]); });
    });
    return parser.result_get();
  }

  /* To be run after `argument_reference_mutation()`. */
  std::string variable_reference_mutation(const std::string &str, report_callback report_error)
  {
    using namespace std;
    /* Processing regex and logic is expensive. Check if they are needed at all. */
    bool valid_match = false;
    string next_str = str;
    reference_search(next_str, [&](int parenthesis_depth, int /*bracket_depth*/, char &c) {
      /* Check if inside a function body. */
      if (parenthesis_depth == 0) {
        valid_match = true;
        /* Modify the & into @ to make sure we only match these references in the regex
         * below. @ being forbidden in the shader language, it is safe to use a temp
         * character. */
        c = '@';
      }
    });
    if (!valid_match) {
      return str;
    }
    string out_str;
    /* Example: `const float &var = value;` */
    regex regex_ref(R"(\ ?(?:const)?\s*\w+\s+\@(\w+) =\s*([^;]+);)");

    smatch match;
    while (regex_search(next_str, match, regex_ref)) {
      const string definition = match[0].str();
      const string name = match[1].str();
      const string value = match[2].str();
      const string prefix = match.prefix().str();
      const string suffix = match.suffix().str();

      out_str += prefix;

      /* Assert definition doesn't contain any side effect. */
      if (value.find("++") != string::npos || value.find("--") != string::npos) {
        report_error(line_number(match),
                     char_number(match),
                     line_str(match),
                     "Reference definitions cannot have side effects.");
        return str;
      }
      if (value.find("(") != string::npos) {
        if (value.find("specialization_constant_get(") == string::npos &&
            value.find("push_constant_get(") == string::npos &&
            value.find("interface_get(") == string::npos &&
            value.find("attribute_get(") == string::npos &&
            value.find("buffer_get(") == string::npos &&
            value.find("sampler_get(") == string::npos && value.find("image_get(") == string::npos)
        {
          report_error(line_number(match),
                       char_number(match),
                       line_str(match),
                       "Reference definitions cannot contain function calls.");
          return str;
        }
      }
      if (value.find("[") != string::npos) {
        const string index_var = get_content_between_balanced_pair(value, '[', ']');

        if (index_var.find(' ') != string::npos) {
          report_error(line_number(match),
                       char_number(match),
                       line_str(match),
                       "Array subscript inside reference declaration must be a single variable or "
                       "a constant, not an expression.");
          return str;
        }

        /* Add a space to avoid empty scope breaking the loop. */
        string scope_depth = " }";
        bool found_var = false;
        while (!found_var) {
          string scope = get_content_between_balanced_pair(out_str + scope_depth, '{', '}', true);
          scope_depth += '}';

          if (scope.empty()) {
            break;
          }
          /* Remove nested scopes. Avoid variable shadowing to mess with the detection. */
          scope = regex_replace(scope, regex(R"(\{[^\}]*\})"), "{}");
          /* Search if index variable definition qualifies it as `const`. */
          regex regex_definition(R"((const)? \w+ )" + index_var + " =");
          smatch match_definition;
          if (regex_search(scope, match_definition, regex_definition)) {
            found_var = true;
            if (match_definition[1].matched == false) {
              report_error(line_number(match),
                           char_number(match),
                           line_str(match),
                           "Array subscript variable must be declared as const qualified.");
              return str;
            }
          }
        }
        if (!found_var) {
          report_error(line_number(match),
                       char_number(match),
                       line_str(match),
                       "Cannot locate array subscript variable declaration. "
                       "If it is a global variable, assign it to a temporary const variable for "
                       "indexing inside the reference.");
          return str;
        }
      }

      /* Find scope this definition is active in. */
      const string scope = get_content_between_balanced_pair('{' + suffix, '{', '}');
      if (scope.empty()) {
        report_error(line_number(match),
                     char_number(match),
                     line_str(match),
                     "Reference is defined inside a global or unterminated scope.");
        return str;
      }
      string original = definition + scope;
      string modified = original;

      /* Replace definition by nothing. Keep number of lines. */
      string newlines(line_count(definition), '\n');
      replace_all(modified, definition, newlines);
      /* Replace every occurrence of the reference. Avoid matching other symbols like class members
       * and functions with the same name. */
      modified = regex_replace(
          modified, regex(R"(([^\.])\b)" + name + R"(\b([^(]))"), "$1" + value + "$2");

      /** IMPORTANT: `match` is invalid after the assignment. */
      next_str = definition + suffix;

      /* Replace whole modified scope in output string. */
      replace_all(next_str, original, modified);
    }
    out_str += next_str;
    return out_str;
  }

  std::string argument_decorator_macro_injection(const std::string &str)
  {
    /* Example: `out float var[2]` > `out float _out_sta var _out_end[2]` */
    std::regex regex(R"((out|inout|in|shared)\s+(\w+)\s+(\w+))");
    return std::regex_replace(str, regex, "$1 $2 _$1_sta $3 _$1_end");
  }

  std::string array_constructor_macro_injection(const std::string &str)
  {
    /* Example: `= float[2](0.0, 0.0)` > `= ARRAY_T(float) ARRAY_V(0.0, 0.0)` */
    std::regex regex(R"(=\s*(\w+)\s*\[[^\]]*\]\s*\()");
    return std::regex_replace(str, regex, "= ARRAY_T($1) ARRAY_V(");
  }

  /* TODO(fclem): Too many false positive and false negative to be applied to python shaders. */
  void matrix_constructor_linting(const std::string &str, report_callback report_error)
  {
    /* The following regex is expensive. Do a quick early out scan. */
    if (str.find("mat") == std::string::npos && str.find("float") == std::string::npos) {
      return;
    }
    /* Example: `mat4(other_mat)`. */
    std::regex regex(R"(\s(?:mat(?:\d|\dx\d)|float\dx\d)\()");
    regex_global_search(str, regex, [&](const std::smatch &match) {
      std::string args = get_content_between_balanced_pair("(" + match.suffix().str(), '(', ')');
      int arg_count = split_string_not_between_balanced_pair(args, ',', '(', ')').size();
      bool has_floating_point_arg = args.find('.') != std::string::npos;
      /* TODO(fclem): Check if arg count matches matrix type. */
      if (arg_count != 1 || has_floating_point_arg) {
        return;
      }
      /* This only catches some invalid usage. For the rest, the CI will catch them. */
      const char *msg =
          "Matrix constructor is not cross API compatible. "
          "Use to_floatNxM to reshape the matrix or use other constructors instead.";
      report_error(line_number(match), char_number(match), line_str(match), msg);
    });
  }

  /* Assume formatted source with our code style. Cannot be applied to python shaders. */
  void global_scope_constant_linting(const std::string &str, report_callback report_error)
  {
    /* Example: `const uint global_var = 1u;`. Matches if not indented (i.e. inside a scope). */
    std::regex regex(R"(const \w+ \w+ =)");
    regex_global_search(str, regex, [&](const std::smatch &match) {
      /* Positive look-behind is not supported in #std::regex. Do it manually. */
      if (match.prefix().str().back() == '\n') {
        const char *msg =
            "Global scope constant expression found. These get allocated per-thread in MSL. "
            "Use Macro's or uniforms instead.";
        report_error(line_number(match), char_number(match), line_str(match), msg);
      }
    });
  }

  void quote_linting(const std::string &str, report_callback report_error)
  {
    std::regex regex(R"(["'])");
    regex_global_search(str, regex, [&](const std::smatch &match) {
      /* This only catches some invalid usage. For the rest, the CI will catch them. */
      const char *msg = "Quotes are forbidden in GLSL.";
      report_error(line_number(match), char_number(match), line_str(match), msg);
    });
  }

  void array_constructor_linting(const std::string &str, report_callback report_error)
  {
    std::regex regex(R"(=\s*(\w+)\s*\[[^\]]*\]\s*\()");
    regex_global_search(str, regex, [&](const std::smatch &match) {
      /* This only catches some invalid usage. For the rest, the CI will catch them. */
      const char *msg =
          "Array constructor is not cross API compatible. Use type_array instead of type[].";
      report_error(line_number(match), char_number(match), line_str(match), msg);
    });
  }

  template<typename ReportErrorF>
  void small_type_linting(const std::string &str, const ReportErrorF &report_error)
  {
    std::regex regex(R"(\su?(char|short|half)(2|3|4)?\s)");
    regex_global_search(str, regex, [&](const std::smatch &match) {
      report_error(line_number(match),
                   char_number(match),
                   line_str(match),
                   "Small types are forbidden in shader interfaces.");
    });
  }

  std::string threadgroup_variables_suffix()
  {
    if (shared_vars_.empty()) {
      return "";
    }

    std::stringstream suffix;
    /**
     * For Metal shaders to compile, shared (threadgroup) variable cannot be declared globally.
     * They must reside within a function scope. Hence, we need to extract these declarations and
     * generate shared memory blocks within the entry point function. These shared memory blocks
     * can then be passed as references to the remaining shader via the class function scope.
     *
     * The shared variable definitions from the source file are replaced with references to
     * threadgroup memory blocks (using _shared_sta and _shared_end macros), but kept in-line in
     * case external macros are used to declare the dimensions.
     *
     * Each part of the codegen is stored inside macros so that we don't have to do string
     * replacement at runtime.
     */
    suffix << "\n";
    /* Arguments of the wrapper class constructor. */
    suffix << "#undef MSL_SHARED_VARS_ARGS\n";
    /* References assignment inside wrapper class constructor. */
    suffix << "#undef MSL_SHARED_VARS_ASSIGN\n";
    /* Declaration of threadgroup variables in entry point function. */
    suffix << "#undef MSL_SHARED_VARS_DECLARE\n";
    /* Arguments for wrapper class constructor call. */
    suffix << "#undef MSL_SHARED_VARS_PASS\n";

    /**
     * Example replacement:
     *
     * \code{.cc}
     * // Source
     * shared float bar[10];                                    // Source declaration.
     * shared float foo;                                        // Source declaration.
     * // Rest of the source ...
     * // End of Source
     *
     * // Backend Output
     * class Wrapper {                                          // Added at runtime by backend.
     *
     * threadgroup float (&foo);                                // Replaced by regex and macros.
     * threadgroup float (&bar)[10];                            // Replaced by regex and macros.
     * // Rest of the source ...
     *
     * Wrapper (                                                // Added at runtime by backend.
     * threadgroup float (&_foo), threadgroup float (&_bar)[10] // MSL_SHARED_VARS_ARGS
     * )                                                        // Added at runtime by backend.
     * : foo(_foo), bar(_bar)                                   // MSL_SHARED_VARS_ASSIGN
     * {}                                                       // Added at runtime by backend.
     *
     * }; // End of Wrapper                                     // Added at runtime by backend.
     *
     * kernel entry_point() {                                   // Added at runtime by backend.
     *
     * threadgroup float foo;                                   // MSL_SHARED_VARS_DECLARE
     * threadgroup float bar[10]                                // MSL_SHARED_VARS_DECLARE
     *
     * Wrapper wrapper                                          // Added at runtime by backend.
     * (foo, bar)                                               // MSL_SHARED_VARS_PASS
     * ;                                                        // Added at runtime by backend.
     *
     * }                                                        // Added at runtime by backend.
     * // End of Backend Output
     * \endcode
     */
    std::stringstream args, assign, declare, pass;

    bool first = true;
    for (SharedVar &var : shared_vars_) {
      char sep = first ? ' ' : ',';

      args << sep << "threadgroup " << var.type << "(&_" << var.name << ")" << var.array;
      assign << (first ? ':' : ',') << var.name << "(_" << var.name << ")";
      declare << "threadgroup " << var.type << ' ' << var.name << var.array << ";";
      pass << sep << var.name;
      first = false;
    }

    suffix << "#define MSL_SHARED_VARS_ARGS " << args.str() << "\n";
    suffix << "#define MSL_SHARED_VARS_ASSIGN " << assign.str() << "\n";
    suffix << "#define MSL_SHARED_VARS_DECLARE " << declare.str() << "\n";
    suffix << "#define MSL_SHARED_VARS_PASS (" << pass.str() << ")\n";
    suffix << "\n";

    return suffix.str();
  }

  std::string line_directive_prefix(const std::string &filepath)
  {
    std::string filename = std::regex_replace(filepath, std::regex(R"((?:.*)\/(.*))"), "$1");

    std::stringstream suffix;
    /* NOTE: This is not supported by GLSL. All line directives are muted at runtime and the
     * sources are scanned after error reporting for the locating the muted line. */
    suffix << "#line 1 \"" << filename << "\"\n";
    return suffix.str();
  }

  /* Made public for unit testing purpose. */
 public:
  static std::string get_content_between_balanced_pair(const std::string &input,
                                                       char start_delimiter,
                                                       char end_delimiter,
                                                       const bool backwards = false)
  {
    int balance = 0;
    size_t start = std::string::npos;
    size_t end = std::string::npos;

    if (backwards) {
      std::swap(start_delimiter, end_delimiter);
    }

    for (size_t i = 0; i < input.length(); ++i) {
      size_t idx = backwards ? (input.length() - 1) - i : i;
      if (input[idx] == start_delimiter) {
        if (balance == 0) {
          start = idx;
        }
        balance++;
      }
      else if (input[idx] == end_delimiter) {
        balance--;
        if (balance == 0 && start != std::string::npos) {
          end = idx;
          if (backwards) {
            std::swap(start, end);
          }
          return input.substr(start + 1, end - start - 1);
        }
      }
    }
    return "";
  }

  /* Replaces all occurrences of `from` by `to` between `start_delimiter`
   * and `end_delimiter` even inside nested delimiters pair. */
  static std::string replace_char_between_balanced_pair(const std::string &input,
                                                        const char start_delimiter,
                                                        const char end_delimiter,
                                                        const char from,
                                                        const char to)
  {
    int depth = 0;

    std::string str = input;
    for (char &string_char : str) {
      if (string_char == start_delimiter) {
        depth++;
      }
      else if (string_char == end_delimiter) {
        depth--;
      }
      else if (depth > 0 && string_char == from) {
        string_char = to;
      }
    }
    return str;
  }

  /* Function to split a string by a delimiter and return a vector of substrings. */
  static std::vector<std::string> split_string(const std::string &str, const char delimiter)
  {
    std::vector<std::string> substrings;
    std::stringstream ss(str);
    std::string item;

    while (std::getline(ss, item, delimiter)) {
      substrings.push_back(item);
    }
    return substrings;
  }

  /* Similar to split_string but only split if the delimiter is not between any pair_start and
   * pair_end. */
  static std::vector<std::string> split_string_not_between_balanced_pair(const std::string &str,
                                                                         const char delimiter,
                                                                         const char pair_start,
                                                                         const char pair_end)
  {
    const char safe_char = '@';
    const std::string safe_str = replace_char_between_balanced_pair(
        str, pair_start, pair_end, delimiter, safe_char);
    std::vector<std::string> split = split_string(safe_str, delimiter);
    for (std::string &str : split) {
      replace_all(str, safe_char, delimiter);
    }
    return split;
  }

  static void replace_all(std::string &str, const std::string &from, const std::string &to)
  {
    if (from.empty()) {
      return;
    }
    size_t start_pos = 0;
    while ((start_pos = str.find(from, start_pos)) != std::string::npos) {
      str.replace(start_pos, from.length(), to);
      start_pos += to.length();
    }
  }

  static void replace_all(std::string &str, const char from, const char to)
  {
    for (char &string_char : str) {
      if (string_char == from) {
        string_char = to;
      }
    }
  }

  static int64_t char_count(const std::string &str, char c)
  {
    return std::count(str.begin(), str.end(), c);
  }

  static int64_t line_count(const std::string &str)
  {
    return char_count(str, '\n');
  }

  /* Match any reference definition (e.g. `int &a = b`).
   * Call the callback function for each `&` character that matches a reference definition.
   * Expects the input `str` to be formatted with balanced parenthesis and curly brackets. */
  static void reference_search(std::string &str, std::function<void(int, int, char &)> callback)
  {
    scopes_scan_for_char(
        str, '&', [&](size_t pos, int parenthesis_depth, int bracket_depth, char &c) {
          if (pos > 0 && pos <= str.length() - 2) {
            /* This is made safe by the previous check. */
            char prev_char = str[pos - 1];
            char next_char = str[pos + 1];
            /* Validate it is not an operator (`&`, `&&`, `&=`). */
            if (prev_char == ' ' || prev_char == '(') {
              if (next_char != ' ' && next_char != '\n' && next_char != '&' && next_char != '=') {
                callback(parenthesis_depth, bracket_depth, c);
              }
            }
          }
        });
  }

  /* Match any default argument definition (e.g. `void func(int a = 0)`).
   * Call the callback function for each `=` character inside a function argument list.
   * Expects the input `str` to be formatted with balanced parenthesis and curly brackets. */
  static void default_argument_search(std::string &str,
                                      std::function<void(int, int, char &)> callback)
  {
    scopes_scan_for_char(
        str, '=', [&](size_t pos, int parenthesis_depth, int bracket_depth, char &c) {
          if (pos > 0 && pos <= str.length() - 2) {
            /* This is made safe by the previous check. */
            char prev_char = str[pos - 1];
            char next_char = str[pos + 1];
            /* Validate it is not an operator (`==`, `<=`, `>=`). Expects formatted input. */
            if (prev_char == ' ' && next_char == ' ') {
              if (parenthesis_depth == 1 && bracket_depth == 0) {
                callback(parenthesis_depth, bracket_depth, c);
              }
            }
          }
        });
  }

  /* Scan through a string matching for every occurrence of a character.
   * Calls the callback with the context in which the match occurs. */
  static void scopes_scan_for_char(std::string &str,
                                   char search_char,
                                   std::function<void(size_t, int, int, char &)> callback)
  {
    size_t pos = 0;
    int parenthesis_depth = 0;
    int bracket_depth = 0;
    for (char &c : str) {
      if (c == search_char) {
        callback(pos, parenthesis_depth, bracket_depth, c);
      }
      else if (c == '(') {
        parenthesis_depth++;
      }
      else if (c == ')') {
        parenthesis_depth--;
      }
      else if (c == '{') {
        bracket_depth++;
      }
      else if (c == '}') {
        bracket_depth--;
      }
      pos++;
    }
  }

  /* Return the line number this token is found at. Take into account the #line directives. */
  static size_t line_number(const std::string &file_str, size_t pos)
  {
    std::string sub_str = file_str.substr(0, pos);
    std::string directive = "#line ";
    size_t nearest_line_directive = sub_str.rfind(directive);
    size_t line_count = 1;
    if (nearest_line_directive != std::string::npos) {
      sub_str = sub_str.substr(nearest_line_directive + directive.size());
      line_count = std::stoll(sub_str) - 1;
    }
    return line_count + std::count(sub_str.begin(), sub_str.end(), '\n');
  }
  static size_t line_number(const std::smatch &smatch)
  {
    std::string whole_file = smatch.prefix().str() + smatch[0].str() + smatch.suffix().str();
    return line_number(whole_file, smatch.prefix().str().size());
  }

  /* Return the offset to the start of the line. */
  static size_t char_number(const std::string &file_str, size_t pos)
  {
    std::string sub_str = file_str.substr(0, pos);
    size_t nearest_line_directive = sub_str.find_last_of("\n");
    return (nearest_line_directive == std::string::npos) ?
               (sub_str.size() - 1) :
               (sub_str.size() - nearest_line_directive);
  }
  static size_t char_number(const std::smatch &smatch)
  {
    std::string whole_file = smatch.prefix().str() + smatch[0].str() + smatch.suffix().str();
    return char_number(whole_file, smatch.prefix().str().size());
  }

  /* Return the line the token is at. */
  static std::string line_str(const std::string &file_str, size_t pos)
  {
    size_t start = file_str.rfind('\n', pos);
    size_t end = file_str.find('\n', pos);
    if (start == std::string::npos) {
      start = 0;
    }
    return file_str.substr(start, end - start);
  }
  static std::string line_str(const std::smatch &smatch)
  {
    std::string whole_file = smatch.prefix().str() + smatch[0].str() + smatch.suffix().str();
    return line_str(whole_file, smatch.prefix().str().size());
  }
};

}  // namespace blender::gpu::shader
