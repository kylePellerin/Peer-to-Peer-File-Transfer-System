# Makefile for the P2P XML-RPC server

CLASSPATH=.:./lib/*

default: MainServer.class FileList.class

MainServer.class: MainServer.java FileList.class
		javac -cp $(CLASSPATH) MainServer.java

FileList.class: FileList.java
		javac -cp $(CLASSPATH) FileList.java

run:
		java -cp $(CLASSPATH) MainServer

clean:
		rm -f *.class
