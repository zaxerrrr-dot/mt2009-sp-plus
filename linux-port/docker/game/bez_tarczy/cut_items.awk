# MT2009_PLUS_NO_TRZECH_WLADCOW_V1: cut every row of an item LO..HI out of a drop file's groups (mob_drop_item.txt,
# special_item_group.txt, the client's npc_location_helper/mob_drop_item.txt) and number the group's rows again (the
# engine stops reading a group at the first missing number). A row: a line inside "Group ... { }" whose first field is
# its number, the item vnum second. A group left with no row: dropped when EMPTY=drop (monster drops), the build fails
# otherwise (a chest without contents would be worse than the shield). Writes "cut <n> rows, <g> groups dropped" to
# stderr; CR line ends stay as they were.
function flush() {
    if (inblk) {
        if (rows > 0 || !touched) printf "%s", blk
        else if (EMPTY == "drop") gone++
        else { printf "group %s would be left empty\n", name > "/dev/stderr"; bad = 1; printf "%s", blk }
    }
    blk = ""; inblk = 0
}
/^[[:blank:]]*Group([[:blank:]]|\r?$)/ { flush(); inblk = 1; name = $2; sub(/\r$/, "", name); k = 0; rows = 0; touched = 0; blk = $0 "\n"; next }
inblk && $1 ~ /^[0-9]+$/ && NF >= 2 {
    v = $2; sub(/\r$/, "", v)
    if (v ~ /^[0-9]+$/ && v + 0 >= LO + 0 && v + 0 <= HI + 0) { cut++; touched = 1; next }
    k++; rows++
    if (touched) { match($0, /^[[:blank:]]*[0-9]+/); lead = substr($0, 1, RLENGTH); sub(/[0-9]+$/, "", lead); $0 = lead k substr($0, RLENGTH + 1) }
    blk = blk $0 "\n"; next }
inblk { blk = blk $0 "\n"; if ($0 ~ /^[[:blank:]]*}/) flush(); next }
{ print }
END { flush(); printf "cut %d rows of %s-%s, %d groups dropped\n", cut, LO, HI, gone > "/dev/stderr"; if (bad) exit 1 }
