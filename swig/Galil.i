
%include <std_string.i>
%include <std_vector.i>
%include <typemaps.i>
%include <exception.i>

%module Galil
%{
	#include <Galil.h>
	#include <vector>
	#include <string>
	#include <iostream>
%}

%{
	#define SWIG_FILE_WITH_INIT
	static PyObject* TimeoutError;
	static PyObject* CommandError;
	static PyObject* MonitorError;
	static PyObject* FileError;
	static PyObject* OpenError;
	static PyObject* WrongbusError;
	static PyObject* InvalidError;
	static PyObject* WarningError;
	static PyObject* OfflineError;
	static PyObject* UnknownError;
%}

%init %{
	TimeoutError    = PyErr_NewException("_Galil.TimeoutError",  NULL, NULL);Py_INCREF(TimeoutError );PyModule_AddObject(m, "TimeoutError",  TimeoutError );
	CommandError    = PyErr_NewException("_Galil.CommandError",  NULL, NULL);Py_INCREF(CommandError );PyModule_AddObject(m, "CommandError",  CommandError );
	MonitorError    = PyErr_NewException("_Galil.MonitorError",  NULL, NULL);Py_INCREF(MonitorError );PyModule_AddObject(m, "MonitorError",  MonitorError );
	FileError       = PyErr_NewException("_Galil.FileError",     NULL, NULL);Py_INCREF(FileError    );PyModule_AddObject(m, "FileError",     FileError    );
	OpenError       = PyErr_NewException("_Galil.OpenError",     NULL, NULL);Py_INCREF(OpenError    );PyModule_AddObject(m, "OpenError",     OpenError    );
	WrongbusError   = PyErr_NewException("_Galil.WrongbusError", NULL, NULL);Py_INCREF(WrongbusError);PyModule_AddObject(m, "WrongbusError", WrongbusError);
	InvalidError    = PyErr_NewException("_Galil.InvalidError",  NULL, NULL);Py_INCREF(InvalidError );PyModule_AddObject(m, "InvalidError",  InvalidError );
	WarningError    = PyErr_NewException("_Galil.WarningError",  NULL, NULL);Py_INCREF(WarningError );PyModule_AddObject(m, "WarningError",  WarningError );
	OfflineError    = PyErr_NewException("_Galil.OfflineError",  NULL, NULL);Py_INCREF(OfflineError );PyModule_AddObject(m, "OfflineError",  OfflineError );
	UnknownError    = PyErr_NewException("_Galil.UnknownError",  NULL, NULL);Py_INCREF(UnknownError );PyModule_AddObject(m, "UnknownError",  UnknownError );
%}

%exception{
	try{
		$action
	}catch(std::string s){
		int c = atoi(s.substr(0, 1).c_str());
		switch(c){
			case 1:  PyErr_SetString(TimeoutError,  const_cast<char*>(s.c_str())); return NULL;
			case 2:  PyErr_SetString(CommandError,  const_cast<char*>(s.c_str())); return NULL;
			case 3:  PyErr_SetString(MonitorError,  const_cast<char*>(s.c_str())); return NULL;
			case 4:  PyErr_SetString(FileError,     const_cast<char*>(s.c_str())); return NULL;
			case 5:  PyErr_SetString(OpenError,     const_cast<char*>(s.c_str())); return NULL;
			case 6:  PyErr_SetString(WrongbusError, const_cast<char*>(s.c_str())); return NULL;
			case 7:  PyErr_SetString(InvalidError,  const_cast<char*>(s.c_str())); return NULL;
			case 8:  PyErr_SetString(WarningError,  const_cast<char*>(s.c_str())); return NULL;
			case 9:  PyErr_SetString(OfflineError,  const_cast<char*>(s.c_str())); return NULL;
			default: PyErr_SetString(UnknownError,  const_cast<char*>(s.c_str())); return NULL;
		}
	}
}

%pythoncode %{
	TimeoutError  = _Galil.TimeoutError
	CommandError  = _Galil.CommandError
	MonitorError  = _Galil.MonitorError
	FileError     = _Galil.FileError
	OpenError     = _Galil.OpenError
	WrongbusError = _Galil.WrongbusError
	InvalidError  = _Galil.InvalidError
	WarningError  = _Galil.WarningError
	OfflineError  = _Galil.OfflineError
	UnknownError  = _Galil.UnknownError
%}

#ifdef _MSC_VER
	#ifdef MAKEDLL
		#define DLL_IMPORT_EXPORT __declspec(dllexport)
	#else
		#define DLL_IMPORT_EXPORT
	#endif
#else
	#define DLL_IMPORT_EXPORT
#endif

namespace std{
	%template(IntVector) vector<int>;
	%template(DoubleVector) vector<double>;
	%template(CharVector) vector<char>;
	%template(StringVector) vector<string>;
}

class Galil
{
public:
	static std::string libraryVersion();
	static std::vector<std::string> addresses();
	Galil(const std::string& address = "");
	~Galil();
	std::string connection();
	int timeout_ms;
	std::string command(const std::string& command = "MG TIME", const std::string& terminator = "\r", const std::string& ack = ":", bool trim = true);
	double commandValue(const std::string& command = "MG TIME");
	std::string message(  int timeout_ms = 500);
	int interrupt(int timeout_ms = 500);
	std::string programUpload();
	void programDownload(const std::string& program = "MG TIME\rEN");
	void programUploadFile(const std::string& file = "program.dmc");
	void programDownloadFile(const std::string& file = "program.dmc");
	std::vector<double> arrayUpload(const std::string& name = "array");
	void arrayDownload(const std::vector<double>& array, const std::string& name = "array");
	void arrayUploadFile(const std::string& file, const std::string& names = "");
	void arrayDownloadFile(const std::string& file = "arrays.csv");
	void firmwareDownloadFile(const std::string& file = "firmware.hex");
	int write(const std::string& bytes = "\r");
	std::string read();
	std::vector<std::string> sources();
	void recordsStart(double period_ms = -1);
	std::vector<char> record(const std::string& method = "QR");
	double sourceValue(const std::vector<char>& record, const std::string& source = "TIME");
	std::string source(const std::string& field = "Description", const std::string& source = "TIME");
	void setSource(const std::string& field = "Description", const std::string& source = "TIME", const std::string& to = "Sample counter");
};

