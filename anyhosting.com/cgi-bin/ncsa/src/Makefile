# For gcc
CC= gcc
# For ANSI compilers
#CC= cc

#For Optimization
#CFLAGS= -O2
#For debugging
CFLAGS= -g

RM= /bin/rm -f
#--- You shouldn't have to edit anything else. ---

.c.o: 
	$(CC) -c $(CFLAGS) $<

all: query post-query imagemap jj phf

ibm:
	make all CC=gcc

sun:
	make all CC=gcc

hp: 
	make all CC=gcc

sgi:
	make all CC=cc

decmips:
	make all CC=cc

decaxp:
	make all CC=cc

tar: query post-query imagemap jj phf 
	$(RM) post-query.o util.o imagerect.o jj.o phf.o

post-query: post-query.o util.o
	$(CC) post-query.o util.o -o ../post-query

query: query.o util.o
	$(CC) query.o util.o -o ../query

imagemap: imagemap.o util.o
	$(CC) imagemap.o util.o -o ../imagemap

jj: jj.o util.o
	$(CC) jj.o util.o -o ../jj

phf: phf.o util.o
	$(CC) phf.o util.o -o ../phf

change-passwd: change-passwd.o util.o
	$(CC) change-passwd.o util.o -o ../change-passwd


clean:
	rm -f *.o ../post-query ../query ../change-passwd ../phf ../jj 

