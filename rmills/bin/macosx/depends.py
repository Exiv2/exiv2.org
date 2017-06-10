#!/usr/bin/python
from __future__ import print_function

r"""depends.py - find the ordered dependancies of a library/executable (deepest first)

To use this:
	depends.py [options]+ <pathtolibrary/pathtoexecutable/pathotoapp>

"""
__author__	= "Robin Mills <robin@clanmills.com>"

import string
import os
import sys
import optparse
from sets import Set

global version, options
version="2017-06-10"

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

##
# recursively update dependdict for libname (which can be @executable_path etc)
# execdir is the directory of @executable_path
# loaddir is the directory of @loader_path
# returns path to libname or '' (empty string)
def depend(execdir,loaddir,libname,dependdict):
	""" recursive descent of the libraries """

	global options

	##
	# discover libpath for libname
	epath='@executable_path/'
	lpath='@loader_path/'
	rpath='@rpath/'
	libpath=libname
	if libname[:len(epath)] == epath:
		libpath=os.path.join(execdir,libname[len(epath):])
	if libname[:len(lpath)] == lpath:
		libpath=os.path.join(loaddir,libname[len(lpath):])
	if libname[:len(rpath)] == rpath:
		libpath=os.path.join(loaddir,libname[len(rpath):])
	libpath=os.path.abspath(libpath)

	if os.path.isfile(libpath):
		if not dependdict.has_key(libpath):
			dependdict[libpath]=Set([])                 # push now to prevent infinite loop in recursion
			cmd = 'otool -L "%s"' % libpath         	# otool -L prints library dependancies:
														# libpath:
														# <tab>dependancy (metadata) ...
			for line in os.popen(cmd).readlines():      # run cmd
				if line[:1]=='\t':                      # parse <tab>dependancy (metadata)
					dependancy=line.split()[0]
					# print libpath,' => ',dependancy
					# recurse to find dependancies of dependancy
					dpath=depend(execdir,loaddir,dependancy,dependdict)
					dependdict[libpath].add(dpath)      # update dependdict from recursion
	else:
		print("depend: execdir=%s, loaddir=%s, libname=%s" % (execdir,loaddir,libname))
		print("*** error NOT a FILE libname=%s libpath=%s ***" % (libname,libpath))
		libpath=''

	return libpath

##
#
def tsort(dependdict): # returns (ordered) array of libraries
	filename='/tmp/tsortXX.txt'
	file=open(filename,'w')
	for key in dependdict.keys():
		depends=dependdict[key]
		for d in depends:
			if len(d) > 0:
				D=d.replace(' ','*');
				K=key.replace(' ','*')
				file.write( '%s %s\n' % (K,D) )
	file.close()
	cmd='tsort "%s" 2>/dev/null' % (filename)
	lines=os.popen(cmd).readlines()
	lines.reverse()

	result=[]
	for line in lines:
		line=line[:-1].replace('*',' ')
		result.append(line)
	return result;
#
##

##
#
def main():
	global options
	##
	# set up argument parser
	usage = "usage: %prog [options]+ target"
	parser = optparse.OptionParser(usage)

	parser.add_option('-V', '--version'		, action='store_true' , dest='version' ,help='report version'     )
	parser.add_option('-v', '--verbose'		, action='store_true' , dest='verbose' ,help='verbose output'	  )
	parser.add_option('-d', '--deploy'		, action='store_true' , dest='deploy'  ,help='update the bundle'  )
	parser.add_option('-D', '--depends'	    , action='store_true' , dest='depends' ,help='report dependancies')

	##
	# parse and test for errors
	(options, args) = parser.parse_args()

	if options.version:
		global version
		print('version: %s' % (version))
		exit(0)

	if len(args) != 1:
		parser.print_help()
		return

	if not options.depends and not options.deploy:
		options.depends=True

	##
	# dependdict key is a library path.  Value is a set of dependant library paths
	dependdict   = {}  # dependdict['/usr/lib/foo.dylib'] = Set([ '/usr/lib/a.dylib', ... ])
	libname      = args[0]
	execname     = ''
	if os.path.isdir(libname):
		execname = os.path.basename(os.path.abspath(libname)).strip('.app');
		execname = os.path.join(libname,'Contents/MacOS/',execname)
		if os.path.isfile(execname):
			libname=execname
	execdir      = os.path.abspath(os.path.join(libname,'..'))
	loaddir      = execdir if execname == '' else os.path.abspath(os.path.join(execdir,'../Frameworks/'))

	if options.verbose:
		print('execdir = %s, loaddir = %s' % (execdir,loaddir) )

	##
	# recursively build the dependency dictionary
	depend(execdir,loaddir,libname,dependdict)

	##
	# --deploy: sort and report
	if options.deploy:
		eprint("option deploy not implemented yet")
		exit(1)

	##
	# --depends: sort and report
	if options.depends:
		results=tsort(dependdict)
		for result in results:
			print(result)
#
##

if __name__ == '__main__':
	main()

# That's all Folks!
##
