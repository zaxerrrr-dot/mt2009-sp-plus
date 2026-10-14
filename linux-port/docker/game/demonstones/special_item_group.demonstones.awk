# MT2009_PLUS_DEMON_STONES_V1 (the Dockerfile step of that name): special_item_group.txt in, out. The chests the pl-wiki
# names for Kamien Demonow / Kamien Mocy Demonow get the grades past +0, numbered on after each group's last row:
#   B. Smocza Skrz. (lekka) 70411 - Demonow +1, +2, Mocy Demonow +0;
#   B. Smocza Skrz. (ciezka) 70412 - Demonow +1 to +4 (+4: Zdobiona Skrzynia Aamona's, which we do not have);
#   Skarb Wezy 70429 - Demonow +1 to +4, Mocy Demonow +1;
#   Skrzynia Hydry 54705 (the wiki's Skarb Hydry) - Demonow +0 to +3.
# Writes the number of chests changed to the file named by -v report.
function rows(v) {
	if (v == "70411") return "28146 1 15|28246 1 10|28047 1 10"
	if (v == "70412") return "28146 1 15|28246 1 10|28346 1 5|28446 1 2"
	if (v == "70429") return "28146 1 15|28246 1 10|28346 1 5|28446 1 2|28147 1 5"
	if (v == "54705") return "28046 1 40|28146 1 25|28246 1 12|28346 1 5"
	return ""
}
function flush(   i, t, f, k, last, ind, cr, n, r, parts, j) {
	if (nb == 0) return
	r = rows(vnum)
	if (r != "") {
		last = 0; ind = 0
		for (i = 1; i <= nb; i++) {
			t = L[i]; sub(/\r$/, "", t); k = split(t, f)
			if (k >= 4 && f[1] ~ /^[0-9]+$/) { last = f[1] + 0; ind = i }
		}
		if (ind > 0) {
			cr = (L[ind] ~ /\r$/) ? "\r" : ""
			n = split(r, parts, "|")
			for (i = nb; i > ind; i--) L[i + n] = L[i]
			for (j = 1; j <= n; j++) {
				split(parts[j], f, " ")
				L[ind + j] = "\t" (last + j) "\t" f[1] "\t" f[2] "\t" f[3] "\t-- MT2009_PLUS_DEMON_STONES_V1" cr
			}
			nb += n; changed++
		}
	}
	for (i = 1; i <= nb; i++) print L[i]
	nb = 0
}
/^[[:blank:]]*Group([[:blank:]]|$)/ { flush(); vnum = "" }
{
	L[++nb] = $0
	t = $0; sub(/\r$/, "", t); k = split(t, f)
	if (k >= 2 && tolower(f[1]) == "vnum") vnum = f[2]
}
END { flush(); print "chests " changed + 0 > report }
