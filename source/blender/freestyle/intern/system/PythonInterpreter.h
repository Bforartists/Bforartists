//
//  Filename         : PythonInterpreter.h
//  Author(s)        : Emmanuel Turquin
//  Purpose          : Python Interpreter
//  Date of creation : 17/04/2003
//
///////////////////////////////////////////////////////////////////////////////


//
//  Copyright (C) : Please refer to the COPYRIGHT file distributed 
//   with this source distribution. 
//
//  This program is free software; you can redistribute it and/or
//  modify it under the terms of the GNU General Public License
//  as published by the Free Software Foundation; either version 2
//  of the License, or (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
//
///////////////////////////////////////////////////////////////////////////////

#ifndef  PYTHON_INTERPRETER_H
# define PYTHON_INTERPRETER_H

# include <iostream>
# include <Python.h>
# include "StringUtils.h"
# include "Interpreter.h"

//soc
extern "C" {
#include "MEM_guardedalloc.h"
#include "BKE_main.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_report.h"
#include "BKE_text.h"
#include "BKE_library.h"
#include "BPY_extern.h"
}

class LIB_SYSTEM_EXPORT PythonInterpreter : public Interpreter
{
 public:

  PythonInterpreter() {
    _language = "Python";
    //Py_Initialize();
  }

  virtual ~PythonInterpreter() {
    //Py_Finalize();
  }

  int interpretFile(const string& filename) {

	bContext* C = CTX_create();
	ReportList* reports = (ReportList*) MEM_mallocN(sizeof(ReportList), "freestyleExecutionReportList");
	
	initPath(C);
	
	BKE_reports_init(reports, RPT_ERROR);
	char *fn = const_cast<char*>(filename.c_str());

	int status = BPY_run_python_script( C, fn, NULL, reports);

	if (status != 1) {
		cout << "\nError executing Python script from PythonInterpreter::interpretFile" << endl;
		cout << "File: " << fn << endl;
		cout << "Errors: " << endl;
		BKE_reports_print(reports, RPT_ERROR);
		return 1;
	}

	// cleaning up
	CTX_free( C );
	BKE_reports_clear(reports);
	if ((reports->flag & RPT_FREE) == 0)
	{
		MEM_freeN(reports);
	}
	
	return 0;
  }

  struct Options
  {
    static void setPythonPath(const string& path) {
      _path = path;
    }

    static string getPythonPath() {
      return _path;
    }
  };

  void reset() {
    Py_Finalize();
    Py_Initialize();
    _initialized = false;
  }

private:

  static void initPath(bContext* C) {
	if (_initialized)
		return;

	vector<string> pathnames;
	StringUtils::getPathName(_path, "", pathnames);
	
	struct Text *text = add_empty_text("tmp_freestyle_initpath.txt");
	string cmd = "import sys\n";
	txt_insert_buf(text, const_cast<char*>(cmd.c_str()));
	
	for (vector<string>::const_iterator it = pathnames.begin(); it != pathnames.end();++it) {
		if ( !it->empty() ) {
			cout << "Adding Python path: " << *it << endl;
			cmd = "sys.path.append(r\"" + *it + "\")\n";
			txt_insert_buf(text, const_cast<char*>(cmd.c_str()));
		}
	}
	
	BPY_run_python_script( C, NULL, text, NULL);
	
	// cleaning up
	unlink_text(G.main, text);
	free_libblock(&G.main->text, text);
	
	//PyRun_SimpleString("from Freestyle import *");
    _initialized = true;
  }

  static bool	_initialized;
  static string _path;
};

#endif // PYTHON_INTERPRETER_H
