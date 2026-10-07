# MT2009_PLUS_BELT_MATS_V1 (the Dockerfile's step of that name): mob_drop_item.txt in, out.
#  * every kill group (Type kill, kill_drop over 1) carrying a gold part (30518, 30519, 30522,
#    30523) or Niebieski Rzemyk (30550): that item's weight x3, kill_drop times W / W' (the old
#    and the new sum of the weights, rounded, at least 1) - the belt item drops three times as
#    often, every other item of the group as often as before. kill_drop 1 groups (the chiefs,
#    one item every kill) stay: their bosses' limit groups (mob_drop_item.beltmats.append.txt)
#    carry the increase.
#  * Wladca Ochao's (6390) limit group gets Zlota Przedza and Zloty Hak at 25% each, numbered on.
# Writes "kill <n>" and "ochao <n>" counts to the file named by -v report.
function isbelt(v) { return v == "30518" || v == "30519" || v == "30522" || v == "30523" || v == "30550" }
function flush(   i, t, f, k, W, B, nkd, cr, line, wt, lead, n, last, ind) {
	if (nb == 0) return
	if (typ == "kill" && kd > 1) {
		W = 0; B = 0
		for (i = 1; i <= nb; i++) {
			t = L[i]; sub(/\r$/, "", t); k = split(t, f)
			if (k >= 4 && f[1] ~ /^[0-9]+$/) { W += f[4]; if (isbelt(f[2])) B += f[4] }
		}
		if (B > 0) {
			nkd = int(kd * W / (W + 2 * B) + 0.5); if (nkd < 1) nkd = 1
			for (i = 1; i <= nb; i++) {
				line = L[i]; cr = sub(/\r$/, "", line); k = split(line, f)
				if (k >= 2 && tolower(f[1]) == "kill_drop") {
					sub(/kill_drop[[:blank:]]+[0-9]+/, "kill_drop\t" nkd, line)
				} else if (k >= 4 && f[1] ~ /^[0-9]+$/ && isbelt(f[2])) {
					wt = f[4] * 3
					match(line, /^[[:blank:]]*[0-9]+[[:blank:]]+[0-9]+[[:blank:]]+[0-9]+[[:blank:]]+[0-9.]+/)
					lead = substr(line, 1, RLENGTH); sub(/[0-9.]+$/, wt, lead)
					line = lead substr(line, RLENGTH + 1)
				}
				L[i] = line (cr ? "\r" : "")
			}
			nkill++
		}
	}
	if (typ == "limit" && mob == "6390") {
		last = 0; ind = 0
		for (i = 1; i <= nb; i++) {
			t = L[i]; sub(/\r$/, "", t); k = split(t, f)
			if (k >= 2 && f[1] ~ /^[0-9]+$/) { last = f[1] + 0; ind = i }
		}
		if (ind > 0) {
			cr = (L[ind] ~ /\r$/) ? "\r" : ""
			for (i = nb; i > ind; i--) L[i + 2] = L[i]
			L[ind + 1] = "\t" (last + 1) "\t30518\t1\t25\t-- Zlota Przedza (MT2009_PLUS_BELT_MATS_V1)" cr
			L[ind + 2] = "\t" (last + 2) "\t30519\t1\t25\t-- Zloty Hak (MT2009_PLUS_BELT_MATS_V1)" cr
			nb += 2; nochao++
		}
	}
	for (i = 1; i <= nb; i++) print L[i]
	nb = 0
}
/^[[:blank:]]*Group([[:blank:]]|$)/ { flush(); typ = ""; mob = ""; kd = 0 }
{
	L[++nb] = $0
	t = $0; sub(/\r$/, "", t); k = split(t, f)
	if (k >= 2 && tolower(f[1]) == "type") typ = tolower(f[2])
	if (k >= 2 && tolower(f[1]) == "mob") mob = f[2]
	if (k >= 2 && tolower(f[1]) == "kill_drop") kd = f[2] + 0
}
END { flush(); print "kill " nkill + 0 > report; print "ochao " nochao + 0 > report }
