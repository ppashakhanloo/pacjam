#!/bin/bash

wget http://valgrind.org/docs/manual/cl-manual.html
mv analysis-out/trace.txt analysis-out/http.txt

wget https://ftp.gnu.org/gnu/wget/wget-1.5.3.tar.gz --no-check-certificate
mv analysis-out/trace.txt analysis-out/ftp.txt

wget http://www.köln.de/ --no-check-certificate
mv analysis-out/trace.txt analysis-out/idn.txt

