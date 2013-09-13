
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

   static std::string              libraryVersion();                        //returns version string of Galil class library for display (e.g. "0.0.4.3 Jan 2 2008 16:04:50 libGalil.so").  Can be called WITHOUT an instance of Galil.  Note that this has nothing to do with the version of the controller (which can be found with connection() below).
   static std::vector<std::string> addresses();                             //returns list of available addresses to connect to (e.g. "1.2.3.4").  Each item in the list may be fed to the constructor Galil()

                                   Galil(std::string address = "");  //constructor opens connection with controller e.g. 192.168.1.2, COM1, /dev/ttyS0, GALILPCI1 /dev/galilpci0 (default constructor with no arguments will bring up a dialog)
                                  ~Galil();                                 //destructor closes connection with controller
   std::string                     connection();                            //returns a string like "DMC4080 Rev 1.0, 123, 10.0.0.70, IHA"

   int                             timeout_ms; //default = 500 milliseconds.  This is the timeout for everything but BP, BV, RS, ^R^S, and program/array/firmware download
   std::string                     command(     const std::string& command = "MG TIME", const std::string& terminator = "\r", const std::string& ack = ":", bool trim = true); //send a command (e.g. "MG _RPX") to the controller and get the response
   double                          commandValue(const std::string& command = "MG TIME"); //convenience method that converts response from string to numerical value
   std::string                     message(  int timeout_ms = 500); //ms.  get MGs from controller program
   int                             interrupt(int timeout_ms = 500); //ms.  EI, UI (DMC-18xx only).  Returns status byte (e.g. 0xf0 for UI0)

   std::string                     programUpload();                                                 //UL upload   a controller program to   an in-memory buffer
   void                            programDownload(    const std::string& program = "MG TIME\rEN"); //DL download a controller program from an in-memory buffer
   void                            programUploadFile(  const std::string& file    = "program.dmc"); //UL upload   a controller program to   a disk file
   void                            programDownloadFile(const std::string& file    = "program.dmc"); //DL download a controller program from a disk file

   std::vector<double>             arrayUpload(                                              const std::string& name  = "array"); //QU upload   an array to   an in-memory buffer
   void                            arrayDownload(    const std::vector<double>& array,       const std::string& name  = "array"); //QD download an array from an in-memory buffer
   void                            arrayUploadFile(  const std::string& file = "arrays.csv", const std::string& names = "");      //QU upload   array(s) to   a disk file.  "" means upload all arrays, else separate the array names with a space
   void                            arrayDownloadFile(const std::string& file = "arrays.csv");                                     //QD download array(s) from a disk file

   void                            firmwareDownloadFile(const std::string& file = "firmware.hex"); //download hex file (RS-232 only for DMC-21x3)

   int                             write(const std::string& bytes = "\r");  //returns actual number of bytes written
   std::string                     read();                                  //returns actual bytes read

   std::vector<std::string>        sources();                           //returns list of sources (_RPA...) supported by this controller, which are fed to sourceValue(), source(), and setSource()
   void                            recordsStart(double period_ms = -1); //milliseconds.  Sends DR.  -1 means leave be if not 0, else run as fast as possible.  > 0 sets the DR sample period in true milliseconds (rounded to nearest power of 2 for DMC-18xx).  0 sets DR0 (turns it off)
   std::vector<char>               record(const std::string& method = "QR"); //reads DR packet OR sends QR and reads response
   double                          sourceValue(const std::vector<char>& record,          const std::string& source = "TIME"); //get the value for one particular source (e.g. _RPA is 1000)
   std::string                     source(     const std::string& field = "Description", const std::string& source = "TIME"); //get e.g. the description string for one particular source (e.g. _RPA is "Axis A reference position").  Fields are "Description", "Units", & "Scale"
   void                            setSource(  const std::string& field = "Description", const std::string& source = "TIME", const std::string& to = "Sample counter"); //set e.g. the description string for one particular source (e.g. _RPA to "Feed axis reference position").  Fields are "Description", "Units", & "Scale"

};
