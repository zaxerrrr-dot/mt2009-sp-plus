// MT2009_PLUS_SHOP3_TOKEN_V1 - the ItemShop's in-game login token (server-patches/enginefixes, ACMD(do_in_game_mall)).
//
// The owner, 10 Nov 2026: a player with several accounts opened the ItemShop (Shift+F12) on account Y and got account
// X's shop, or the login form. The link of ACMD(do_in_game_mall) was signed with md5(pid . account id . "GF9001") only:
// the same for ever (a link seen once logs in for ever), and the shop gave up on any link it did not take and showed
// whatever session the client's browser still had. Every "/in_game_mall" answer now also carries a fresh token:
//
//   &aid=<account id>&ts=<unix time>&n=<16 random bytes, hex>&tok=<hex HMAC-SHA256(key, "shop3|1|pid|aid|ts|n")>
//
// The shop (linux-port/docker/itemshop/app/shop3/include/functions/game_login.php) takes it for 120 seconds, once,
// and signs in as exactly that account and character - logging out any other session of that browser first.
// The key: M2_SHOP3_TOKEN_SECRET when set, else derived from M2_DB_PASSWORD (both containers have it, players never
// do). Never the account's password.

#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/rand.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <string>

static void Mt2009Shop3Hex(const unsigned char* data, size_t len, char* out)
{
	static const char hex[] = "0123456789abcdef";
	for (size_t i = 0; i < len; ++i)
	{
		out[i * 2] = hex[data[i] >> 4];
		out[i * 2 + 1] = hex[data[i] & 0x0f];
	}
	out[len * 2] = '\0';
}

static bool Mt2009Shop3Key(std::string& key)
{
	const char* secret = getenv("M2_SHOP3_TOKEN_SECRET");
	if (secret && *secret)
	{
		key = secret;
		return true;
	}
	const char* dbPassword = getenv("M2_DB_PASSWORD");
	if (!dbPassword || !*dbPassword)
		return false;
	key = "mt2009plus-shop3-token|";
	key += dbPassword;
	return true;
}

// Writes "&aid=..&ts=..&n=..&tok=.." into out; false (out empty) when there is no key or no randomness - the link then
// has no token and the shop asks to open it again from the game instead of logging anybody in.
bool Mt2009Shop3Token(unsigned int pid, unsigned int aid, char* out, size_t outLen)
{
	if (!out || outLen == 0)
		return false;
	out[0] = '\0';

	std::string key;
	if (!Mt2009Shop3Key(key))
		return false;

	unsigned char nonceRaw[16];
	if (RAND_bytes(nonceRaw, sizeof(nonceRaw)) != 1)
		return false;
	char nonce[sizeof(nonceRaw) * 2 + 1];
	Mt2009Shop3Hex(nonceRaw, sizeof(nonceRaw), nonce);

	const unsigned long ts = (unsigned long) time(NULL);
	char payload[160];
	snprintf(payload, sizeof(payload), "shop3|1|%u|%u|%lu|%s", pid, aid, ts, nonce);

	unsigned char mac[EVP_MAX_MD_SIZE];
	unsigned int macLen = 0;
	if (!HMAC(EVP_sha256(), key.data(), (int) key.size(), (const unsigned char*) payload, strlen(payload), mac, &macLen) || macLen == 0)
		return false;
	char macHex[EVP_MAX_MD_SIZE * 2 + 1];
	Mt2009Shop3Hex(mac, macLen, macHex);

	const int n = snprintf(out, outLen, "&aid=%u&ts=%lu&n=%s&tok=%s", aid, ts, nonce, macHex);
	if (n < 0 || (size_t) n >= outLen)
	{
		out[0] = '\0';
		return false;
	}
	return true;
}
