#!/bin/bash


EXTRACT_KEY=exam-extract-key.py
BASE_KEY=exam-key

# Check if prefix is given
if [ -z "$1" ]; then
  echo "Usage: $0 <prefix>"
  exit 1
fi

prefix="$1"
DIR=$(dirname $(realpath "$0"))

VERSIONS=$(ls -1 ${prefix}-?.tex | sed -e 's/.*-//' -e 's/\.tex//')
PREFIX="$prefix-"

if [[ -z "$VERSIONS" ]]; then
  VERSIONS=$(ls -1 ${prefix}?.tex)
  PREFIX=$prefix
fi

[[ -z "$VERSIONS" ]] && exit

EXAM_KEY=${PREFIX}key

for v in $VERSIONS; do
  python "$DIR/$EXTRACT_KEY" $PREFIX$v.tex > ${EXAM_KEY}-$v.txt
done
for v in $VERSIONS; do
  V=$(cat ${EXAM_KEY}-$v.txt | cut -d '	' -f 1)
  K=$(cat ${EXAM_KEY}-$v.txt | cut -d '	' -f 2- | tr '\t' ',')
	rm -f $BASE_KEY_TEX.pdf
	latexmk -f -pdf -usepretex="\\def\\FILE{$PREFIX}\\def\\VERSION{$V}\\def\\KEY{$K}\\def\\SOURCE{$DIR}" "$DIR/$BASE_KEY.tex" && mv $BASE_KEY.pdf ${EXAM_KEY}-$v.pdf
done
# latexmk -c
