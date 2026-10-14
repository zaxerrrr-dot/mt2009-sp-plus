# MT2009_PLUS_JADE_JEWELLERY_V1 (the Dockerfile step of that name): special_item_group.txt in, out. The chests the
# pl-wiki names ("Pochodzenie" of Kolia / Klipsy / Obrecz Jadeitu, the chests' "Zawartosc") get the jade jewellery +0,
# numbered on after each group's last row:
#   Id. Skrzynia Naszyjniku 83052 - Kolia Jadeitu Mgly, Nocy, Slonca (+ Luska Argosa 31228, in our world now);
#   Id. Skrzynia Kolczykow 83053  - Klipsy Jadeitu Mgly, Nocy, Slonca (+ Luska Argosa);
#   Skrzynia Labiryntowa 31256    - Kolia / Obrecz / Klipsy Jadeitu Slonca and Mgly;
#   Szkatulka Yohara 50528        - Klipsy / Kolia / Obrecz Jadeitu Mgly.
# (Jadeitu Dymu: no chest on the wiki - Mistrz Chi only.) The weights are ours (the groups' own rows: 10 / 3 / 8).
# Writes the number of chests changed to the file named by -v report.
function rows(v) {
	if (v == "83052") return "16580 1 5|16600 1 5|16590 1 5|31228 1 10"
	if (v == "83053") return "17570 1 5|17590 1 5|17580 1 5|31228 1 10"
	if (v == "31256") return "16590 1 3|16580 1 3|14590 1 3|14580 1 3|17580 1 3|17570 1 3"
	if (v == "50528") return "17570 1 8|16580 1 8|14580 1 8"
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
				L[ind + j] = "\t" (last + j) "\t" f[1] "\t" f[2] "\t" f[3] "\t-- MT2009_PLUS_JADE_JEWELLERY_V1" cr
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
