#pragma once
#include <iostream>
#include <cryptopp/cryptlib.h>
#include <cryptopp/filters.h>
#include <cryptopp/chachapoly.h>
#include <cryptopp/files.h>
#include <cryptopp/hex.h>
#include <cryptopp/osrng.h>
#include <cryptopp/base64.h>

#include <string.h>
#include <cstddef>
#include <cstring>
#include <sstream>

using namespace CryptoPP;
void HexToBytes(const std::string hex, CryptoPP::byte* output, int inputlength);
char * encrypt(const char* plain, const char* keyInHex);
int decrypt(char* cipherEncoded, char* recover, const char* keyInHex);

