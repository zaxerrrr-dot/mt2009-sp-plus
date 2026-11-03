# MT2009_PLUS_DROP307_V1 (the owner's list of 3 November 2026) - one pass over mob_drop_item.txt (-v kind=mob) or
# special_item_group.txt (-v kind=sig), the game image's Dockerfile step "drop 3.0.7":
#  * Lza Bogini (70012), Plaszcz Uciekiniera (70048), Symbol (70050) and Rekawica (70051) Krola Przepowiedni drop from
#    nothing any more - every row of theirs in every drop group (monsters, Metins, bosses) and in the chests' groups
#    (the bosses' and dungeons' chests: Szkat. Olbrz. Pajaka 50074, Skrzynia Nemere 950275, Skrzynia Przebudzenia 31143,
#    Skrzynia Bagjanamu 54701, Skrzynia Triumfu 50249) is cut - not the event's and the Biologist's boxes (Skarpetka
#    50010, Heksagonalna Szkatulka 50037, Zolta Ebonit. Szkatulka 50111, collect_quest_lv50 / harvest_festival) - the rest of the group numbered again (the loaders stop at the
#    first missing number, item_manager_read_tables.cpp); a group left empty stops the build;
#  * kind=mob: every group of Krol Bao (misja) (6692) is cut whole - it drops nothing (the pl-wiki);
#  * Kamien Kowala 71025 -> 39015 and Magiczny Metal 71026 -> 39016 (the tradeable twins) in the boss drops: the drop
#    groups of Potezny Kappa (6749) and the boss chests' / tier groups 50077-50079, 50082, 50097, 50098, 10742-10744,
#    10754, 10755 and Biala Smocza Skrzynia (ciezka) 70412. The ItemShop's and the events' chests keep 71025 / 71026.
# The report (cut rows, cut groups, swapped rows) goes to stderr; "bad" > 0 exits 1.
function flush(   i) {
	if (keep) { for (i = 1; i <= nb; i++) print B[i] } else cutg++
	nb = 0; ing = 0
}
BEGIN {
	split("70012 70048 70050 70051", a); for (i in a) GONE[a[i]] = 1
	split("50077 50078 50079 50082 50097 50098 10742 10743 10744 10754 10755 70412", a); for (i in a) SWAPG[a[i]] = 1
	SWAP["71025"] = "39015"; SWAP["71026"] = "39016"
	split("50010 50037 50111", a); for (i in a) KEEPG[a[i]] = 1
}
/^[[:blank:]]*Group([[:blank:]]|$)/ { if (ing) flush(); ing = 1; keep = 1; nb = 0; key = ""; k = 0; renum = 0; B[++nb] = $0; next }
ing {
	t = $0; sub(/\r$/, "", t); n = split(t, f)
	if (n >= 2 && ((kind == "mob" && tolower(f[1]) == "mob") || (kind == "sig" && tolower(f[1]) == "vnum"))) {
		key = f[2]
		if (kind == "mob" && key == "6692") keep = 0
	}
	if (t ~ /^[[:blank:]]*}/) {
		if (renum && k == 0) { printf "FATAL: group %s left empty\n", key > "/dev/stderr"; bad++ }
		B[++nb] = $0; flush(); next
	}
	if (n >= 3 && f[1] ~ /^[0-9]+$/) {
		if ((f[2] in GONE) && !(kind == "sig" && (key in KEEPG))) { cut++; renum = 1; next }
		k++
		if ((f[2] in SWAP) && ((kind == "mob" && key == "6749") || (kind == "sig" && (key in SWAPG)))) {
			match($0, /^[[:blank:]]*[0-9]+[[:blank:]]+/)
			$0 = substr($0, 1, RLENGTH) SWAP[f[2]] substr($0, RLENGTH + 6)
			swapped++
		}
		if (renum) {
			match($0, /^[[:blank:]]*[0-9]+/); lead = substr($0, 1, RLENGTH); sub(/[0-9]+$/, "", lead)
			$0 = lead k substr($0, RLENGTH + 1)
		}
	}
	B[++nb] = $0; next
}
{ print }
END {
	if (ing) flush()
	printf "share: drop 3.0.7 (%s) - %d row(s) of 70012/70048/70050/70051 cut, %d group(s) of 6692 cut, %d smith row(s) made tradeable\n", kind, cut, cutg, swapped > "/dev/stderr"
	if (bad) exit 1
}
