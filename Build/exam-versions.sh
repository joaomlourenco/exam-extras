#!/bin/bash
LATEX=pdf
OPTS="-shell-escape" #" -auxdir=AUX"
PRINT=print
ANSWERS=answers
if [ "$1" == "" ] ; then
    echo "Usage: `basename $0` LATEX_FILE (without '-V.tex')"
    exit 1
fi
B="$1-"
F=$(ls $B?.tex 2> /dev/null)
if [[ -z "$F" ]]; then
  B="$1"
  F=$(ls $B?.tex 2> /dev/null)
fi
if [[ -z "$F" ]]; then
    echo "Usage: `basename $0` LATEX_FILE (without '-V.tex')"
    exit 1
fi

for f in $F; do
  B=${f%.tex}
  V=${B#*-}
  rm -f $B.pdf $B-${PRINT}.pdf $B-${ANSWERS}.pdf
  perl -pi -e 's/^( *\%? *,? *)(no)?answers/  noanswers/' $f
  latexmk -${OPTS} -${LATEX} -usepretex="\def\VERSION{\MakeUppercase{$V}}" $f && mv $B.pdf $B-${PRINT}.pdf
  perl -pi -e 's/^( *\%? *,? *)(no)?answers/  answers/' $f
  latexmk -${OPTS} -${LATEX} -usepretex="\def\VERSION{\MakeUppercase{$V}}" $f && mv $B.pdf $B-${ANSWERS}.pdf
done
# V="a"
# while : ; do
#   [[ -f "$B$V.tex" ]] || break
#   rm -f $B$V.pdf $B$V-${PRINT}.pdf $B$V-${ANSWERS}.pdf
#   perl -pi -e 's/^( *\%? *,? *)(no)?answers/  noanswers/' $B$V.tex
#   latexmk -${OPTS} -${LATEX} -usepretex="\def\VERSION{\MakeUppercase{$V}}" $B$V && mv $B$V.pdf $B$V-${PRINT}.pdf
#   perl -pi -e 's/^( *\%? *,? *)(no)?answers/  answers/' $B$V.tex
#   latexmk -${OPTS} -${LATEX} -usepretex="\def\VERSION{\MakeUppercase{$V}}" $B$V && mv $B$V.pdf $B$V-${ANSWERS}.pdf
#   V=$(echo "$V" | tr "0-9a-z" "1-9a-z_")
# done
latexmk -${LATEX} -c
rm -rf AUX
