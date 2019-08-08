#!/bin/bash

# Don't use ACL
tar -xzvf wget-1.5.3.tar.gz
mv analysis-out/trace.txt analysis-out/no-acl.txt

# Build something with acl
tar --acls -cpf backup.tar wget-1.5.3
tar --acls -xpf backup.tar 
mv analysis-out/trace.txt analysis-out/acl.txt
