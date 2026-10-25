#include "crypto.h"

using namespace CryptoPP;


void HexToBytes(const std::string hex, CryptoPP::byte* output, int inputlength)
{
	CryptoPP::byte* outputLocal = static_cast<CryptoPP::byte*> (malloc((hex.length() / 2) * sizeof(CryptoPP::byte)));
	unsigned int  j = 0;
	for (unsigned int i = 0; i < hex.length(); i += 2)
	{
		std::string byteString = hex.substr(i, 2);
		char byte = (char)strtol(byteString.c_str(), NULL, 16);
		outputLocal[j] = byte;
		j++;
	}
	memcpy(output, outputLocal, hex.length() / 2);
	free(outputLocal);
}
char * encrypt(const char* plain, const char* keyInHex)
{
	std::string decoded1, input = plain, keyPtr = keyInHex;
	StringSource ss(input, true /*pumpAll*/, new StringSink(decoded1));
	const CryptoPP::byte* pt = (const CryptoPP::byte*)decoded1.data();

	const CryptoPP::byte aad[] = { 0x50,0x51,0x52,0x53,0xc0,0xc1,0xc2,0xc3,0xc4,0xc5,0xc6,0xc7 };
	CryptoPP::byte key[32];
	HexToBytes(keyPtr, key, 64);
	CryptoPP::byte nonce[12];

	AutoSeededRandomPool prng;
	prng.GenerateBlock(nonce, sizeof(nonce));
	////prng.Reseed(true, sizeof(nonce));

	CryptoPP::byte mac[16];
	CryptoPP::byte* ct = static_cast<CryptoPP::byte*>(malloc((input.length()) * sizeof(CryptoPP::byte)));
	ChaCha20Poly1305::Encryption enc;
	enc.SetKeyWithIV(key, sizeof(key), nonce, sizeof(nonce));
	enc.EncryptAndAuthenticate(ct, mac, sizeof(mac), nonce, sizeof(nonce), aad, sizeof(aad), pt, input.length());

	std::stringstream ctHex, macHex, nonceHex;
	StringSource(ct, input.length(), true, new HexEncoder(new FileSink(ctHex)));

	StringSource(mac, sizeof(mac), true, new HexEncoder(new FileSink(macHex)));

	StringSource(nonce, sizeof(nonce), true, new HexEncoder(new FileSink(nonceHex)));

	std::string CTWhole = ctHex.str().c_str();
	CTWhole.append(macHex.str().c_str());
	CTWhole.append(nonceHex.str().c_str());

	std::string encoded;
	StringSource(CTWhole, true, new Base64Encoder(new StringSink(encoded)));
	free(ct);

	char *cstr = new char[encoded.length() + 1];
	strcpy(cstr, encoded.c_str());
	return (cstr);
}

int decrypt(char* cipherEncoded, char* recover, const char* keyInHex)
{
	//PLOG_DEBUG << "Enter: " << cipherEncoded << ", " << keyInHex;
	std::string keyPtr = keyInHex;
	const CryptoPP::byte aad[] = { 0x50,0x51,0x52,0x53,0xc0,0xc1,0xc2,0xc3,0xc4,0xc5,0xc6,0xc7 };

	std::string decoded;
	StringSource(cipherEncoded, true, new Base64Decoder(new StringSink(decoded)));
	size_t ctLength = (decoded.length() - 24 - 32);

	CryptoPP::byte* ct = static_cast<CryptoPP::byte*>(malloc((ctLength / 2) * sizeof(CryptoPP::byte)));
	HexToBytes(decoded.substr(0, ctLength), ct, ctLength);

	CryptoPP::byte mac[16]; HexToBytes(decoded.substr(ctLength, ctLength + 32), mac, 32);

	CryptoPP::byte nonce[12]; HexToBytes(decoded.substr(ctLength + 32, decoded.length()), nonce, 24);

	CryptoPP::byte key[32];
	HexToBytes(keyPtr, key, 64);

	CryptoPP::byte rt[sizeof(ct)];
	ChaCha20Poly1305::Decryption dec;
	dec.SetKeyWithIV(key, sizeof(key), nonce, sizeof(nonce));
	int authenticated = dec.DecryptAndVerify(rt, mac, sizeof(mac), nonce, sizeof(nonce), aad, sizeof(aad), ct, sizeof(ct));

	std::string destinationRT;
	StringSource ssRT(rt, sizeof rt, true, new HexEncoder(new StringSink(destinationRT)));

	memcpy(recover, rt, sizeof rt);
	free(ct);
	return authenticated;
}

