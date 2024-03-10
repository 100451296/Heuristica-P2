#!/bin/bash

# Debe ejecutarse desde la raiz del proyecto

# Mapa easy 2
echo "################# easy2 #################"
python3 ASTARTraslados.py ASTAR-test/easy2.csv 2
python3 ASTARTraslados.py ASTAR-test/easy2.csv 1
echo "#########################################"

# Mapa easy
echo "################# easy #################"
python3 ASTARTraslados.py ASTAR-test/easy.csv 2
python3 ASTARTraslados.py ASTAR-test/easy.csv 1
echo "#########################################"

# Mapa easy3
echo "################# easy3 #################"
python3 ASTARTraslados.py ASTAR-test/easy3.csv 2
python3 ASTARTraslados.py ASTAR-test/easy3.csv 1
echo "#########################################"

# Mapa medium
echo "################# medium #################"
python3 ASTARTraslados.py ASTAR-test/medium.csv 2
python3 ASTARTraslados.py ASTAR-test/medium.csv 1
echo "#########################################"

# Mapa medium2
echo "################# medium2 #################"
python3 ASTARTraslados.py ASTAR-test/medium2.csv 2
python3 ASTARTraslados.py ASTAR-test/medium2.csv 1
echo "#########################################"



 