# MT2009_PLUS_RECEPTURY_SUPER_V1 (the Dockerfile's step of that name; the owner, 3 November 2026): the "super receptury"
# group s50902 used to give one of four recipes at equal weights - Mikstura Geniuszu 50932, Mikstura Determinacji 50933,
# Miks. Szybkiej Analizy 50935 and Mikstura Madrosci 50930. The first three were withdrawn (MT2009_PLUS_MIKSTURY_WYCOFANE_V1:
# weight 0 in Receptury_Super), so every s50902 roll became a Receptura Mikstura Madrosci - four times as many as before.
# A group row cannot give "nothing" (a chest row must give an item, an unknown group is an error), so the cut is made
# where s50902 is rolled, in special_item_group.txt or mob_drop_item.txt (one file in, the same file out):
#  * a "Type drop" group (mob_drop_item.txt: the row's own chance in percent) - the s50902 row's chance / 4;
#  * a weighted group (special_item_group.txt without a Type or a Pick: one row an opening by weight) - every OTHER
#    row's weight x 4, which is the s50902 row's weight / 4 without fractions: the recipe drops as often as before and
#    the rest of the group keeps its odds between itself;
#  * any other group with an s50902 row is left as it is and counted as "other" (the Dockerfile wants none).
# Writes "drop <rows>", "weighted <groups>" and "other <groups>" to the file named by -v report.
function flush(   i, k, f, line, cr, lead, hit, p, other) {
	if (nb == 0) return
	hit = 0
	for (i = 1; i <= nb; i++) {
		line = L[i]; sub(/\r$/, "", line); k = split(line, f)
		if (k >= 4 && f[1] ~ /^[0-9]+$/ && f[2] == "s50902") hit++
	}
	other = hit && !((typ == "drop") || (typ == "" && !pick))
	if (other) nother++
	for (i = 1; i <= nb; i++) {
		line = L[i]
		if (hit && !other) {
			cr = sub(/\r$/, "", line); k = split(line, f)
			if (k >= 4 && f[1] ~ /^[0-9]+$/ && f[4] ~ /^[0-9]+(\.[0-9]+)?$/ &&
					((typ == "drop" && f[2] == "s50902") || (typ == "" && f[2] != "s50902"))) {
				p = (typ == "drop") ? f[4] / 4 : f[4] * 4
				p = (p == int(p)) ? sprintf("%d", p) : sprintf("%g", p)
				match(line, /^[[:blank:]]*[0-9]+[[:blank:]]+[^[:blank:]]+[[:blank:]]+[0-9]+[[:blank:]]+[0-9.]+/)
				lead = substr(line, 1, RLENGTH); sub(/[0-9.]+$/, p, lead)
				line = lead substr(line, RLENGTH + 1)
				if (typ == "drop") ndrop++
			}
			if (cr) line = line "\r"
		}
		print line
	}
	if (hit && typ == "" && !pick) nweighted++
	nb = 0; typ = ""; pick = 0
}
BEGIN { nb = 0; typ = ""; pick = 0; ndrop = 0; nweighted = 0; nother = 0 }
{
	t = $0; sub(/\r$/, "", t)
	if (t ~ /^[[:blank:]]*Group([[:blank:]]|$)/) { flush(); ingroup = 1 }
	if (!ingroup) { print; next }
	L[++nb] = $0
	split(t, g)
	if (tolower(g[1]) == "type") typ = tolower(g[2])
	if (tolower(g[1]) == "pick") pick = 1
	if (t ~ /^[[:blank:]]*}/) { flush(); ingroup = 0 }
}
END {
	flush()
	print "drop " ndrop > report
	print "weighted " nweighted > report
	print "other " nother > report
}
