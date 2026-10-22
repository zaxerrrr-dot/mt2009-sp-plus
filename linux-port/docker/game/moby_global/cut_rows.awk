# MT2009_PLUS_MOBY_GLOBAL_V1: cut the rows of R ("<mob> <item> <count> <value>") from that monster's groups (not
# MT2009_* / playerbot_*), number the group again; a group left with no row goes as a whole.
# MT2009_PLUS_237_GLOBAL_MODE_V1: -v LOOSE=1 (the 2.x image) - a listed row the file lacks is only counted.
BEGIN { while ((getline l < R) > 0) { sub(/\r$/, "", l); if (l ~ /^#/ || l == "") continue; split(l, f, /[ \t]+/); want[f[1] SUBSEP f[2] SUBSEP f[3] SUBSEP f[4]] = 1; nwant++ } }
function flush() { if (inblk) { if (rows > 0 || !touched) printf "%s", blk; else gone++ } blk = ""; inblk = 0 }
/^[[:blank:]]*Group([[:blank:]]|$)/ { flush(); inblk = 1; blk = ""; name = $2; sub(/\r$/, "", name); ours = (name ~ /^(MT2009_|playerbot_)/); mob = ""; k = 0; rows = 0; touched = 0; blk = blk $0 "\n"; next }
inblk && /^[[:blank:]]*Mob[[:blank:]]/ { mob = $2; sub(/\r$/, "", mob) }
inblk && $1 ~ /^[0-9]+$/ && NF >= 4 {
    c = $3; v = $4; sub(/\r$/, "", v); it = $2
    if (!ours && ((mob SUBSEP it SUBSEP c SUBSEP v) in want)) { cut++; touched = 1; done[mob SUBSEP it SUBSEP c SUBSEP v] = 1; next }
    k++; rows++
    if (touched) { match($0, /^[[:blank:]]*[0-9]+/); lead = substr($0, 1, RLENGTH); sub(/[0-9]+$/, "", lead); $0 = lead k substr($0, RLENGTH + 1) }
    blk = blk $0 "\n"; next }
inblk { blk = blk $0 "\n"; if ($0 ~ /^[[:blank:]]*}/) flush(); next }
{ print }
END { flush(); n = 0; for (x in done) n++; printf "share: %d row(s) cut (%d of %d listed), %d group(s) left empty and dropped\n", cut, n, nwant, gone > "/dev/stderr"; if (n != nwant && !LOOSE) exit 1 }
