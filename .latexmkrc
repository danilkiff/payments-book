$max_repeat = 8;
$makeindex = 'texindy -L russian -C utf8 -t %R.ilg -o %D %S';

# This book needs more than the default number of TeX engine passes from a clean
# state because the global TOC, chapter margin TOCs, and bibliography settle
# across several runs.
